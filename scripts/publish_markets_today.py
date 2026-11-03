"""Patch the existing Markets Today Blogger page, without creating a new page."""
from pathlib import Path
from blogger_client import get_blogger_service, get_blog_by_url, load_site_config

SLUG = 'markets-today'
BODY = Path(__file__).resolve().parent.parent / 'content' / 'markets-today.html'


def main():
    if not BODY.is_file():
        raise SystemExit(f'Missing body file: {BODY}')
    content = BODY.read_text(encoding='utf-8')
    for forbidden in ('/p/daily-news.html', '/p/article.html', '/p/disclaimer.html', 'dailyyield.blogspot.com'):
        if forbidden in content.lower():
            raise SystemExit(f'Refusing to publish: old route remains: {forbidden}')
    if '/p/financial-disclaimer-milled-edge.html' not in content:
        raise SystemExit('Refusing to publish: financial disclaimer link is missing')

    site = load_site_config()
    service = get_blogger_service()
    blog = get_blog_by_url(service, site['blog_url'])
    pages = service.pages().list(blogId=blog['id'], fetchBodies=False, maxResults=50).execute().get('items', [])
    matches = [p for p in pages if p.get('url', '').rstrip('/').endswith(f'/p/{SLUG}.html')]
    if len(matches) != 1:
        raise SystemExit(f'Expected one existing /p/{SLUG}.html page; found {len(matches)}; no write made')
    page = matches[0]
    service.pages().patch(blogId=blog['id'], pageId=page['id'], body={'content': content}).execute()
    print(f'Updated existing /p/{SLUG}.html ({len(content)} characters); no page was created.')


if __name__ == '__main__':
    main()
