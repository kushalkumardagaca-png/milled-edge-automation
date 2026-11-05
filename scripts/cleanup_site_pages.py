"""Patch existing pages in place to remove retired routes and dangling fragments."""
from pathlib import Path
from blogger_client import get_blogger_service, get_blog_by_url, load_site_config

ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    'calculator_0908148622': ROOT / 'content' / 'pages-fixes' / 'calculator_0908148622.html',
    'for-corporate_01804417406': ROOT / 'content' / 'pages-fixes' / 'for-corporate_01804417406.html',
    'money-atlas_01486068069': ROOT / 'content' / 'pages-fixes' / 'money-atlas_01486068069.html',
    'about-milled-edge': ROOT / 'content' / 'pages-fixes' / 'about-milled-edge.html',
    'contact-milled-edge': ROOT / 'content' / 'pages-fixes' / 'contact-milled-edge.html',
    'privacy-policy-milled-edge': ROOT / 'content' / 'pages-fixes' / 'privacy-policy-milled-edge.html',
    'financial-disclaimer-milled-edge': ROOT / 'content' / 'pages-fixes' / 'financial-disclaimer-milled-edge.html',
    'terms-milled-edge': ROOT / 'content' / 'pages-fixes' / 'terms-milled-edge.html',
}
FORBIDDEN = ('/p/daily-news.html', '/p/article.html', '/p/disclaimer.html', 'dailyyield.blogspot.com', 'millededge.blogspot.com', 'milledgeindia.blogspot.com', 'Daily News', 'Daily Article')


def main():
    bodies = {}
    for slug, path in PAGES.items():
        if not path.is_file():
            raise SystemExit(f'Missing page body: {path}')
        text = path.read_text(encoding='utf-8')
        for marker in FORBIDDEN:
            if marker.lower() in text.lower():
                raise SystemExit(f'Refusing to publish {slug}: old content remains: {marker}')
        if slug == 'markets-today' and '/p/financial-disclaimer-milled-edge.html' not in text:
            raise SystemExit('Financial disclaimer link missing from Markets Today')
        bodies[slug] = text

    site = load_site_config()
    service = get_blogger_service()
    blog = get_blog_by_url(service, site['blog_url'])
    existing = service.pages().list(blogId=blog['id'], fetchBodies=False, maxResults=50).execute().get('items', [])
    for slug, text in bodies.items():
        match = [p for p in existing if p.get('url', '').rstrip('/').endswith(f'/p/{slug}.html')]
        if len(match) != 1:
            raise SystemExit(f'Expected exactly one existing /p/{slug}.html page; found {len(match)}; stopped')
    for slug, text in bodies.items():
        page = next(p for p in existing if p.get('url', '').rstrip('/').endswith(f'/p/{slug}.html'))
        service.pages().patch(blogId=blog['id'], pageId=page['id'], body={'content': text}).execute()
        print(f'Updated existing /p/{slug}.html ({len(text)} characters).')


if __name__ == '__main__':
    main()
