"""Permanently delete ALL posts from the configured Blogger blog.

Destructive. Only runs when the trigger file contains the exact confirmation
phrase. Pages are never touched. No post bodies are saved; the report contains
only IDs, titles, URLs, and statuses of deleted posts (an audit log, not a
content backup).
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

from googleapiclient.errors import HttpError

from blogger_client import get_blog_by_url, get_blogger_service, load_site_config

ROOT = Path(__file__).resolve().parent.parent
CONFIRM_PHRASE = "CONFIRM: DELETE ALL POSTS PERMANENTLY"
TRIGGER_FILE = ROOT / "trigger" / "delete-all-posts.txt"
STATUSES = ["LIVE", "DRAFT", "SCHEDULED", "SOFT_TRASHED"]
RETRYABLE = {429, 500, 502, 503, 504}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_with_retry(request, what: str, attempts: int = 6):
    for attempt in range(1, attempts + 1):
        try:
            return request.execute(num_retries=2)
        except HttpError as error:
            status = getattr(error.resp, "status", None)
            if status in RETRYABLE and attempt < attempts:
                delay = min(60.0, 2.0 ** attempt) + random.uniform(0, 1)
                print(f"Retry {attempt}/{attempts - 1} for {what} after HTTP {status}; sleeping {delay:.1f}s", flush=True)
                time.sleep(delay)
                continue
            raise


def collect_posts(service, blog_id: str, status: str) -> list[dict]:
    items: list[dict] = []
    request = service.posts().list(
        blogId=blog_id,
        status=status,
        maxResults=500,
        fetchBodies=False,
        orderBy="UPDATED",
    )
    while request is not None:
        response = execute_with_retry(request, f"posts.list status={status}")
        items.extend(response.get("items", []))
        request = service.posts().list_next(request, response)
    return items


def snapshot(post: dict) -> dict:
    return {
        "id": post.get("id"),
        "title": post.get("title"),
        "url": post.get("url"),
        "status": post.get("status"),
    }


def delete_post(service, blog_id: str, post_id: str, use_trash: bool) -> None:
    request = service.posts().delete(blogId=blog_id, postId=post_id, useTrash=use_trash)
    execute_with_retry(request, f"posts.delete {post_id} useTrash={use_trash}")


def save_report(report: dict) -> None:
    output_dir = ROOT / "artifacts"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "delete-all-posts-report.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(f"Report saved: {path}", flush=True)


def main() -> None:
    config = load_site_config()
    expected_blog_id = str(config.get("expected_blog_id", "")).strip()

    phrase_present = TRIGGER_FILE.exists() and any(
        line.strip() == CONFIRM_PHRASE for line in TRIGGER_FILE.read_text(encoding="utf-8").splitlines()
    )
    if not phrase_present:
        raise SystemExit("Refusing to run: trigger file does not contain the exact confirmation phrase.")

    service = get_blogger_service()
    blog = get_blog_by_url(service, config["blog_url"])
    blog_id = str(blog["id"])
    if expected_blog_id and blog_id != expected_blog_id:
        raise SystemExit(f"Blog ID mismatch: expected {expected_blog_id}, got {blog_id}. Aborting.")

    report = {
        "mode": "delete-all-posts",
        "started_at_utc": now(),
        "blog": {"id": blog_id, "name": blog.get("name"), "url": blog.get("url")},
        "found_by_status": {},
        "deleted": [],
        "failed": [],
        "remaining_after": None,
        "finished_at_utc": None,
    }

    seen: dict[str, dict] = {}
    for status in STATUSES:
        posts = collect_posts(service, blog_id, status)
        report["found_by_status"][status] = len(posts)
        print(f"Found {len(posts)} posts with status {status}", flush=True)
        for post in posts:
            post_id = str(post.get("id"))
            if post_id and post_id not in seen:
                seen[post_id] = post

    print(f"Total unique posts to delete: {len(seen)}", flush=True)
    if not seen:
        report["remaining_after"] = 0
        report["finished_at_utc"] = now()
        save_report(report)
        print("Nothing to delete.", flush=True)
        return

    for index, (post_id, post) in enumerate(seen.items(), start=1):
        status = (post.get("status") or "").upper()
        use_trash = status in {"LIVE", "SCHEDULED"}
        try:
            delete_post(service, blog_id, post_id, use_trash=use_trash)
            report["deleted"].append({**snapshot(post), "action": "trashed" if use_trash else "deleted"})
        except HttpError as error:
            code = getattr(error.resp, "status", None)
            if code == 404:
                report["deleted"].append({**snapshot(post), "action": "already-gone"})
            else:
                report["failed"].append({**snapshot(post), "error": f"HTTP {code}"})
                print(f"FAILED {post_id}: HTTP {code}", flush=True)
        if index % 25 == 0:
            print(f"Progress: {index}/{len(seen)} processed", flush=True)
        time.sleep(0.35)

    # Second sweep: permanently remove anything left, including posts just
    # moved to trash and anything created while this run was in progress.
    for sweep in range(1, 6):
        leftovers: dict[str, dict] = {}
        for status in STATUSES:
            for post in collect_posts(service, blog_id, status):
                post_id = str(post.get("id"))
                if post_id:
                    leftovers[post_id] = post
        if not leftovers:
            break
        print(f"Sweep {sweep}: permanently deleting {len(leftovers)} remaining posts", flush=True)
        for post_id, post in leftovers.items():
            try:
                delete_post(service, blog_id, post_id, use_trash=False)
                report["deleted"].append({**snapshot(post), "action": "deleted"})
            except HttpError as error:
                code = getattr(error.resp, "status", None)
                if code == 404:
                    report["deleted"].append({**snapshot(post), "action": "already-gone"})
                else:
                    report["failed"].append({**snapshot(post), "error": f"HTTP {code} (sweep {sweep})"})
            time.sleep(0.35)

    remaining = 0
    for status in STATUSES:
        remaining += len(collect_posts(service, blog_id, status))
    report["remaining_after"] = remaining
    report["finished_at_utc"] = now()
    save_report(report)

    print(f"Deleted entries: {len(report['deleted'])}", flush=True)
    print(f"Failed entries: {len(report['failed'])}", flush=True)
    print(f"Remaining posts: {remaining}", flush=True)
    if report["failed"] or remaining:
        raise SystemExit("Deletion incomplete: see report.")


if __name__ == "__main__":
    main()
