#!/usr/bin/env python3
"""Publish the five approved MILLED EDGE pages live at their exact approved URLs.

Rules:
  * Page copy is read verbatim from publish/*.html and never edited.
  * Only the five exact paths below are created/adopted and published.
  * Blogger must return the exact expected URL; a different URL aborts the run.
  * Every URL is verified with a real HTTP request (status 200 + page title).
  * No legacy page is deleted. No posts are touched. No theme is installed.
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from googleapiclient.errors import HttpError

from blogger_client import get_blog_by_url, get_blogger_service, load_site_config

ROOT = Path(__file__).resolve().parents[1]
TRIGGER = ROOT / "trigger" / "publish-five-pages-live.txt"
CONFIRM = "CONFIRM: PUBLISH FIVE MILLED EDGE PAGES LIVE"
REPORT_PATHS = [
    ROOT / "reports" / "publish-five-pages-report.json",
    ROOT / "artifacts" / "publish-five-pages-report.json",
]
BLOG_URL = "https://millededgeindia.blogspot.com/"
EXPECTED_BLOG_ID = "8911514070006792465"

# Visible label -> exact approved path -> seed title that Blogger slugifies to that path.
PAGES = [
    {
        "display_title": "About us",
        "slug": "about-milled-edge",
        "seed_title": "About Milled Edge",
        "content_file": "publish/about_us.html",
    },
    {
        "display_title": "Contact us",
        "slug": "contact-milled-edge",
        "seed_title": "Contact Milled Edge",
        "content_file": "publish/contact_us.html",
    },
    {
        "display_title": "Privacy Policy",
        "slug": "privacy-policy-milled-edge",
        "seed_title": "Privacy Policy Milled Edge",
        "content_file": "publish/privacy_policy.html",
    },
    {
        "display_title": "Financial Disclaimer",
        "slug": "financial-disclaimer-milled-edge",
        "seed_title": "Financial Disclaimer Milled Edge",
        "content_file": "publish/financial_disclaimer.html",
    },
    {
        "display_title": "Terms & Conditions",
        "slug": "terms-milled-edge",
        "seed_title": "Terms Milled Edge",
        "content_file": "publish/terms_conditions.html",
    },
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def page_path(page: dict) -> str:
    return urlparse(page.get("url", "")).path


def expected_path(spec: dict) -> str:
    return "/p/" + spec["slug"] + ".html"


def save(report: dict) -> None:
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    for path in REPORT_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print("Report saved: " + str(REPORT_PATHS[0]), flush=True)
    print(text, flush=True)


def list_pages(service, blog_id: str) -> list[dict]:
    out: list[dict] = []
    request = service.pages().list(blogId=blog_id, maxResults=500, view="ADMIN")
    while request is not None:
        response = request.execute()
        out.extend(response.get("items", []))
        request = service.pages().list_next(request, response)
    return out


def get_page(service, blog_id: str, page_id: str):
    try:
        return service.pages().get(
            blogId=blog_id, pageId=str(page_id), view="ADMIN"
        ).execute()
    except HttpError as exc:
        if getattr(exc.resp, "status", None) == 404:
            return None
        raise


def remove_own_page(service, blog_id: str, page_id: str) -> None:
    try:
        service.pages().delete(
            blogId=blog_id, pageId=str(page_id), useTrash=False
        ).execute()
    except Exception as exc:  # cleanup is best effort, never fatal
        print(f"Cleanup warning for page {page_id}: {exc}", flush=True)


def fetch_page(url: str):
    """Return (http_status, <title> text). Network is available on the runner."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; MILLED-EDGE-url-verifier/1.0)",
            "Accept": "text/html,*/*",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
            body = response.read(3_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read(3_000_000).decode("utf-8", "replace")
    match = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
    title = html.unescape(re.sub(r"\s+", " ", match.group(1)).strip()) if match else ""
    return status, title


def main() -> int:
    if not TRIGGER.exists() or TRIGGER.read_text(encoding="utf-8").strip() != CONFIRM:
        print("Inactive trigger; nothing published.", flush=True)
        return 0

    report = {
        "mode": "publish-five-pages-live",
        "started_at_utc": now(),
        "blog": {},
        "authorized": [
            {"display_title": p["display_title"], "expected_path": expected_path(p)}
            for p in PAGES
        ],
        "pages": [],
        "http_checks": [],
        "legacy_deleted": [],
        "other_pages_or_posts_touched": [],
        "cleanup": [],
        "errors": [],
        "result": "running",
    }
    created_ids: list[tuple[str, str]] = []
    service = None
    blog_id = ""

    try:
        config = load_site_config()
        if config.get("blog_url", "").rstrip("/") != BLOG_URL.rstrip("/"):
            raise RuntimeError("config/site.json blog URL mismatch; aborting.")
        if str(config.get("expected_blog_id")) != EXPECTED_BLOG_ID:
            raise RuntimeError("config/site.json expected blog ID mismatch; aborting.")

        contents = {}
        for spec in PAGES:
            path = ROOT / spec["content_file"]
            text = path.read_text(encoding="utf-8")
            if len(text) < 1000:
                raise RuntimeError(f"Page copy looks empty: {spec['content_file']}")
            contents[spec["slug"]] = text
        print("Page copy preflight: 5 files read verbatim.", flush=True)

        service = get_blogger_service()
        blog = get_blog_by_url(service, config["blog_url"])
        blog_id = str(blog["id"])
        if blog_id != EXPECTED_BLOG_ID:
            raise RuntimeError(f"Blog ID mismatch: expected {EXPECTED_BLOG_ID}, got {blog_id}")
        if blog.get("url", "").rstrip("/") != BLOG_URL.rstrip("/"):
            raise RuntimeError(f"Blog URL mismatch: {blog.get('url')}")
        report["blog"] = {"id": blog_id, "url": blog.get("url"), "name": blog.get("name")}

        current = list_pages(service, blog_id)
        by_path = {page_path(p): p for p in current if p.get("url")}
        print(f"Existing pages on blog: {len(current)}", flush=True)

        prepared = []
        for spec in PAGES:
            expected = expected_path(spec)
            display = spec["display_title"]
            content = contents[spec["slug"]]
            existing = by_path.get(expected)
            allowed = {display.casefold(), spec["seed_title"].casefold()}

            if existing:
                found_title = (existing.get("title") or "").strip()
                if found_title.casefold() not in allowed:
                    raise RuntimeError(
                        f"URL {expected} belongs to an unexpected page "
                        f"{found_title!r} (id {existing.get('id')}); refusing to overwrite."
                    )
                page_id = str(existing["id"])
                page = service.pages().patch(
                    blogId=blog_id,
                    pageId=page_id,
                    body={"title": display, "content": content},
                ).execute()
                if page_path(page) != expected:
                    raise RuntimeError(
                        f"Updating {display} changed its URL to {page.get('url')}; "
                        f"expected {expected}."
                    )
                adopted = True
            else:
                created = service.pages().insert(
                    blogId=blog_id,
                    body={
                        "kind": "blogger#page",
                        "title": spec["seed_title"],
                        "content": content,
                    },
                    isDraft=True,
                ).execute()
                page_id = str(created["id"])
                created_ids.append((page_id, expected))
                print(f"Draft created for {display}: id={page_id} url={created.get('url')}", flush=True)

                # Publish with the seed title so the generated slug is locked in.
                service.pages().publish(blogId=blog_id, pageId=page_id).execute()
                page = get_page(service, blog_id, page_id)
                if page is None or page_path(page) != expected:
                    got = page.get("url") if page else "missing"
                    raise RuntimeError(
                        f"Blogger returned a different URL for {display}: {got}; "
                        f"expected {expected}. Aborting."
                    )
                # Set the reader-facing label after the URL exists; verify it did not move.
                page = service.pages().patch(
                    blogId=blog_id,
                    pageId=page_id,
                    body={"title": display, "content": content},
                ).execute()
                if page_path(page) != expected:
                    raise RuntimeError(
                        f"Display-title update changed the URL for {display}: "
                        f"{page.get('url')}; expected {expected}."
                    )
                adopted = False

            prepared.append(
                {
                    "id": page_id,
                    "display_title": display,
                    "expected_path": expected,
                    "content_file": spec["content_file"],
                    "adopted_existing": adopted,
                }
            )
            print(f"Prepared {display} at {expected}", flush=True)

        # Final API verification: every page must be LIVE at its exact approved URL.
        for item in prepared:
            page = get_page(service, blog_id, item["id"])
            if page is None:
                raise RuntimeError(f"Missing replacement page {item['display_title']}")
            if page.get("status") != "LIVE":
                service.pages().publish(blogId=blog_id, pageId=item["id"]).execute()
                page = get_page(service, blog_id, item["id"])
            if (
                page is None
                or page_path(page) != item["expected_path"]
                or (page.get("title") or "").strip().casefold()
                != item["display_title"].casefold()
                or page.get("status") != "LIVE"
            ):
                raise RuntimeError(
                    f"Live API verification failed for {item['display_title']}: {page}"
                )
            item["url"] = page["url"]
            item["status"] = page["status"]
            report["pages"].append(
                {
                    "id": item["id"],
                    "title": item["display_title"],
                    "url": item["url"],
                    "status": "LIVE",
                    "content_file": item["content_file"],
                    "adopted_existing": item["adopted_existing"],
                }
            )
            print(f"API verified LIVE: {item['url']}", flush=True)

        # Real HTTP verification from the runner (Blogger CDN can lag a little).
        all_ok = True
        for item in prepared:
            wanted = html.unescape(item["display_title"]).casefold()
            last_status, last_title = 0, ""
            ok = False
            for attempt in range(4):
                try:
                    last_status, last_title = fetch_page(item["url"])
                except Exception as exc:
                    last_status, last_title = 0, f"request error: {exc}"
                ok = last_status == 200 and wanted in html.unescape(last_title).casefold()
                if ok:
                    break
                time.sleep(6)
            report["http_checks"].append(
                {
                    "url": item["url"],
                    "expected_path": item["expected_path"],
                    "status_code": last_status,
                    "page_title": last_title,
                    "expected_title": item["display_title"],
                    "ok": ok,
                }
            )
            print(
                f"HTTP check {item['url']} -> {last_status} / {last_title!r} (ok={ok})",
                flush=True,
            )
            if not ok:
                all_ok = False

        report["finished_at_utc"] = now()
        report["result"] = "success" if all_ok else "failed"
        if not all_ok:
            report["errors"].append(
                "One or more approved URLs did not return HTTP 200 with the expected title."
            )
        report["note"] = (
            "No legacy pages deleted; no posts touched; optional theme not installed."
        )
        save(report)
        return 0 if all_ok else 1

    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        print(f"FAILED: {message}", flush=True)
        report["errors"].append(message)
        # Remove only pages this run created that are still drafts or landed on a wrong URL.
        if service and blog_id:
            for page_id, expected in created_ids:
                page = get_page(service, blog_id, page_id)
                if page is None:
                    continue
                if page_path(page) != expected or page.get("status") != "LIVE":
                    remove_own_page(service, blog_id, page_id)
                    report["cleanup"].append(
                        {"id": page_id, "reason": "draft or unexpected URL", "action": "deleted"}
                    )
                else:
                    report["cleanup"].append(
                        {"id": page_id, "reason": "live at approved URL", "action": "kept"}
                    )
        report["finished_at_utc"] = now()
        report["result"] = "failed"
        report["note"] = (
            "No legacy pages deleted; no posts touched; optional theme not installed."
        )
        save(report)
        return 1


if __name__ == "__main__":
    sys.exit(main())
