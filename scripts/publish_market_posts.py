"""Publish or safely update a prepared Blogger market-category post batch.

This first release is limited to batch 1 (20 posts). It never deletes posts or
pages and uses a stable per-post label to make retries idempotent.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POST_DIR = ROOT / "content" / "market-posts" / "batch-1"
CATALOG_PATH = ROOT / "content" / "market-posts" / "batch-1-catalog.json"


def load_catalog() -> list[dict]:
    if not CATALOG_PATH.is_file():
        raise SystemExit(f"Missing generated post catalog: {CATALOG_PATH}")
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if len(data) != 20:
        raise SystemExit(f"Expected exactly 20 category posts in batch 1, found {len(data)}")
    ids = [x["slug"] for x in data]
    if len(set(ids)) != len(ids):
        raise SystemExit("Duplicate category-post IDs in batch catalog")
    return data


def post_body(item: dict) -> str:
    path = POST_DIR / f"{item['slug']}.html"
    if not path.is_file():
        raise SystemExit(f"Missing generated post body: {path}")
    body = path.read_text(encoding="utf-8")
    required = [
        "window.ME_MARKET_POST_CONFIG=", "dyw-post-lane", "dywCompareOne",
        "application/ld+json", "/p/financial-disclaimer-milled-edge.html",
    ]
    missing = [x for x in required if x not in body]
    if missing:
        raise SystemExit(f"Post {item['slug']} is missing required functionality/metadata markers: {missing}")
    if len(body) > 1_000_000:
        raise SystemExit(f"Post {item['slug']} exceeds the 1 MB safety threshold")
    return body


def preflight() -> list[tuple[dict, str, list[str]]]:
    catalog = load_catalog()
    prepared = []
    for item in catalog:
        body = post_body(item)
        labels = list(dict.fromkeys(item["labels"] + ["MarketCategoryPost", "CategoryID-" + item["slug"]]))
        if sum(len(x) for x in labels) > 200:
            raise SystemExit(f"Post labels exceed Blogger's combined length safety limit: {item['slug']}")
        prepared.append((item, body, labels))
    if len({x[0]["title"] for x in prepared}) != 20:
        raise SystemExit("Post titles are not unique")
    return prepared


def write_summary(text: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def list_all_posts(service, blog_id: str) -> list[dict]:
    out, token = [], None
    while True:
        kwargs = {"blogId": blog_id, "fetchBodies": False, "maxResults": 500}
        if token:
            kwargs["pageToken"] = token
        result = service.posts().list(**kwargs).execute()
        out.extend(result.get("items", []))
        token = result.get("nextPageToken")
        if not token:
            return out


def public_check(url: str) -> tuple[bool, str]:
    last = "not checked"
    for delay in (0, 3, 7):
        if delay:
            time.sleep(delay)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; MilledEdgePublisher/1.0)"})
            with urllib.request.urlopen(req, timeout=25) as response:
                html = response.read().decode("utf-8", "replace")
                required = ("dyw-post-lane", "dywCompareOne", "application/ld+json")
                missing = [marker for marker in required if marker not in html]
                if response.status == 200 and not missing:
                    return True, f"HTTP 200, {len(html)} bytes; required features present"
                last = f"HTTP {response.status}, missing {missing}, {len(html)} bytes"
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
    return False, last


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()
    prepared = preflight()
    print(f"Validated {len(prepared)} category posts; {sum(len(body) for _, body, _ in prepared):,} HTML characters total.")
    print("Release order: 20 posts in this first batch; no legacy page/post deletion is part of this script.")
    if args.dry_run:
        return 0
    if args.confirm != "PUBLISH":
        print("Refusing to write without --confirm PUBLISH", file=sys.stderr)
        return 2

    from blogger_client import get_blogger_service, get_blog_by_url, load_site_config

    site = load_site_config()
    service = get_blogger_service()
    blog = get_blog_by_url(service, site["blog_url"])
    if str(blog.get("id")) != str(site["expected_blog_id"]):
        raise SystemExit("Resolved Blogger blog ID did not match config/site.json; no writes made")
    existing = list_all_posts(service, str(blog["id"]))
    by_label: dict[str, dict] = {}
    for post in existing:
        for label in post.get("labels") or []:
            if label.startswith("CategoryID-"):
                by_label[label] = post

    results = []
    failures = []
    for item, body, labels in prepared:
        identity = "CategoryID-" + item["slug"]
        post = by_label.get(identity)
        payload = {"title": item["title"], "content": body, "labels": labels}
        try:
            if post:
                saved = service.posts().patch(blogId=blog["id"], postId=post["id"], body=payload).execute()
                action = "updated"
                if saved.get("status") == "DRAFT":
                    saved = service.posts().publish(blogId=blog["id"], postId=post["id"]).execute()
            else:
                saved = service.posts().insert(blogId=blog["id"], body=payload, isDraft=False).execute()
                action = "created"
            if not saved.get("url") or not saved.get("id"):
                raise RuntimeError("Blogger API response omitted the new post URL or ID")
            results.append({"id": item["slug"], "title": item["title"], "url": saved["url"], "action": action, "labels": labels})
            print(f"{action}: {item['title']} — {saved['url']}", flush=True)
        except Exception as exc:
            failures.append({"id": item["slug"], "error": f"{type(exc).__name__}: {exc}"})
            print(f"FAILED: {item['slug']} — {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)

    if failures:
        write_summary("## Market-category post batch 1: partial failure\n\n" + json.dumps({"published_or_updated": results, "failures": failures}, indent=2))
        raise SystemExit(f"{len(failures)} posts failed; {len(results)} created or updated. No existing pages were deleted.")

    # Public checks happen after API writes; a transient delivery failure is
    # reported clearly and does not trigger any destructive rollback.
    public_results = []
    for result in results:
        ok, detail = public_check(result["url"])
        public_results.append({"url": result["url"], "ok": ok, "detail": detail})
        print(("verified: " if ok else "public-check pending: ") + result["url"] + " — " + detail, flush=True)
    summary = "## Market-category post batch 1\n\n" + json.dumps({"posts": results, "public_checks": public_results}, indent=2)
    write_summary(summary)
    if len(results) != 20:
        raise SystemExit(f"Expected 20 results, got {len(results)}")
    if not all(x["ok"] for x in public_results):
        raise SystemExit("All 20 posts were submitted, but one or more public checks did not pass; do not retire old pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
