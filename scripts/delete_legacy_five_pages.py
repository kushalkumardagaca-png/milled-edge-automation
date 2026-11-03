#!/usr/bin/env python3
"""Permanently delete only the five legacy pages replaced by the new MILLED EDGE pages.

Preflight (all must pass before ANY delete):
  * config/site.json blog URL and expected blog ID match the live blog.
  * All five replacement URLs return HTTP 200 with the expected page title.
  * Each of the five legacy page IDs still exists, with the exact expected title
    and exact expected URL path, and that path is not owned by another page.
  * No other page ID is targeted.

Only then are the five exact IDs deleted with useTrash=False, each verified gone.
No posts, no theme, and no other page is modified.
"""
from __future__ import annotations

import html
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from googleapiclient.errors import HttpError

from blogger_client import get_blog_by_url, get_blogger_service, load_site_config

ROOT = Path(__file__).resolve().parents[1]
TRIGGER = ROOT / "trigger" / "delete-legacy-five-pages.txt"
CONFIRM = "CONFIRM: DELETE ONLY THE FIVE LEGACY MILLED EDGE PAGES"
REPORT_PATHS = [
    ROOT / "reports" / "delete-legacy-five-pages-report.json",
    ROOT / "artifacts" / "delete-legacy-five-pages-report.json",
]
BLOG_URL = "https://millededgeindia.blogspot.com/"
EXPECTED_BLOG_ID = "8911514070006792465"

