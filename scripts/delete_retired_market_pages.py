"""Permanently remove the two specifically authorized retired market pages.

Deletion is allowlisted by Blogger page ID, title, and canonical path. Both
pages are preflighted before either is deleted. No posts or other pages are
modified. A page named Tally, if any, is only reported for review.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from googleapiclient.errors import HttpError
from blogger_client import get_blog_by_url, get_blogger_service, load_site_config

ROOT = Path(__file__).resolve().parent.parent
CONFIRM_PHRASE = "CONFIRM: DELETE MARKETS TODAY AND GLOBAL SNAPSHOT PAGES"
TRIGGER_FILE = ROOT / "trigger" / "delete-market-pages.txt"
TARGETS = [
    {"id": "5236051989054453802", "title": "Markets today", "path": "/p/markets-today.html"},
    {"id": "8504888514217789256", "title": "Global snapshot", "path": "/p/global-snapshot.html"},
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save(report: dict) -> None:
    out = ROOT / "artifacts" / "delete-market-pages-report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Report saved: {out}", flush=True)


def all_pages(service, blog_id: str) -> list[dict]:
    result, token = [], None
    while True:
        args = {"blogId": blog_id, "maxResults": 500}
        if token:
            args["pageToken"] = token
        page = service.pages().list(**args).execute()
        result.extend(page.get("items", []))
        token = page.get("nextPageToken")
        if not token:
            return result


def main() -> None:
    if not TRIGGER_FILE.is_file() or CONFIRM_PHRASE not in TRIGGER_FILE.read_text(encoding="utf-8").splitlines():
        raise SystemExit("Refusing: the exact deletion confirmation phrase is absent.")
    cfg = load_site_config()
    service = get_blogger_service()
    blog = get_blog_by_url(service, cfg["blog_url"])
    blog_id = str(blog["id"])
    if blog_id != str(cfg["expected_blog_id"]):
        raise SystemExit("Resolved Blogger blog ID does not match config; no pages deleted.")
    pages = all_pages(service, blog_id)
    report = {"mode": "delete-retired-market-pages", "started_at_utc": now(), "blog": {"id": blog_id, "url": blog.get("url")}, "targets": [], "deleted": [], "already_missing": [], "failed": [], "tally_candidates": [], "remaining_pages_count": None, "finished_at_utc": None}
    by_id = {str(x.get("id")): x for x in pages}
    verified = []
    # Validate all destinations before performing any destructive action.
    for target in TARGETS:
        page = by_id.get(target["id"])
        if page is None:
            try:
                page = service.pages().get(blogId=blog_id, pageId=target["id"]).execute()
            except HttpError as exc:
                code = getattr(exc.resp, "status", None)
                if code == 404:
                    report["already_missing"].append({**target, "state": "already-missing"})
                    continue
                raise
        actual = urlparse(page.get("url", "")).path
        entry = {**target, "actual_title": page.get("title"), "actual_url": page.get("url")}
        if actual != target["path"] or page.get("title", "").strip().casefold() != target["title"].casefold():
            entry["error"] = f"Preflight mismatch (title={page.get('title')!r}, path={actual!r}); expected exact allowlisted page."
            report["failed"].append(entry)
            save(report)
            raise SystemExit("Target page failed ID/title/path validation; no pages deleted.")
        entry["state"] = "verified"
        report["targets"].append(entry)
        verified.append(entry)
        print(f"Preflight verified: {entry['actual_title']} | {entry['actual_url']} | {target['id']}", flush=True)
    # Perform only the two user's explicitly authorized deletions.
    for entry in verified:
        try:
            service.pages().delete(blogId=blog_id, pageId=entry["id"], useTrash=False).execute()
            report["deleted"].append({**entry, "action": "permanently-deleted"})
            print(f"Permanently deleted: {entry['title']} | {entry['path']}", flush=True)
        except HttpError as exc:
            code = getattr(exc.resp, "status", None)
            if code == 404:
                report["already_missing"].append({**entry, "state": "already-missing-during-delete"})
            else:
                report["failed"].append({**entry, "error": f"HTTP {code}"})
                save(report)
                raise
        time.sleep(0.5)
    remaining = all_pages(service, blog_id)
    report["remaining_pages_count"] = len(remaining)
    report["remaining_pages"] = [{"id": x.get("id"), "title": x.get("title"), "url": x.get("url")} for x in remaining]
    report["tally_candidates"] = [{"id": x.get("id"), "title": x.get("title"), "url": x.get("url")} for x in remaining if "tally" in (x.get("title", "") + " " + x.get("url", "")).casefold()]
    remaining_ids = {str(x.get("id")) for x in remaining}
    for target in TARGETS:
        if target["id"] in remaining_ids:
            report["failed"].append({**target, "error": "Still present after deletion verification"})
    report["finished_at_utc"] = now()
    save(report)
    print(f"Remaining Blogger pages: {len(remaining)}", flush=True)
    print("Tally-title/URL candidates:", len(report["tally_candidates"]), flush=True)
    if report["failed"]:
        raise SystemExit("Deletion verification failed; see artifact report.")


if __name__ == "__main__":
    main()
