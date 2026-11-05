"""Move only the verified project category posts to Blogger Trash (reversible)."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = json.loads((ROOT / "config/site.json").read_text(encoding="utf-8"))
EXPECTED_BLOG_ID = str(SITE["expected_blog_id"])
EXPECTED_COUNT = 100


def all_posts(service, blog_id: str) -> list[dict]:
    items, token = [], None
    while True:
        args = {"blogId": blog_id, "fetchBodies": False, "maxResults": 500}
        if token:
            args["pageToken"] = token
        result = service.posts().list(**args).execute(num_retries=2)
        items.extend(result.get("items", []))
        token = result.get("nextPageToken")
        if not token:
            return items


def is_project_post(post: dict) -> bool:
    labels = set(post.get("labels", []))
    return "MarketCategoryPost" in labels and any(x.startswith("CategoryID-") for x in labels)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="list candidates without writing")
    parser.add_argument("--confirm", help="must be exactly TRASH 100 PROJECT POSTS")
    args = parser.parse_args()
    if not args.dry_run and args.confirm != "TRASH 100 PROJECT POSTS":
        parser.error("A live run requires --confirm 'TRASH 100 PROJECT POSTS'")

    sys.path.insert(0, str(ROOT / "scripts"))
    from blogger_client import get_blogger_service

    service = get_blogger_service()
    blog_id = EXPECTED_BLOG_ID
    blog = service.blogs().get(blogId=blog_id).execute(num_retries=2)
    if str(blog.get("id")) != EXPECTED_BLOG_ID:
        raise SystemExit("Configured blog ID mismatch; no writes made.")

    posts = all_posts(service, blog_id)
    targets = [p for p in posts if is_project_post(p)]
    if len(targets) != EXPECTED_COUNT:
        raise SystemExit(f"Expected exactly {EXPECTED_COUNT} project posts, found {len(targets)}; no writes made.")
    if any(not p.get("id") for p in targets):
        raise SystemExit("A target is missing its Blogger ID; no writes made.")
    print(f"Verified {len(targets)} targets on {blog.get('name')} ({blog_id}); no Pages or unrelated posts selected.")
    for p in targets:
        print(f"{p['id']}\t{p.get('title', '(untitled)')}\t{p.get('url', '')}")
    if args.dry_run:
        return 0

    moved = 0
    for post in targets:
        try:
            service.posts().trash(blogId=blog_id, postId=post["id"]).execute(num_retries=0)
        except Exception as exc:
            print(f"STOP after {moved}/{len(targets)}; Blogger write failed for {post['id']}: {exc}", file=sys.stderr)
            return 2
        moved += 1
        if moved < len(targets):
            time.sleep(2)
    remaining = [p for p in all_posts(service, blog_id) if is_project_post(p)]
    if remaining:
        print(f"Moved {moved}; verification found {len(remaining)} project posts still live.", file=sys.stderr)
        return 3
    print(f"Moved {moved} project posts to Blogger Trash and verified none remain live.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