NEW = {
    "/p/about-milled-edge.html": "About us",
    "/p/contact-milled-edge.html": "Contact us",
    "/p/privacy-policy-milled-edge.html": "Privacy Policy",
    "/p/financial-disclaimer-milled-edge.html": "Financial Disclaimer",
    "/p/terms-milled-edge.html": "Terms & Conditions",
}
# Exact legacy records, from reports/readonly-inventory.json and
# reports/delete-two-pages-report.json (re-verified live below).
LEGACY = [
    {"id": "2716668129166401912", "title": "About us", "path": "/p/about-us_02080501126.html", "replaced_by": "/p/about-milled-edge.html"},
    {"id": "4698688245681185879", "title": "Contact us", "path": "/p/contact-us_01883938366.html", "replaced_by": "/p/contact-milled-edge.html"},
    {"id": "304220949515133754", "title": "Privacy policy", "path": "/p/privacy-policy.html", "replaced_by": "/p/privacy-policy-milled-edge.html"},
    {"id": "3945823007631424733", "title": "Disclaimer", "path": "/p/disclaimer.html", "replaced_by": "/p/financial-disclaimer-milled-edge.html"},
    {"id": "3254393081257151974", "title": "Terms and conditions", "path": "/p/terms-and-conditions.html", "replaced_by": "/p/terms-milled-edge.html"},
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def path_of(page: dict) -> str:
    return urlparse(page.get("url", "")).path


def save(report: dict) -> None:
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    for path in REPORT_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(f"Report saved: {REPORT_PATHS[0]}", flush=True)
    print(text, flush=True)


def get_page(service, blog_id: str, page_id: str):
    try:
        return service.pages().get(
            blogId=blog_id, pageId=str(page_id), view="ADMIN"
        ).execute()
    except HttpError as exc:
        if getattr(exc.resp, "status", None) == 404:
            return None
        raise


def list_pages(service, blog_id: str) -> list[dict]:
    out: list[dict] = []
    request = service.pages().list(blogId=blog_id, maxResults=500, view="ADMIN")
    while request is not None:
        response = request.execute()
        out.extend(response.get("items", []))
        request = service.pages().list_next(request, response)
    return out


def fetch(url: str):
    import time

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Accept": "text/html,*/*;q=0.8",
        },
    )
    last = (0, "")
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, response.read(3_000_000).decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            last = (exc.code, exc.read(1_000_000).decode("utf-8", "replace"))
            if exc.code not in (429, 500, 502, 503, 504):
                return last
        except Exception as exc:
            last = (0, f"request error: {exc}")
        if attempt < 4:
            time.sleep(4 * (attempt + 1))
    return last


def page_title(body: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
    return html.unescape(re.sub(r"\s+", " ", match.group(1)).strip()) if match else ""


def main() -> int:
    if not TRIGGER.exists() or TRIGGER.read_text(encoding="utf-8").strip() != CONFIRM:
        print("Inactive trigger; nothing deleted.", flush=True)
        return 0

    report = {
        "mode": "delete-legacy-five-pages",
        "started_at_utc": now(),
        "blog": {},
        "preflight": {"new_url_checks": [], "legacy_record_checks": [], "passed": False},
        "deleted": [],
        "already_missing": [],
        "untouched_pages_before": 0,
        "untouched_pages_after": 0,
        "errors": [],
        "result": "running",
        "note": "Only the five exact legacy IDs are targeted. No posts, theme or other pages touched.",
    }

    try:
        config = load_site_config()
        if config.get("blog_url", "").rstrip("/") != BLOG_URL.rstrip("/"):
            raise RuntimeError("config/site.json blog URL mismatch; aborting.")
        if str(config.get("expected_blog_id")) != EXPECTED_BLOG_ID:
            raise RuntimeError("config/site.json expected blog ID mismatch; aborting.")

        service = get_blogger_service()
        blog = get_blog_by_url(service, config["blog_url"])
        blog_id = str(blog["id"])
        if blog_id != EXPECTED_BLOG_ID or blog.get("url", "").rstrip("/") != BLOG_URL.rstrip("/"):
            raise RuntimeError(f"Live blog mismatch: {blog_id} {blog.get('url')}")
        report["blog"] = {"id": blog_id, "url": blog.get("url"), "name": blog.get("name")}

        # 1) Re-verify every replacement URL is live and correctly titled.
        for path, label in NEW.items():
            url = urljoin(BLOG_URL, path.lstrip("/"))
            import time
            time.sleep(1.5)
            code, body = fetch(url)
            title = page_title(body)
            ok = code == 200 and html.unescape(label).casefold() in title.casefold()
            report["preflight"]["new_url_checks"].append(
                {"path": path, "url": url, "status_code": code, "page_title": title, "expected_title": label, "ok": ok}
            )
            print(f"New URL check {url} -> {code} / {title!r} (ok={ok})", flush=True)
            if not ok:
                raise RuntimeError(f"Replacement URL is not verified live: {url} ({code}, {title!r})")

        # 2) Re-verify each legacy record still exists with the exact title and path.
        current = list_pages(service, blog_id)
        by_id = {str(p["id"]): p for p in current}
        by_path = {path_of(p): p for p in current if p.get("url")}
        report["untouched_pages_before"] = len(current)

        for target in LEGACY:
            page = get_page(service, blog_id, target["id"])
            if page is None:
                raise RuntimeError(f"Legacy page missing at preflight: {target['id']} ({target['path']})")
            actual_path = path_of(page)
            actual_title = (page.get("title") or "").strip()
            owner = by_path.get(target["path"])
            owner_ok = owner is not None and str(owner["id"]) == target["id"]
            ok = (
                actual_path == target["path"]
                and actual_title.casefold() == target["title"].casefold()
                and owner_ok
            )
            report["preflight"]["legacy_record_checks"].append(
                {
                    "id": target["id"],
                    "expected_title": target["title"],
                    "actual_title": actual_title,
                    "expected_path": target["path"],
                    "actual_path": actual_path,
                    "path_owner_matches": owner_ok,
                    "ok": ok,
                }
            )
            print(
                f"Legacy preflight {target['path']} id={target['id']} "
                f"title={actual_title!r} owner_ok={owner_ok} (ok={ok})",
                flush=True,
            )
            if not ok:
                raise RuntimeError(
                    f"Legacy preflight mismatch for {target['path']}: "
                    f"{actual_title!r} {actual_path}; nothing was deleted."
                )

        # 3) Ensure the deletion set is exactly these five IDs.
        target_ids = {t["id"] for t in LEGACY}
        if len(target_ids) != 5 or not target_ids.issubset(set(by_id)):
            raise RuntimeError("Deletion allowlist does not resolve to exactly five live pages.")
        report["preflight"]["passed"] = True
        print("All preflight checks passed. Deleting the five legacy pages.", flush=True)

        # 4) Delete permanently, then verify each is gone.
        for target in LEGACY:
            page = get_page(service, blog_id, target["id"])
            if page is None:
                report["already_missing"].append({"id": target["id"], "path": target["path"]})
                continue
            service.pages().delete(
                blogId=blog_id, pageId=target["id"], useTrash=False
            ).execute()
            if get_page(service, blog_id, target["id"]) is not None:
                raise RuntimeError(f"Legacy page still exists after delete: {target['id']}")
            report["deleted"].append(
                {
                    "id": target["id"],
                    "title": target["title"],
                    "path": target["path"],
                    "replaced_by": target["replaced_by"],
                    "state": "permanently-deleted",
                }
            )
            print(f"Permanently deleted legacy page: {target['path']}", flush=True)
            import time
            time.sleep(0.5)

        remaining = list_pages(service, blog_id)
        report["untouched_pages_after"] = len(remaining)
        remaining_ids = {str(p["id"]) for p in remaining}
        if target_ids & remaining_ids:
            raise RuntimeError("A legacy ID is still present after deletion.")
        report["remaining_pages"] = [
            {"id": str(p["id"]), "title": p.get("title"), "url": p.get("url")}
            for p in remaining
        ]
        report["finished_at_utc"] = now()
        report["result"] = "success"
        save(report)
        return 0

    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        print(f"FAILED: {message}", flush=True)
        report["errors"].append(message)
        report["finished_at_utc"] = now()
        report["result"] = "failed"
        save(report)
        return 1


if __name__ == "__main__":
    sys.exit(main())
