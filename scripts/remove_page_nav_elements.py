"""Remove the in-page navigation furniture from the five document pages.

Two element families are removed, both of them "jump around this page" widgets:

1. ``<nav ... class="pr-local-nav">`` - the horizontal "On this page" button row
   (About page; also Money Atlas in pages-fixes).
2. ``<aside ... class="md-rail">``    - the sticky "Contents" sidebar rail
   (Contact, Privacy Policy, Terms, Financial Disclaimer).

Targets are located with a real HTML tokenizer, never with a regex spanning the
whole document: one page is ~488 KB and a quadratically backtracking regex over
it does not finish. Everything outside the matched element is preserved byte for
byte.

The page scripts already guard for the removed nodes (``if(bar)`` and
``for(var k=0;k<links.length;k++)``), so nothing throws once the rail is gone.

    python scripts/remove_page_nav_elements.py --dry-run
    python scripts/remove_page_nav_elements.py --confirm REMOVE-NAV --publish
"""
from __future__ import annotations

import argparse
import html as html_lib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES_DIR = ROOT / "content" / "pages"

SOURCES = [
    PAGES_DIR / "about-milled-edge.html",
    PAGES_DIR / "contact-milled-edge.html",
    PAGES_DIR / "privacy-policy-milled-edge.html",
    PAGES_DIR / "terms-milled-edge.html",
    PAGES_DIR / "financial-disclaimer-milled-edge.html",
]

