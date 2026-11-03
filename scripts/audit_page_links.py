#!/usr/bin/env python3
"""Read-only audit of every /p/ button/link across the MILLED EDGE website.

Sources scanned:
  * live homepage HTML (server-rendered theme: nav, tabs, footer, FABs, FAQ)
  * every live Blogger page body (Blogger API, ADMIN view, fetchBodies)
  * every live Blogger post body
  * the repo theme file theme/MILLED_EDGE_Blogger_Theme_v7.xml (NOT installed)
  * the five published page files in publish/*.html

No Blogger write operation is performed.
"""
from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from blogger_client import get_blog_by_url, get_blogger_service, load_site_config

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATHS = [
    ROOT / "reports" / "page-links-audit.json",
    ROOT / "artifacts" / "page-links-audit.json",
]
BLOG_URL = "https://millededgeindia.blogspot.com/"
EXPECTED_BLOG_ID = "8911514070006792465"

NEW = {
    "/p/about-milled-edge.html": "About us",
    "/p/contact-milled-edge.html": "Contact us",
    "/p/privacy-policy-milled-edge.html": "Privacy Policy",
    "/p/financial-disclaimer-milled-edge.html": "Financial Disclaimer",
    "/p/terms-milled-edge.html": "Terms & Conditions",
}
LEGACY = {
    "/p/about-us_02080501126.html": ("2716668129166401912", "About us"),
    "/p/contact-us_01883938366.html": ("4698688245681185879", "Contact us"),
    "/p/privacy-policy.html": ("304220949515133754", "Privacy policy"),
    "/p/disclaimer.html": ("3945823007631424733", "Disclaimer"),
    "/p/terms-and-conditions.html": ("3254393081257151974", "Terms and conditions"),
}

