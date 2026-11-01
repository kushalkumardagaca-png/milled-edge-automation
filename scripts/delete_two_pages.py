"""Permanently delete only the Daily news and Daily article Blogger pages.

Destructive but narrowly allowlisted. This script refuses to delete anything
except the two page IDs below, and only when the trigger file contains the
exact confirmation phrase.
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
CONFIRM_PHRASE = "CONFIRM: DELETE DAILY NEWS AND DAILY ARTICLE PAGES"
TRIGGER_FILE = ROOT / "trigger" / "delete-two-pages.txt"

TARGET_PAGES = [
    {
        "id": "9217579601621666930",
        "expected_path": "/p/daily-news.html",
        "label": "Daily news",
    },
    {
        "id": "1685707888914861815",
        "expected_path": "/p/article.html",
        "label": "Daily article",
    },
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_report(report: dict) -> None:
    output_dir = ROOT / "artifacts"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "delete-two-pages-report.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(f"Report saved: {path}", flush=True)


def list_pages(service, blog_id: str) -> list[dict]:
    items: list[dict] = []
    request = service.pages().list(blogId=blog_id, maxResults=500)
    while request is not None:
        response = request.execute()
        items.extend(response.get("items", []))
        request = service.pages().list_next(request, response)
    return items


def main() -> None:
    config = load_site_config()
    expected_blog_id = str(config.get("expected_blog_id", "")).strip()

    phrase_present = TRIGGER_FILE.exists() and any(
        line.strip() == CONFIRM_PHRASE
        for line in TRIGGER_FILE.read_text(encoding="utf-8").splitlines()
    )
    if not phrase_present:
        raise SystemExit("Refusing to run: trigger file does not contain the exact confirmation phrase.")

    service = get_blogger_service()
    blog = get_blog_by_url(service, config["blog_url"])
    blog_id = str(blog["id"])
    if expected_blog_id and blog_id != expected_blog_id:
        raise SystemExit(f"Blog ID mismatch: expected {expected_blog_id}, got {blog_id}. Aborting.")

    report = {
        "mode": "delete-two-pages",
        "started_at_utc": now(),
        "blog": {"id": blog_id, "name": blog.get("name"), "url": blog.get("url")},
        "targets": [],
        "deleted": [],
        "already_missing": [],
        "failed": [],
        "remaining_pages_count": None,
        "remaining_pages": [],
        "finished_at_utc": None,
    }

    # Preflight: verify every target before deleting anything.
    verified: list[dict] = []
    for target in TARGET_PAGES:
        entry = {**target}
        try:
            page = service.pages().get(blogId=blog_id, pageId=target["id"]).execute()
        except HttpError as error:
            code = getattr(error.resp, "status", None)
            if code == 404:
                entry["state"] = "already-missing"
                report["already_missing"].append(entry)
                report["targets"].append(entry)
                print(f"Already missing: {target['label']} ({target['id']})", flush=True)
                continue
            entry["state"] = "failed-preflight"
            entry["error"] = f"HTTP {code}"
            report["failed"].append(entry)
            report["targets"].append(entry)
            save_report(report)
            raise SystemExit(f"Preflight failed for {target['label']}: HTTP {code}")

        actual_url = page.get("url", "")
        actual_path = urlparse(actual_url).path
        entry["actual_title"] = page.get("title")
        entry["actual_url"] = actual_url

        if actual_path != target["expected_path"]:
            entry["state"] = "failed-preflight"
            entry["error"] = f"URL path mismatch: expected {target['expected_path']}, got {actual_path}"
            report["failed"].append(entry)
            report["targets"].append(entry)
            save_report(report)
            raise SystemExit(f"Preflight mismatch for {target['label']}; aborting before deletion.")

        entry["state"] = "verified"
        report["targets"].append(entry)
        verified.append(entry)
        print(f"Verified: {target['label']} | {page.get('title')} | {actual_url}", flush=True)

    # Delete only verified allowlisted pages.
    for entry in verified:
        try:
            service.pages().delete(blogId=blog_id, pageId=entry["id"], useTrash=False).execute()
            report["deleted"].append({**entry, "action": "permanently-deleted"})
            print(f"Deleted: {entry['label']} ({entry['id']})", flush=True)
        except HttpError as error:
            code = getattr(error.resp, "status", None)
            if code == 404:
                report["already_missing"].append({**entry, "action": "already-gone"})
                print(f"Already gone during delete: {entry['label']}", flush=True)
            else:
                report["failed"].append({**entry, "error": f"HTTP {code}"})
                print(f"FAILED: {entry['label']} HTTP {code}", flush=True)
        time.sleep(0.5)

    remaining = list_pages(service, blog_id)
    report["remaining_pages_count"] = len(remaining)
    report["remaining_pages"] = [
        {
            "id": page.get("id"),
            "title": page.get("title"),
            "url": page.get("url"),
        }
        for page in remaining
    ]
    report["finished_at_utc"] = now()
    save_report(report)

    print(f"Remaining pages: {len(remaining)}", flush=True)
    for page in remaining:
        print(f"- {page.get('title')} | {page.get('url')}", flush=True)

    if report["failed"]:
        raise SystemExit("One or more target pages failed; see report.")


if __name__ == "__main__":
    main()