TARGETS = (("nav", "pr-local-nav"), ("aside", "md-rail"))

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9:-]*)((?:[^>\"']|\"[^\"]*\"|'[^']*')*)>")

LAYOUT_FIX = (
    "\n/* no-nav layout fix: the Contents rail is gone, so the article owns the "
    "full row */\n.me-doc .md-grid{grid-template-columns:minmax(0,1fr)!important}\n"
)


def _has_class(attrs: str, cls: str) -> bool:
    m = re.search(r"\bclass\s*=\s*(\"([^\"]*)\"|'([^']*)')", attrs)
    if not m:
        return False
    value = m.group(2) if m.group(2) is not None else m.group(3)
    return cls in value.split()


def find_blocks(html: str) -> list[tuple[int, int, str]]:
    """Return (start, end, matched_class) for every target element, outermost only."""
    blocks: list[tuple[int, int, str]] = []
    stack: list[tuple[str, int, str | None]] = []
    for m in TAG_RE.finditer(html):
        closing, tag, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if tag in VOID or attrs.rstrip().endswith("/"):
            continue
        if not closing:
            matched = None
            for target_tag, target_cls in TARGETS:
                if tag == target_tag and _has_class(attrs, target_cls):
                    matched = target_cls
                    break
            stack.append((tag, m.start(), matched))
        else:
            for depth in range(len(stack) - 1, -1, -1):
                if stack[depth][0] == tag:
                    _, start, matched = stack[depth]
                    del stack[depth:]
                    if matched:
                        blocks.append((start, m.end(), matched))
                    break
    blocks.sort()
    kept: list[tuple[int, int, str]] = []
    for start, end, label in blocks:
        if kept and start < kept[-1][1]:
            continue
        kept.append((start, end, label))
    return kept


def strip(html: str) -> tuple[str, list[str], list[str]]:
    """Return (edited_html, removed_labels, removed_source_snippets)."""
    blocks = find_blocks(html)
    snippets = [html[start:end] for start, end, _ in blocks]
    for start, end, _ in reversed(blocks):
        html = html[:start] + html[end:]
    return html, [label for _, _, label in blocks], snippets


def add_layout_fix(html: str) -> tuple[str, bool]:
    """The four document pages size .md-grid as 230px + article. With the rail
    gone the article would be squeezed into the 230px track, so the grid is reset
    to a single full-width column. Injected once, only where a rail was removed."""
    if "meNoNavLayoutFix" in html:
        return html, False
    marker = '<style id="meDocStyle">'
    i = html.find(marker)
    if i < 0:
        return html, False
    j = html.find("</style>", i)
    if j < 0:
        return html, False
    close = "</style>"
    fix = f'<style id="meNoNavLayoutFix">{LAYOUT_FIX}</style>'
    return html[: j + len(close)] + fix + html[j + len(close):], True


def validate(before: str, after: str, snippets: list[str], name: str) -> list[str]:
    problems: list[str] = []
    if find_blocks(after):
        problems.append(f"{name}: a target element survived the edit")
    removed_text = "".join(snippets)
    for needle, label in (("<script", "script"), ("<section", "section"),
                          ("<h2", "heading"), ("<figure", "figure")):
        delta = before.count(needle) - after.count(needle)
        expected = removed_text.count(needle)
        if delta != expected:
            problems.append(f"{name}: {label} count fell by {delta}, expected {expected}")
    if len(after) > len(before):
        problems.append(f"{name}: file grew during a removal - refusing")
    for tag in ("div", "aside", "nav", "ul", "section", "article", "p", "span"):
        b = len(re.findall(rf"<{tag}\b", before)) - len(re.findall(rf"</{tag}>", before))
        a = len(re.findall(rf"<{tag}\b", after)) - len(re.findall(rf"</{tag}>", after))
        if a != 0:
            problems.append(f"{name}: <{tag}> balance is {a} after edit (was {b})")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--confirm", default="")
    ap.add_argument("--publish", action="store_true")
    args = ap.parse_args()

    if not args.dry_run and args.confirm != "REMOVE-NAV":
        print("Refusing to write without --confirm REMOVE-NAV", file=sys.stderr)
        return 2

    planned: list[tuple[pathlib.Path, str, str, int]] = []
    problems: list[str] = []
    for path in SOURCES:
        if not path.exists():
            problems.append(f"missing source {path.name}")
            continue
        before = path.read_text(encoding="utf-8")
        after, removed, snippets = strip(before)
        if "md-rail" in removed:
            after, fixed = add_layout_fix(after)
            if not fixed:
                problems.append(f"{path.name}: could not inject the layout fix")
        problems.extend(validate(before, after, snippets, path.name))
        planned.append((path, before, after, len(removed)))
        print(
            f"{path.name:42s} {len(before):7d} -> {len(after):7d} "
            f"(-{len(before)-len(after):5d})  removed={removed or 'none'}"
        )

    if problems:
        print("\nPreflight failed, nothing written:", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 2

    total = sum(n for _, _, _, n in planned)
    if args.dry_run:
        print(f"\nDry run complete. {total} block(s) would be removed. No files written.")
        return 0
    if total == 0:
        print("\nEvery page source is already clean.")

    for path, before, after, n in planned:
        if n:
            path.write_text(after, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")

    if not args.publish:
        print("\nFiles updated locally. Re-run with --publish to push to Blogger.")
        return 0

    from blogger_client import (get_blogger_service, get_blog_by_url,
                                get_credentials, load_site_config)

    site = load_site_config()
    get_credentials()
    service = get_blogger_service()
    blog = get_blog_by_url(service, site["blog_url"])
    if str(blog["id"]) != str(site["expected_blog_id"]):
        print("Refusing to publish: resolved blog ID does not match config/site.json", file=sys.stderr)
        return 2

    pages = service.pages().list(blogId=blog["id"], fetchBodies=False).execute().get("items", [])
    targets, errors = {}, []
    for path, _, _, _n in planned:
        matches = [p for p in pages
                   if p.get("url", "").rstrip("/").endswith(f"/p/{path.stem}.html")]
        if len(matches) != 1:
            errors.append(f"{path.stem}: expected exactly one page, found {len(matches)}")
        else:
            targets[path.stem] = matches[0]["id"]
    if errors:
        print("Destination preflight failed, nothing patched:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        return 2

    def norm(text: str) -> str:
        # Blogger may re-encode entities or collapse whitespace on the way in, so
        # comparison is done on a normalised form to avoid republishing for nothing.
        return re.sub(r"\s+", " ", html_lib.unescape(text or "")).strip()

    published = skipped = failed = 0
    for path, _, _after, _n in planned:
        slug, page_id = path.stem, targets[path.stem]
        local = path.read_text(encoding="utf-8")
        remote = service.pages().get(blogId=blog["id"], pageId=page_id).execute().get("content", "")
        if norm(local) == norm(remote):
            print(f"unchanged {slug:40s} pageId={page_id} - Blogger already serves this body")
            skipped += 1
            continue
        try:
            service.pages().patch(
                blogId=blog["id"], pageId=page_id, body={"content": local}
            ).execute()
        except Exception as exc:  # noqa: BLE001 - report and continue with the rest
            print(f"FAILED    {slug:40s} pageId={page_id}: {type(exc).__name__}: {exc}", file=sys.stderr)
            failed += 1
            continue
        print(f"published {slug:40s} pageId={page_id} {len(local):7d} bytes "
              f"(blogger had {len(remote):7d})")
        published += 1

    print(f"\nSummary: {published} published, {skipped} already current, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
