"""Publish the existing Markets Today page and one idempotent Top 5,000 post.

The page is patched in place. The only post this script may create or update is
its exact title/label allowlist; it never creates pages or unrelated posts.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUG = "markets-today"
PAGE_BODY = ROOT / "content" / "markets-today.html"
DATA_FILE = ROOT / "content" / "market-data" / "top-50000.json"
POST_BODY = ROOT / "content" / "posts" / "top-5000-market-instruments.html"
POST_TITLE = "Top 5,000 Market Instruments: Category-Aware Activity Directory"
POST_LABEL = "Top-5000-Markets"


def preflight() -> tuple[str, str]:
    for path in (PAGE_BODY, DATA_FILE, POST_BODY):
        if not path.is_file():
            raise SystemExit(f"Missing publication input: {path}")
    page = PAGE_BODY.read_text(encoding="utf-8")
    post = POST_BODY.read_text(encoding="utf-8")
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    if len(entries) != 50_000 or data.get("metadata", {}).get("total") != 50_000:
        raise SystemExit("Refusing to publish: Top 50,000 data file must contain exactly 50,000 entries")
    if not data.get("metadata", {}).get("asOf"):
        raise SystemExit("Refusing to publish: ranking data has no as-of date")
    # The body contains 5,000 instrument rows plus one header row per category.
    row_count = post.count("<tr>")
    header_count = post.count("<thead>")
    if row_count - header_count != 5_000:
        raise SystemExit(f"Refusing to publish: expected 5,000 instrument rows, found {row_count - header_count}")
    if "/p/financial-disclaimer-milled-edge.html" not in page:
        raise SystemExit("Refusing to publish: financial disclaimer link is missing")
    for marker in ("Top 50,000 market directory", "dywTopCategory", "dywCountry", "top-50000.json"):
        if marker not in page:
            raise SystemExit(f"Refusing to publish: Markets Today is missing required marker: {marker}")
    for marker in ("Top 5,000 Market Instruments", "Methodology and source notes", "As of "):
        if marker not in post:
            raise SystemExit(f"Refusing to publish: Top 5,000 post is missing marker: {marker}")
    if "TradingView Global Scanner" not in post or "not a universal" not in post.lower():
        raise SystemExit("Refusing to publish: Top 5,000 post source/method notes are missing")
    return page, post


def list_posts(service, blog_id: str, statuses: list[str] | None = None) -> list[dict]:
    posts: list[dict] = []
    token = None
    while True:
        kwargs = {"blogId": blog_id, "fetchBodies": False, "maxResults": 500}
        if token:
            kwargs["pageToken"] = token
        # Fetch live, draft, and scheduled posts so a prior partial run cannot
        # cause the allowlisted post to be duplicated. Verification can request
        # LIVE alone; status is a list filter, not a Post resource field.
        kwargs["status"] = statuses or ["LIVE", "DRAFT", "SCHEDULED"]
        response = service.posts().list(**kwargs).execute()
        posts.extend(response.get("items", []))
        token = response.get("nextPageToken")
        if not token:
            return posts


def call_with_report(stage: str, fn):
    try:
        result = fn()
    except Exception as exc:
        status = getattr(exc, "status_code", None)
        message = str(exc)
        content = getattr(exc, "content", None)
        if content:
            try:
                body = json.loads(content.decode("utf-8") if isinstance(content, bytes) else content)
                message = body.get("error", {}).get("message", message)
            except Exception:
                pass
        detail = f"HTTP {status}: {message}" if status else f"{type(exc).__name__}: {message}"
        safe = f"Market Today publish stage failed — {stage}: {detail}"
        print(safe, file=sys.stderr, flush=True)
        annotation = detail.replace("%", "%25").replace("\\r", "%0D").replace("\\n", "%0A")
        print(f"::error file=.github/workflows/publish-markets-today.yml,title=Market directory publish::{annotation}", flush=True)
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as summary:
                summary.write(f"## Blogger publish diagnostic\\n\\n{safe}\\n")
        raise
    print(f"::notice title=Blogger publish::Completed stage: {stage}", flush=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()

    page_content, post_content = preflight()
    if args.dry_run:
        print("Local preflight only; no Blogger API calls or remote writes.")
        print(f"Markets Today page: {len(page_content):,} characters")
        print(f"Top 50,000 JSON: {DATA_FILE.stat().st_size:,} bytes")
        print(f"Top 5,000 post: {len(post_content):,} characters")
        return 0
    if args.confirm != "PUBLISH":
        print("Refusing to write without --confirm PUBLISH", file=sys.stderr)
        return 2

    from blogger_client import get_blogger_service, get_blog_by_url, load_site_config

    site = load_site_config()
    service = call_with_report("authenticate to Blogger", get_blogger_service)
    blog = call_with_report("resolve the configured blog", lambda: get_blog_by_url(service, site["blog_url"]))
    if str(blog["id"]) != str(site["expected_blog_id"]):
        print("Refusing to publish: resolved Blogger blog ID does not match config/site.json", file=sys.stderr)
        return 2

    pages = call_with_report("list existing pages", lambda: service.pages().list(blogId=blog["id"], fetchBodies=False, maxResults=50).execute().get("items", []))
    matches = [p for p in pages if p.get("url", "").rstrip("/").endswith(f"/p/{SLUG}.html")]
    if len(matches) != 1:
        print(f"Expected one existing /p/{SLUG}.html page; found {len(matches)}; no write made", file=sys.stderr)
        return 2
    page = matches[0]

    posts = call_with_report("list Blogger posts and check for the allowlisted title", lambda: list_posts(service, str(blog["id"])))
    post_matches = [p for p in posts if p.get("title", "").strip() == POST_TITLE]
    if len(post_matches) > 1:
        print(f"Refusing to write: found {len(post_matches)} posts with the allowlisted title", file=sys.stderr)
        return 2

    # The explicit one-post authorization is implemented narrowly: insert the
    # Top 5,000 post if absent; otherwise patch that same post in place.
    if post_matches:
        target = post_matches[0]
        result = call_with_report("update the existing allowlisted post", lambda: service.posts().patch(
            blogId=blog["id"],
            postId=target["id"],
            body={"title": POST_TITLE, "content": post_content, "labels": [POST_LABEL]},
            publish=True,
        ).execute())
        action = "updated"
    else:
        result = call_with_report("create the one allowlisted live post", lambda: service.posts().insert(
            blogId=blog["id"],
            body={"title": POST_TITLE, "content": post_content, "labels": [POST_LABEL]},
            isDraft=False,
        ).execute())
        action = "created"

    call_with_report("patch the existing Markets Today page", lambda: service.pages().patch(blogId=blog["id"], pageId=page["id"], body={"content": page_content}).execute())
    check = call_with_report("verify the Top 5,000 post title and label", lambda: service.posts().get(blogId=blog["id"], postId=result["id"], fetchBody=False).execute())
    if check.get("title") != POST_TITLE or POST_LABEL not in check.get("labels", []):
        detail = f"title={check.get('title')!r}; labels={check.get('labels')!r}"
        print(f"::error title=Blogger post content verification::{detail}", flush=True)
        raise SystemExit("Post write did not verify with the expected title and label")
    live_posts = call_with_report("verify the post is LIVE", lambda: list_posts(service, str(blog["id"]), statuses=["LIVE"]))
    if not any(p.get("id") == result["id"] for p in live_posts):
        print("::error title=Blogger publication verification::The allowlisted post ID was not returned by the LIVE posts filter", flush=True)
        raise SystemExit("Post write did not verify as LIVE")
    print(f"Updated existing /p/{SLUG}.html ({len(page_content):,} characters).")
    print(f"{action.title()} the single allowlisted Blogger post ({len(post_content):,} characters).")
    print(f"Post URL: {check.get('url', '(URL not returned)')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
