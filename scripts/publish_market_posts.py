"""Publish or safely update one prepared Blogger market-category post batch.

The publisher is explicit about batch number and requires --confirm PUBLISH.
It never deletes posts or pages and uses stable category labels for retries.
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
POST_ROOT = ROOT / "content" / "market-posts"
BATCH_SIZES = {1:20, 2:20, 3:22, 4:22, 5:20}
WRITE_DELAY_SECONDS = 20


def load_catalog(batch: int) -> list[dict]:
    catalog_path = POST_ROOT / f"batch-{batch}-catalog.json"
    if not catalog_path.is_file():
        raise SystemExit(f"Missing generated post catalog: {catalog_path}")
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    expected = BATCH_SIZES[batch]
    if len(data) != expected:
        raise SystemExit(f"Expected {expected} category posts in batch {batch}, found {len(data)}")
    ids = [x["slug"] for x in data]
    if len(set(ids)) != len(ids):
        raise SystemExit("Duplicate category-post IDs in batch catalog")
    return data


def post_body(item: dict, batch: int) -> str:
    path = POST_ROOT / f"batch-{batch}" / f"{item['slug']}.html"
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
    if '"datePublished"' not in body:
        raise SystemExit(f"Post {item['slug']} has no publication date; regenerate with --publication-date before live publishing")
    if any(marker in body for marker in ("DY_SEO_META_START", "DY_BRAND_IDENTITY_START", "DY_PAGE_FAMILY_START", "DY_BRAND_SEO_START")):
        raise SystemExit(f"Post {item['slug']} contains source-template markers that should not be published")
    if len(body) > 1_000_000:
        raise SystemExit(f"Post {item['slug']} exceeds the 1 MB safety threshold")
    return body


def preflight(batch: int) -> list[tuple[dict, str, list[str]]]:
    catalog = load_catalog(batch)
    prepared = []
    for item in catalog:
        if item.get("batch") != batch:
            raise SystemExit(f"Catalog entry {item.get('slug')} is assigned to batch {item.get('batch')}, not {batch}")
        body = post_body(item, batch)
        labels = list(dict.fromkeys(item["labels"] + ["MarketCategoryPost", "CategoryID-" + item["slug"]]))
        if sum(len(x) for x in labels) > 200:
            raise SystemExit(f"Post labels exceed Blogger's combined length safety limit: {item['slug']}")
        prepared.append((item, body, labels))
    if len({x[0]["title"] for x in prepared}) != BATCH_SIZES[batch]:
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
        result = service.posts().list(**kwargs).execute(num_retries=10)
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
    parser.add_argument("--batch", type=int, required=True, choices=range(1, 6))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--allow-public-check-pending", action="store_true", help="continue batch sequence; run the separate final feed verification")
    args = parser.parse_args()
    prepared = preflight(args.batch)
    print(f"Validated batch {args.batch}: {len(prepared)} category posts; {sum(len(body) for _, body, _ in prepared):,} HTML characters total.")
    print("This publisher never deletes existing posts or pages.")
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
        # Existing live category posts are treated as published once their stable
        # identity, title, and required labels match. Avoid fetching or comparing
        # large HTML bodies: Blogger can throttle those full-body catalog reads.
        if (post and post.get("status") == "LIVE" and post.get("title") == item["title"]
                and set(labels).issubset(set(post.get("labels") or []))):
            results.append({"id": item["slug"], "title": item["title"], "url": post["url"], "action": "unchanged", "labels": labels})
            print(f"unchanged: {item['title']} — {post['url']}", flush=True)
            continue
        try:
            if post:
                saved = service.posts().patch(blogId=blog["id"], postId=post["id"], body=payload).execute(num_retries=3)
                action = "updated"
                if saved.get("status") == "DRAFT":
                    saved = service.posts().publish(blogId=blog["id"], postId=post["id"]).execute(num_retries=3)
            else:
                saved = service.posts().insert(blogId=blog["id"], body=payload, isDraft=False).execute(num_retries=3)
                # Pace writes so a batch retry after a transient Blogger quota response remains gentle.
                action = "created"
            if not saved.get("url") or not saved.get("id"):
                raise RuntimeError("Blogger API response omitted the new post URL or ID")
            results.append({"id": item["slug"], "title": item["title"], "url": saved["url"], "action": action, "labels": labels})
            print(f"{action}: {item['title']} — {saved['url']}", flush=True)
        except Exception as exc:
            failures.append({"id": item["slug"], "error": f"{type(exc).__name__}: {exc}"})
            print(f"FAILED: {item['slug']} — {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        finally:
            time.sleep(WRITE_DELAY_SECONDS)

    if failures:
        for failure in failures:
            detail = failure["error"].replace("%", "%25").replace("\\r", " ").replace("\\n", " ").replace(":", "%3A")
            print(f"::error title=Market category post failure::{failure['id']} — {detail}", flush=True)
        write_summary(f"## Market-category post batch {args.batch}: partial failure\n\n" + json.dumps({"published_or_updated": results, "failures": failures}, indent=2))
        raise SystemExit(f"{len(failures)} posts failed; {len(results)} created or updated. No existing pages were deleted.")

    # Public checks happen after API writes; a transient delivery failure is
    # reported clearly and does not trigger any destructive rollback.
    public_results = []
    for result in results:
        ok, detail = public_check(result["url"])
        public_results.append({"url": result["url"], "ok": ok, "detail": detail})
        print(("verified: " if ok else "public-check pending: ") + result["url"] + " — " + detail, flush=True)
    summary = f"## Market-category post batch {args.batch}\n\n" + json.dumps({"posts": results, "public_checks": public_results}, indent=2)
    write_summary(summary)
    if len(results) != BATCH_SIZES[args.batch]:
        raise SystemExit(f"Expected {BATCH_SIZES[args.batch]} results, got {len(results)}")
    if not all(x["ok"] for x in public_results):
        message = f"All {len(results)} posts in batch {args.batch} were submitted, but one or more immediate URL checks are still pending."
        if not args.allow_public_check_pending:
            raise SystemExit(message + " Do not retire old pages.")
        print("WARNING: " + message + " Final feed verification remains mandatory.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
