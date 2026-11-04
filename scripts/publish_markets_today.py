"""Publish the existing Markets Today page and retire its authorized old ranking post.

The page is patched in place. Post deletion is limited to one exact title and
label; the script never creates, edits, or removes unrelated posts.
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
POST_TITLE = "Top 5,000 Market Instruments: Category-Aware Activity Directory"
POST_LABEL = "Top-5000-Markets"


def preflight() -> str:
    if not PAGE_BODY.is_file():
        raise SystemExit(f"Missing publication input: {PAGE_BODY}")
    page = PAGE_BODY.read_text(encoding="utf-8")
    if "/p/financial-disclaimer-milled-edge.html" not in page:
        raise SystemExit("Refusing to publish: financial disclaimer link is missing")
    if "Search all 450,000+ market instruments" not in page:
        raise SystemExit("Refusing to publish: all-markets search heading is missing")
    for marker in ("Top 50,000 market directory", "dywTop50000", "dywCountry", "top-50000.json", "Top-5000-Markets"):
        if marker in page:
            raise SystemExit(f"Refusing to publish: retired Top 50,000 content remains: {marker}")
    required_browse = (
        "dyw-division-index", "dywDivisionIndex", "dywDivisionDirectory",
        "MARKET_DIVISIONS", "dyw-ticker-viewport", "pointerdown", "pointermove",
        "pointerup", "dywInstrumentResults", "dywCategoryList", "dywAnalysis",
    )
    missing = [marker for marker in required_browse if marker not in page]
    if missing:
        raise SystemExit("Refusing to publish: incomplete division/category browse flow: " + ", ".join(missing))
    return page


def list_posts(service, blog_id: str, statuses: list[str] | None = None) -> list[dict]:
    posts: list[dict] = []
    token = None
    while True:
        kwargs = {"blogId": blog_id, "fetchBodies": False, "maxResults": 500}
        if token:
            kwargs["pageToken"] = token
        # Inspect live, draft, and scheduled posts so the allowlisted post is
        # removed regardless of publication state. Status is a list filter,
        # not a field on the Blogger Post resource.
        kwargs["status"] = statuses or ["LIVE", "DRAFT", "SCHEDULED"]
        response = service.posts().list(**kwargs).execute()
        posts.extend(response.get("items", []))
        token = response.get("nextPageToken")
        if not token:
            return posts


def is_retired_ranking_post(post: dict) -> bool:
    labels = post.get("labels") or []
    return post.get("title", "").strip() == POST_TITLE and (not labels or POST_LABEL in labels)


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
        annotation = detail.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error file=.github/workflows/publish-markets-today.yml,title=Market directory publish::{annotation}", flush=True)
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            with open(summary_path, "a", encoding="utf-8") as summary:
                summary.write(f"## Blogger publish diagnostic\n\n{safe}\n")
        raise
    print(f"::notice title=Blogger publish::Completed stage: {stage}", flush=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()

    page_content = preflight()
    if args.dry_run:
        print("Local preflight only; no Blogger API calls or remote writes.")
        print(f"Markets Today page: {len(page_content):,} characters")
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

    posts = call_with_report("list Blogger posts to locate the one retired ranking post", lambda: list_posts(service, str(blog["id"])))
    post_matches = [p for p in posts if is_retired_ranking_post(p)]
    for target in post_matches:
        call_with_report("delete the exact allowlisted retired Top 5,000 post", lambda target=target: service.posts().delete(
            blogId=blog["id"],
            postId=target["id"],
        ).execute())

    call_with_report("patch the existing Markets Today page", lambda: service.pages().patch(blogId=blog["id"], pageId=page["id"], body={"content": page_content}).execute())
    remaining = call_with_report("verify the retired Top 5,000 post is absent", lambda: list_posts(service, str(blog["id"])))
    if any(is_retired_ranking_post(p) for p in remaining):
        print("::error title=Blogger post removal verification::The allowlisted Top 5,000 post still appears after deletion", flush=True)
        raise SystemExit("Top 5,000 post removal did not verify")
    print(f"Updated existing /p/{SLUG}.html ({len(page_content):,} characters).")
    print(f"Retired exact Top 5,000 post: {len(post_matches)} matching post(s) removed; no other posts were touched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