ANCHOR_RE = re.compile(
    r"<a\b[^>]*?href\s*=\s*([\"'])(.*?)\1[^>]*>(.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
PATH_RE = re.compile(r"/p/[A-Za-z0-9_.-]+\.html", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(raw: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", raw))).strip()[:120]


def norm_path(href: str) -> str:
    href = html.unescape(href.strip())
    parsed = urlparse(href)
    path = parsed.path if parsed.scheme else href.split("?", 1)[0].split("#", 1)[0]
    if not path.startswith("/"):
        path = "/" + path
    return path


def scan(markup: str, source: str, source_type: str, out: list) -> int:
    found = 0
    for match in ANCHOR_RE.finditer(markup):
        href, label = match.group(2), clean_text(match.group(3))
        for path in PATH_RE.findall(html.unescape(href)):
            out.append(
                {
                    "source": source,
                    "source_type": source_type,
                    "button_text": label,
                    "href": html.unescape(href)[:220],
                    "path": path,
                }
            )
            found += 1
    return found


def all_path_mentions(markup: str, source: str, source_type: str, out: list) -> None:
    """Non-anchor references (JSON-LD, search index, JS data, canonical, etc.)."""
    anchor_spans = [(m.start(), m.end()) for m in ANCHOR_RE.finditer(markup)]
    for match in PATH_RE.finditer(html.unescape(markup)):
        if any(a <= match.start() < b for a, b in anchor_spans):
            continue
        out.append(
            {
                "source": source,
                "source_type": source_type,
                "button_text": "(non-button reference)",
                "href": match.group(0),
                "path": match.group(0),
            }
        )


def fetch(url: str):
    request = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; MILLED-EDGE-link-audit/1.0)"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read(6_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(2_000_000).decode("utf-8", "replace")
    except Exception as exc:
        return 0, f"request error: {exc}"


def list_all(service, collection: str, blog_id: str) -> list[dict]:
    out: list[dict] = []
    method = getattr(service, collection)()
    request = method.list(
        blogId=blog_id, maxResults=500, view="ADMIN", fetchBodies=True
    )
    while request is not None:
        response = request.execute()
        out.extend(response.get("items", []))
        request = method.list_next(request, response)
    return out


def main() -> int:
    report = {
        "mode": "page-links-audit",
        "generated_at_utc": now(),
        "blog": {},
        "sources": [],
        "live_pages": [],
        "live_posts_count": 0,
        "links": [],
        "new_page_coverage": {},
        "legacy_still_linked": {},
        "url_status_checks": [],
        "other_page_links": {},
        "errors": [],
        "result": "running",
    }
    try:
        config = load_site_config()
        service = get_blogger_service()
        blog = get_blog_by_url(service, config["blog_url"])
        blog_id = str(blog["id"])
        report["blog"] = {"id": blog_id, "url": blog.get("url"), "name": blog.get("name")}

        pages = list_all(service, "pages", blog_id)
        posts = list_all(service, "posts", blog_id)
        report["live_posts_count"] = len(posts)
        live_paths = set()
        for page in pages:
            path = urlparse(page.get("url", "")).path
            live_paths.add(path)
            report["live_pages"].append(
                {
                    "id": str(page.get("id")),
                    "title": page.get("title"),
                    "url": page.get("url"),
                    "status": page.get("status"),
                    "content_bytes": len(page.get("content") or ""),
                }
            )
            body = page.get("content") or ""
            n = scan(body, f"page: {page.get('title')} ({page.get('url')})", "live_page", report["links"])
            all_path_mentions(body, f"page: {page.get('title')}", "live_page", report["links"])
            report["sources"].append({"name": f"page: {page.get('title')}", "type": "live_page", "anchors": n})

        for post in posts:
            body = post.get("content") or ""
            n = scan(body, f"post: {post.get('title')}", "live_post", report["links"])
            report["sources"].append({"name": f"post: {post.get('title')}", "type": "live_post", "anchors": n})

        # Live server-rendered theme: homepage HTML.
        status, homepage = fetch(BLOG_URL)
        n = scan(homepage, "live homepage (theme nav/tabs/footer/FAB/FAQ)", "live_theme", report["links"])
        all_path_mentions(homepage, "live homepage", "live_theme", report["links"])
        report["sources"].append(
            {"name": "live homepage (theme)", "type": "live_theme", "http_status": status, "anchors": n}
        )

        # Repo theme file (explicitly NOT installed on Blogger).
        theme_path = ROOT / "theme" / "MILLED_EDGE_Blogger_Theme_v7.xml"
        if theme_path.exists():
            theme = theme_path.read_text(encoding="utf-8")
            n = scan(theme, "repo theme XML (not installed)", "repo_theme_file", report["links"])
            all_path_mentions(theme, "repo theme XML (not installed)", "repo_theme_file", report["links"])
            report["sources"].append(
                {"name": "repo theme XML (not installed)", "type": "repo_theme_file", "anchors": n}
            )

        for path, label in NEW.items():
            f = ROOT / "publish" / {
                "/p/about-milled-edge.html": "about_us.html",
                "/p/contact-milled-edge.html": "contact_us.html",
                "/p/privacy-policy-milled-edge.html": "privacy_policy.html",
                "/p/financial-disclaimer-milled-edge.html": "financial_disclaimer.html",
                "/p/terms-milled-edge.html": "terms_conditions.html",
            }[path]
            body = f.read_text(encoding="utf-8")
            n = scan(body, f"published page file: {f.name}", "published_page_file", report["links"])
            all_path_mentions(body, f"published page file: {f.name}", "published_page_file", report["links"])
            report["sources"].append(
                {"name": f"published page file: {f.name}", "type": "published_page_file", "anchors": n}
            )

        # Coverage per approved page.
        for path, label in NEW.items():
            hits = [x for x in report["links"] if x["path"] == path]
            real_buttons = [x for x in hits if x["button_text"] != "(non-button reference)"]
            by_type: dict[str, int] = {}
            for x in real_buttons:
                by_type[x["source_type"]] = by_type.get(x["source_type"], 0) + 1
            report["new_page_coverage"][path] = {
                "label": label,
                "url": urljoin(BLOG_URL, path.lstrip("/")),
                "total_button_links": len(real_buttons),
                "total_references": len(hits),
                "by_source_type": by_type,
                "buttons": [
                    {"source": x["source"], "text": x["button_text"]} for x in real_buttons
                ][:80],
                "linked_from_live_theme": any(
                    x["source_type"] == "live_theme" for x in real_buttons
                ),
                "linked_from_other_live_pages": any(
                    x["source_type"] == "live_page" and path not in x["source"]
                    for x in real_buttons
                ),
            }

        for path, (page_id, title) in LEGACY.items():
            hits = [x for x in report["links"] if x["path"] == path]
            real_buttons = [x for x in hits if x["button_text"] != "(non-button reference)"]
            report["legacy_still_linked"][path] = {
                "id": page_id,
                "title": title,
                "total_button_links": len(real_buttons),
                "buttons": [
                    {"source": x["source"], "text": x["button_text"]} for x in real_buttons
                ][:80],
            }

        # Every other /p/ path referenced, grouped.
        for x in report["links"]:
            p = x["path"]
            if p not in NEW and p not in LEGACY:
                report["other_page_links"].setdefault(p, 0)
                if x["button_text"] != "(non-button reference)":
                    report["other_page_links"][p] += 1

        # HTTP status of every referenced path (from the runner, real network).
        seen = []
        for p in list(NEW) + list(LEGACY) + sorted(report["other_page_links"]):
            if p in seen:
                continue
            seen.append(p)
            url = urljoin(BLOG_URL, p.lstrip("/"))
            code, body = fetch(url)
            report["url_status_checks"].append(
                {
                    "path": p,
                    "status_code": code,
                    "category": "new" if p in NEW else "legacy" if p in LEGACY else "other",
                    "exists_on_blog": p in live_paths,
                }
            )

        report["summary"] = {
            "live_pages_total": len(pages),
            "live_posts_total": len(posts),
            "distinct_paths_linked": len({x["path"] for x in report["links"]}),
            "total_button_links": len(
                [x for x in report["links"] if x["button_text"] != "(non-button reference)"]
            ),
            "new_pages_with_zero_buttons": [
                p for p, v in report["new_page_coverage"].items()
                if v["total_button_links"] == 0
            ],
            "legacy_paths_still_linked": [
                p for p, v in report["legacy_still_linked"].items()
                if v["total_button_links"] > 0
            ],
            "broken_links": [
                c["path"] for c in report["url_status_checks"] if c["status_code"] != 200
            ],
        }
        report["result"] = "success"
    except Exception as exc:
        report["result"] = "failed"
        report["errors"].append(f"{type(exc).__name__}: {exc}")

    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    for path in REPORT_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(f"Audit report saved: {REPORT_PATHS[0]}", flush=True)
    print(json.dumps(report["summary"], indent=2), flush=True)
    print(json.dumps(report["new_page_coverage"], indent=2)[:6000], flush=True)
    print(json.dumps(report["legacy_still_linked"], indent=2)[:6000], flush=True)
    return 0 if report["result"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
