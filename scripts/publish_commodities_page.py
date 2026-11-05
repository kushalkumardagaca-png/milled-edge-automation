"""Publish a commodity-only Blogger Page, verify it publicly, then trash retired posts.

This is page publishing only; it never builds or writes the Blogger theme.
The nine old commodity category posts are allowlisted by stable category labels
and catalog titles, and are moved to Blogger trash (not permanently erased).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
BODY_PATH = ROOT / "content" / "pages" / "commodities.html"
DATA_PATH = ROOT / "content" / "commodity-price-board.json"
CATALOG_PATH = ROOT / "content" / "market-posts" / "batch-1-catalog.json"
PAGE_TITLE = "Commodities"
PAGE_PATH = "/p/commodities.html"
EXPECTED_SLUGS = {
    "commodities-commodity-precious",
    "commodities-commodity-base-metals",
    "commodities-commodity-minerals",
    "commodities-commodity-gases",
    "commodities-commodity-energy",
    "commodities-commodity-grains",
    "commodities-commodity-fibres-softs",
    "commodities-commodity-livestock",
    "commodities-commodity-forestry",
}


def preflight() -> tuple[str, dict, dict[str, str]]:
    if not BODY_PATH.is_file() or not DATA_PATH.is_file() or not CATALOG_PATH.is_file():
        raise SystemExit("Commodity page body, benchmark data, or retired-post catalog is missing.")
    body = BODY_PATH.read_text(encoding="utf-8")
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if len(data.get("items", [])) != 55:
        raise SystemExit("Refusing to publish: expected 55 commodity-only benchmark rows.")
    required_markers = (
        "me-commodity-page", "me-c-item", "me-c-topic-labels", "me-c-faq",
        "World Bank", "schema.org", "spatialCoverage", "canonical",
        "m.description", "Country / location", "Formal series", "Common name",
        "PHYSICAL COMMODITY PRICE BENCHMARK", "No exchange ticker assigned",
    )
    missing = [marker for marker in required_markers if marker.casefold() not in body.casefold()]
    if missing:
        raise SystemExit("Refusing to publish: SEO/GEO/content preflight markers are missing: " + ", ".join(missing))
    if "#meMarketPanel" in body or "CategoryID-commodities-" in body:
        raise SystemExit("Refusing to publish a commodity page containing theme/category-menu wiring.")
    titles = {x["slug"]: x["title"] for x in catalog if x.get("slug") in EXPECTED_SLUGS}
    if set(titles) != EXPECTED_SLUGS:
        raise SystemExit("Refusing to delete: the nine retired commodity post titles could not be validated from the catalog.")
    return body, data, titles


def list_pages(service, blog_id: str) -> list[dict]:
    found, token = [], None
    while True:
        args = {"blogId": blog_id, "maxResults": 500, "fetchBodies": False}
        if token:
            args["pageToken"] = token
        response = service.pages().list(**args).execute()
        found.extend(response.get("items", []))
        token = response.get("nextPageToken")
        if not token:
            return found


def list_posts(service, blog_id: str) -> list[dict]:
    found, token = [], None
    while True:
        args = {"blogId": blog_id, "maxResults": 500, "fetchBodies": False, "status": ["LIVE", "DRAFT", "SCHEDULED"]}
        if token:
            args["pageToken"] = token
        response = service.posts().list(**args).execute()
        found.extend(response.get("items", []))
        token = response.get("nextPageToken")
        if not token:
            return found


def public_check(url: str) -> tuple[bool, str]:
    last = "not checked"
    for attempt in range(5):
        if attempt:
            time.sleep(min(8, 2 * attempt))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; MilledEdgeCommodityPageCheck/1.0)"})
            with urllib.request.urlopen(req, timeout=25) as response:
                page = response.read().decode("utf-8", "replace")
                if response.status == 200 and "me-commodity-page" in page and "me-c-item" in page and "Gold" in page and "Silver" in page:
                    return True, f"HTTP 200; commodity-only board markers found ({len(page):,} bytes)."
                last = f"HTTP {response.status}; page markers missing."
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
    return False, last


def summary(text: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(text + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--trash-retired-posts", action="store_true", help="after page verification, move the nine allowlisted old commodity posts to Blogger trash")
    args = parser.parse_args()
    body, data, expected_titles = preflight()
    print(f"Preflight: /p/commodities.html; {len(data['items'])} physical commodity price series; source month {data['price_month']}.")
    print("Retired post allowlist:", ", ".join(sorted(EXPECTED_SLUGS)))
    if args.dry_run:
        print("Dry run only; no Blogger calls or remote writes.")
        return 0
    if args.confirm != "PUBLISH":
        print("Refusing to write without --confirm PUBLISH", file=sys.stderr)
        return 2
    if not args.trash_retired_posts:
        print("Refusing to retire old posts without the explicit --trash-retired-posts flag", file=sys.stderr)
        return 2

    from blogger_client import get_blogger_service, get_blog_by_url, load_site_config
    config = load_site_config()
    service = get_blogger_service()
    blog = get_blog_by_url(service, config["blog_url"])
    blog_id = str(blog.get("id"))
    if blog_id != str(config["expected_blog_id"]):
        raise SystemExit("Resolved Blogger blog ID did not match config/site.json; no writes made.")

    page_matches = [p for p in list_pages(service, blog_id) if urlparse(p.get("url", "")).path.rstrip("/") == PAGE_PATH]
    if len(page_matches) > 1:
        raise SystemExit("More than one /p/commodities.html page exists; no page or post writes made.")
    if page_matches:
        page = page_matches[0]
        saved = service.pages().patch(blogId=blog_id, pageId=page["id"], body={"title": PAGE_TITLE, "content": body}).execute()
        action = "updated"
    else:
        saved = service.pages().insert(blogId=blog_id, body={"title": PAGE_TITLE, "content": body}, isDraft=False).execute()
        action = "created"
    page_url = saved.get("url") or (page_matches[0].get("url") if page_matches else "")
    if urlparse(page_url).path.rstrip("/") != PAGE_PATH:
        raise SystemExit(f"Page {action}, but Blogger returned unexpected path {page_url!r}; old posts were not touched.")
    ok, detail = public_check(page_url)
    if not ok:
        raise SystemExit(f"Commodity page {page_url} was not publicly verified ({detail}); old posts were not touched.")
    print(f"{action.title()} and publicly verified {page_url}: {detail}", flush=True)

    all_posts = list_posts(service, blog_id)
    matches: dict[str, list[dict]] = {slug: [] for slug in EXPECTED_SLUGS}
    unexpected = []
    for post in all_posts:
        for label in post.get("labels") or []:
            if not label.startswith("CategoryID-commodities-"):
                continue
            slug = label[len("CategoryID-"):]
            if slug not in EXPECTED_SLUGS:
                unexpected.append({"id": post.get("id"), "title": post.get("title"), "label": label})
            else:
                matches[slug].append(post)
    if unexpected:
        raise SystemExit(f"Page is live, but unexpected commodity category posts were found; refusing to delete outside the allowlist: {unexpected}")
    duplicates = {slug: len(posts) for slug, posts in matches.items() if len(posts) > 1}
    if duplicates:
        raise SystemExit(f"Page is live, but duplicate retired-post labels were found; refusing deletion: {duplicates}")
    title_mismatches = [
        f"{slug}: {posts[0].get('title')!r} != {expected_titles[slug]!r}"
        for slug, posts in matches.items() if posts and posts[0].get("title") != expected_titles[slug]
    ]
    if title_mismatches:
        raise SystemExit("Page is live, but post title validation failed; no posts deleted: " + "; ".join(title_mismatches))

    deleted, already_absent = [], []
    for slug in sorted(EXPECTED_SLUGS):
        items = matches[slug]
        if not items:
            already_absent.append(slug)
            continue
        post = items[0]
        service.posts().delete(blogId=blog_id, postId=post["id"], useTrash=True).execute()
        deleted.append({"slug": slug, "id": str(post["id"]), "title": post.get("title"), "url": post.get("url")})
        print(f"Moved to Blogger trash: {slug} | {post.get('url')}", flush=True)
        time.sleep(0.5)

    remaining = list_posts(service, blog_id)
    remaining_slugs = sorted({
        label[len("CategoryID-"):]
        for post in remaining for label in (post.get("labels") or [])
        if label.startswith("CategoryID-commodities-") and label[len("CategoryID-"):] in EXPECTED_SLUGS
    })
    if remaining_slugs:
        summary("## Commodity page published; retired-post verification failed\n\n" + json.dumps({"page_url": page_url, "deleted": deleted, "still_listed": remaining_slugs}, indent=2))
        raise SystemExit("Some allowlisted commodity posts remain live/draft/scheduled after trashing: " + ", ".join(remaining_slugs))
    message = f"## Commodity-only page published and verified\n\n- Page: {page_url}\n- Commodity benchmark series: {len(data['items'])}\n- Old category posts moved to Blogger trash: {len(deleted)}\n- Already absent: {len(already_absent)}\n- No theme file was read, generated, or changed.\n"
    summary(message + "\n" + json.dumps({"deleted": deleted, "already_absent": already_absent}, indent=2))
    print(f"Verified: {page_url} is public; {len(deleted)} old commodity category posts moved to trash; {len(already_absent)} already absent.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit as exc:
        if exc.code not in (0, None):
            detail = str(exc)
            for secret_name in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"):
                secret = os.environ.get(secret_name, "")
                if secret:
                    detail = detail.replace(secret, "[redacted]")
            print(f"::error title=Commodity-page publishing failed::{detail}", flush=True)
            summary("## Commodity page publish failed\n\n" + detail)
        raise
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"
        for secret_name in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"):
            secret = os.environ.get(secret_name, "")
            if secret:
                detail = detail.replace(secret, "[redacted]")
        print(f"::error title=Commodity-page publishing failed::{detail}", flush=True)
        summary("## Commodity page publish failed\n\n" + detail)
        raise
