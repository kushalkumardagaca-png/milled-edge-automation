"""Strip the page-level site shell that duplicates the Blogger theme.

Every one of the five pages carries its own <a class=skip>, <header> (brand +
nav) and <footer> (a second site footer). The theme already renders exactly
those three things, which is why readers see the same identity, the same
navigation and the same footer twice. Only the <main> block belongs to a page.
"""
import re, sys
from bs4 import BeautifulSoup

PAGES = ["about-milled-edge", "contact-milled-edge", "privacy-policy-milled-edge",
         "financial-disclaimer-milled-edge", "terms-milled-edge"]

SHELL = ("a.skip", "a.me-skip", "header.site-header", "header.me-site-header",
         "header.shell", "footer.site-footer", "footer.me-site-footer", "footer.shell")


def post_body(t):
    i = t.find("<div class='post-body entry-content'>")
    if i < 0:
        raise SystemExit("no post body")
    depth = 0
    for m in re.finditer(r"<(/?)(div)([^>]*)>", t[i:], re.I):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return t[i:i + m.end()]
    raise SystemExit("unterminated post body")


def clean(slug):
    src = open(f"/home/user/live/{slug}.html", encoding="utf-8").read()
    soup = BeautifulSoup(post_body(src), "html.parser")
    root = soup.find("div", class_="post-body")
    removed = []
    for sel in SHELL:
        for el in root.select(sel):
            removed.append(sel)
            el.decompose()
    # an empty wrapper is left behind by the shell on four of the five pages
    for el in list(root.find_all("div", recursive=False)):
        if not el.get_text(strip=True) and not el.find(["img", "svg", "iframe"]):
            el.decompose()
    return str(root), removed


if __name__ == "__main__":
    for slug in PAGES:
        html, removed = clean(slug)
        open(f"/home/user/build/pages/{slug}.html", "w", encoding="utf-8").write(html)
        txt = re.sub(r"\s+", " ", BeautifulSoup(html, "html.parser").get_text(" ", strip=True))
        print(f"{slug:32s} {len(html):7d} bytes  shell removed: {sorted(set(removed))}")
        print(f"{'':34s}first words: {txt[:90]}")
