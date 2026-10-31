"""Create a read-only inventory of the configured Blogger blog.

This script only calls Blogger API read endpoints. It does not create, update,
publish, revert, or delete anything.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from blogger_client import get_blog_by_url, get_blogger_service, load_site_config


def list_all_pages(service, blog_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    request = service.pages().list(blogId=blog_id, maxResults=500)
    while request is not None:
        response = request.execute()
        for page in response.get("items", []):
            items.append(
                {
                    "id": page.get("id"),
                    "title": page.get("title"),
                    "url": page.get("url"),
                    "status": page.get("status"),
                    "published": page.get("published"),
                    "updated": page.get("updated"),
                }
            )
        request = service.pages().list_next(request, response)
    return items


def list_all_posts(service, blog_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    request = service.posts().list(blogId=blog_id, maxResults=500, fetchBodies=False)
    while request is not None:
        response = request.execute()
        for post in response.get("items", []):
            items.append(
                {
                    "id": post.get("id"),
                    "title": post.get("title"),
                    "url": post.get("url"),
                    "status": post.get("status"),
                    "published": post.get("published"),
                    "updated": post.get("updated"),
                    "labels": post.get("labels", []),
                }
            )
        request = service.posts().list_next(request, response)
    return items


def main() -> None:
    config = load_site_config()
    service = get_blogger_service()
    blog = get_blog_by_url(service, config["blog_url"])
    blog_id = blog["id"]

    pages = list_all_pages(service, blog_id)
    posts = list_all_posts(service, blog_id)

    inventory = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "read-only",
        "blog": {
            "id": blog.get("id"),
            "name": blog.get("name"),
            "url": blog.get("url"),
            "description": blog.get("description"),
        },
        "counts": {
            "pages": len(pages),
            "posts": len(posts),
        },
        "pages": pages,
        "posts": posts,
    }

    output_dir = Path(__file__).resolve().parent.parent / "artifacts"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "readonly-inventory.json"
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(inventory, handle, indent=2, ensure_ascii=False)

    print("Read-only inventory completed.")
    print(f"Blog: {blog.get('name')} ({blog_id})")
    print(f"Pages: {len(pages)}")
    print(f"Posts: {len(posts)}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
