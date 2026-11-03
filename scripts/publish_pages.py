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

    bodies = {
        slug: (CONTENT_DIR / filename).read_text(encoding='utf-8')
        for filename, slug in PAGES.items()
    }
    if any(not body.strip() for body in bodies.values()):
        print('Refusing to publish an empty page body', file=sys.stderr)
        return 2

    if args.dry_run:
        print('Local preflight only; no Blogger API calls or remote content comparison.')
        for slug, body in bodies.items():
            print(f'preflight {slug:38s} {len(body):7d} bytes')
        return 0

    get_credentials()
    service = get_blogger_service()
    blog = get_blog_by_url(service, site['blog_url'])
    if str(blog['id']) != str(site['expected_blog_id']):
        print('Refusing to publish: resolved Blogger blog ID does not match config/site.json', file=sys.stderr)
        return 2
    pages = service.pages().list(blogId=blog['id'], fetchBodies=False).execute().get('items', [])

    # Resolve and validate every destination before the first write. A mismatch
    # aborts the whole run instead of silently leaving a partial publication.
    targets = {}
    errors = []
    for slug in bodies:
        matches = [p for p in pages if p.get('url', '').rstrip('/').endswith(f'/p/{slug}.html')]
        if len(matches) != 1:
            errors.append(f'{slug}: expected exactly one page, found {len(matches)}')
        else:
            targets[slug] = matches[0]
    if errors:
        print('Refusing to publish; destination preflight failed:', file=sys.stderr)
        for error in errors:
            print(f' - {error}', file=sys.stderr)
        return 2

    for slug, body in bodies.items():
        page = targets[slug]
        service.pages().patch(blogId=blog['id'], pageId=page['id'], body={'content': body}).execute()
        print(f'updated  {slug:38s} pageId={page["id"]}  {len(body):7d} bytes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
