"""Install the five rebuilt page bodies over the existing Blogger pages.

The bodies are already the finished article: the theme supplies the header, the
navigation and the footer, so nothing in these files repeats them.

Matching is by the page's own address slug, never by title, so no duplicate page is
created and no existing page is renamed. Only `content` is patched; titles, slugs and
settings stay exactly as they are.

    python scripts/publish_pages.py --dry-run
    python scripts/publish_pages.py --confirm PUBLISH
"""
from __future__ import annotations

import argparse
import pathlib
import sys

from blogger_client import get_blogger_service, get_blog_by_url, get_credentials, load_site_config

CONTENT_DIR = pathlib.Path(__file__).resolve().parent.parent / 'content' / 'pages'

PAGES = {
    'about-milled-edge.html': 'about-milled-edge',
    'contact-milled-edge.html': 'contact-milled-edge',
    'privacy-policy-milled-edge.html': 'privacy-policy-milled-edge',
    'financial-disclaimer-milled-edge.html': 'financial-disclaimer-milled-edge',
    'terms-milled-edge.html': 'terms-milled-edge',
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--confirm', default='')
    args = ap.parse_args()

    site = load_site_config()
    if not args.dry_run and args.confirm != 'PUBLISH':
        print('Refusing to write without --confirm PUBLISH', file=sys.stderr)
        return 2

    missing = [name for name in PAGES if not (CONTENT_DIR / name).exists()]
    if missing:
        print('Missing page bodies: ' + ', '.join(missing), file=sys.stderr)
        return 2

    if args.dry_run:
        service = None
        blog = {'id': site['expected_blog_id']}
        pages = None
    else:
        get_credentials()
        service = get_blogger_service()
        blog = get_blog_by_url(service, site['blog_url'])
        pages = service.pages().list(blogId=blog['id'], fetchBodies=False).execute().get('items', [])

    for filename, slug in PAGES.items():
        body = (CONTENT_DIR / filename).read_text(encoding='utf-8')
        if args.dry_run:
            print(f'dry run  {slug:38s} {len(body):7d} bytes')
            continue
        match = [p for p in pages if p['url'].rstrip('/').endswith(f'/p/{slug}.html')]
        if len(match) != 1:
            print(f'no single page matches {slug} ({len(match)} found) — skipped', file=sys.stderr)
            continue
        page = match[0]
        service.pages().patch(blogId=blog['id'], pageId=page['id'], body={'content': body}).execute()
        print(f'updated  {slug:38s} pageId={page["id"]}  {len(body):7d} bytes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
