"""Verify public Blogger URLs and features for a requested market-post batch range."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POST_ROOT = ROOT / "content" / "market-posts"
BLOG_URL = "https://millededgeindia.blogspot.com"
FEED_URL = BLOG_URL + "/feeds/posts/default/-/MarketCategoryPost?alt=json&max-results=18&start-index={}"
REQUIRED = ("dyw-post-lane", "dywAnalysis", "dywCompareOne", "dywCompareTwo", "application/ld+json")


def get_feed_entries() -> list[dict]:
    entries: list[dict] = []
    start = 1
    total = None
    while total is None or len(entries) < total:
        req = urllib.request.Request(FEED_URL.format(start), headers={"User-Agent": "Mozilla/5.0 (compatible; MilledEdgeReleaseCheck/1.0)"})
        with urllib.request.urlopen(req, timeout=30) as response:
            feed = json.loads(response.read().decode("utf-8", "replace"))["feed"]
        total = int(feed.get("openSearch$totalResults", {}).get("$t", 0))
        page = feed.get("entry", [])
        if not page:
            break
        entries.extend(page)
        start += len(page)
    return entries


def inspect(url: str) -> tuple[bool, str]:
    last = "not checked"
    for delay in (0, 4, 10, 20):
        if delay:
            time.sleep(delay)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; MilledEdgeReleaseCheck/1.0)"})
            with urllib.request.urlopen(req, timeout=30) as response:
                body = response.read().decode("utf-8", "replace")
                missing = [marker for marker in REQUIRED if marker not in body]
                stray = [marker for marker in ("DY_SEO_META_START", "DY_BRAND_IDENTITY_START", "DY_PAGE_FAMILY_START", "DY_BRAND_SEO_START") if marker in body]
                if response.status == 200 and not missing and not stray and '"datePublished"' in body:
                    return True, f"HTTP 200; {len(body)} bytes; features and publication schema found"
                last = f"HTTP {response.status}; missing {missing}; stray {stray}; {len(body)} bytes"
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
    return False, last


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batches", default="2,3,4,5")
    args = parser.parse_args()
    batches = [int(x) for x in args.batches.split(",") if x]
    expected: dict[str, dict] = {}
    for batch in batches:
        catalog_path = POST_ROOT / f"batch-{batch}-catalog.json"
        for item in json.loads(catalog_path.read_text(encoding="utf-8")):
            expected[item["slug"]] = item
    entries = get_feed_entries()
    live: dict[str, dict] = {}
    duplicates = []
    for entry in entries:
        labels = [x.get("term", "") for x in entry.get("category", [])]
        ids = [x[len("CategoryID-"):] for x in labels if x.startswith("CategoryID-")]
        if len(ids) != 1:
            continue
        if ids[0] in live:
            duplicates.append(ids[0])
            continue
        alt = next((x["href"] for x in entry.get("link", []) if x.get("rel") == "alternate"), None)
        if alt:
            live[ids[0]] = {"title": entry.get("title", {}).get("$t", ""), "url": alt, "labels": labels}
    missing = sorted(set(expected) - set(live))
    wrong_titles = [slug for slug in expected.keys() & live.keys() if expected[slug]["title"] != live[slug]["title"]]
    targets = [(slug, live[slug]["url"]) for slug in expected.keys() & live.keys()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        outcomes = list(pool.map(lambda x: (x[0], x[1], *inspect(x[1])), targets))
    failures = [{"id": slug, "url": url, "detail": detail} for slug, url, ok, detail in outcomes if not ok]
    report = {"expected": len(expected), "live_category_posts": len(live), "verified_target_posts": sum(ok for _, _, ok, _ in outcomes), "missing": missing, "duplicate_ids": sorted(set(duplicates)), "title_mismatches": wrong_titles, "url_failures": failures}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if missing or duplicates or wrong_titles or failures or len(targets) != len(expected):
        raise SystemExit("Final public verification failed; retain all existing navigation and pages.")
    if len(live) != 104:
        raise SystemExit(f"Expected 104 public category posts after these batches, found {len(live)}")
    print("Verified all 104 unique category posts are public; requested batch URLs return complete market functionality.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
