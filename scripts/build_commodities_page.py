"""Build a standalone Blogger Page body for physical-commodity benchmarks.

This writes only content/pages/commodities.html; it never builds or changes a theme.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "content" / "commodity-price-board.json"
OUT = ROOT / "content" / "pages" / "commodities.html"


def build() -> str:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    entries = []
    for item in data["items"]:
        name = html.escape(item["name"])
        basis = html.escape(item["basis"])
        unit = html.escape(item["unit"])
        value = f'{item["value"]:,.2f}'.rstrip("0").rstrip(".")
        status = " · estimate" if item.get("status") == "estimated" else ""
        haystack = html.escape((item["name"] + " " + item["basis"] + " " + item["unit"]).casefold(), quote=True)
        entries.append(
            f'<article class="me-c-item" data-search="{haystack}">'
            f'<div class="me-c-top"><h2>{name}</h2><span class="me-c-period">{html.escape(data["price_month"])}</span></div>'
            f'<p class="me-c-price">{html.escape(value)} <small>{unit}</small></p>'
            f'<p class="me-c-basis">{basis}{status}</p>'
            '</article>'
        )
    title = html.escape(data["title"])
    source = html.escape(data["source_name"])
    source_url = html.escape(data["source_url"], quote=True)
    monthly_url = html.escape(data["monthly_file_url"], quote=True)
    release = html.escape(data["release_date"])
    price_month = html.escape(data["price_month"])
    note = html.escape(data["note"])
    return f'''<section class="me-commodity-page" aria-labelledby="me-c-title">
<style>
.me-commodity-page{{--c-ink:#241610;--c-muted:#706253;--c-line:#e7dbc9;--c-paper:#fffdf8;--c-copper:#a64e2b;max-width:1180px;margin:0 auto;padding:clamp(16px,3vw,34px);color:var(--c-ink);font-family:Arial,Helvetica,sans-serif;line-height:1.55}}
.me-commodity-page *{{box-sizing:border-box}}
.me-c-hero{{padding:clamp(22px,4vw,42px);border:1px solid var(--c-line);border-radius:18px;background:linear-gradient(135deg,#fffdf8,#f7ead6);box-shadow:0 16px 38px -30px #5c3b22}}
.me-c-kicker{{margin:0 0 8px;color:var(--c-copper);font-size:11px;font-weight:800;letter-spacing:.16em;text-transform:uppercase}}
.me-c-hero h1{{margin:0;font:800 clamp(32px,5vw,54px)/1.08 Georgia,serif;letter-spacing:-.03em}}
.me-c-lead{{max-width:850px;margin:14px 0 0;color:var(--c-muted);font-size:15px}}
.me-c-stamp{{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}}
.me-c-stamp span{{padding:7px 10px;border:1px solid var(--c-line);border-radius:999px;background:#fffdf8;font-size:11px;font-weight:700}}
.me-c-toolbar{{display:flex;gap:9px;align-items:center;margin:20px 0 8px}}
.me-c-toolbar input{{flex:1;min-width:0;padding:13px 14px;border:1px solid #cdb89d;border-radius:10px;background:#fffdf8;font-size:15px;color:var(--c-ink)}}
.me-c-toolbar button{{padding:12px 15px;border:0;border-radius:10px;background:var(--c-copper);color:white;font-weight:800;cursor:pointer}}
.me-c-status{{min-height:22px;margin:0 0 10px;color:var(--c-muted);font-size:12px}}
.me-c-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:11px}}
.me-c-item{{min-width:0;padding:15px;border:1px solid var(--c-line);border-radius:13px;background:var(--c-paper);box-shadow:0 7px 18px -18px #241610}}\n.me-c-item[hidden]{{display:none!important}}
.me-c-top{{display:flex;align-items:flex-start;justify-content:space-between;gap:9px}}
.me-c-item h2{{margin:0;font:700 16px/1.25 Georgia,serif}}
.me-c-period{{flex:none;padding:4px 7px;border-radius:999px;background:#f6eddf;color:var(--c-muted);font-size:9px;font-weight:700}}
.me-c-price{{margin:13px 0 5px;font:800 25px/1.1 Georgia,serif;font-variant-numeric:tabular-nums;color:var(--c-copper);overflow-wrap:anywhere}}
.me-c-price small{{font:700 11px/1.4 Arial,Helvetica,sans-serif;color:var(--c-muted)}}
.me-c-basis{{margin:0;color:var(--c-muted);font-size:11px;line-height:1.45}}
.me-c-empty{{grid-column:1/-1;padding:22px;text-align:center;border:1px dashed var(--c-line);border-radius:12px;color:var(--c-muted)}}
.me-c-method{{margin-top:20px;padding:16px 18px;border:1px solid var(--c-line);border-radius:14px;background:#faf5ec;color:var(--c-muted);font-size:12px}}
.me-c-method h2{{margin:0 0 7px;color:var(--c-ink);font:700 17px Georgia,serif}}
.me-c-method p{{margin:7px 0}}
.me-c-method a{{color:var(--c-copper);font-weight:700}}
@media(max-width:850px){{.me-c-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
@media(max-width:540px){{.me-commodity-page{{padding:12px}}.me-c-grid{{grid-template-columns:1fr}}.me-c-toolbar{{align-items:stretch;flex-direction:column}}.me-c-toolbar button{{width:100%}}.me-c-hero{{padding:22px 17px}}}}
</style>
<header class="me-c-hero">
<p class="me-c-kicker">MILLED EDGE · physical commodity prices</p>
<h1 id="me-c-title">{title}</h1>
<p class="me-c-lead">A single, flat board of {len(data['items'])} published commodity price benchmarks—including gold and silver. No commodity menus or subcategories, and no futures, ETFs, bonds, miners, CFDs, or other financial instruments.</p>
<div class="me-c-stamp"><span>Reference month: {price_month}</span><span>Source released: {release}</span><span>Monthly benchmarks · not live quotes</span></div>
</header>
<div class="me-c-toolbar" role="search"><input id="meCommoditySearch" type="search" autocomplete="off" placeholder="Search commodity names, grades, locations or basis…" aria-label="Search all commodity price benchmarks"><button id="meCommodityClear" type="button">Clear search</button></div>
<p class="me-c-status" id="meCommodityCount" role="status" aria-live="polite">Showing {len(data['items'])} commodity price series.</p>
<div class="me-c-grid" id="meCommodityItems">{''.join(entries)}</div>
<section class="me-c-method"><h2>Price basis and limitations</h2>
<p>{note} These are source-specific grade, location, import/export, auction, fixing, spot, or physical-settlement price series—not one universal price for every physical delivery. Gold and silver figures are international benchmarks, not Indian jewellery-shop or retail cash prices; purity, duties, taxes and local premiums are not included.</p>
<p>Source: <a href="{source_url}" target="_blank" rel="noopener">{source} — November 2026 sheet (PDF)</a> · <a href="{monthly_url}" target="_blank" rel="noopener">monthly source workbook</a>.</p>
<p>Only commodity price series with a reported October 2026 value and a non-futures physical-market basis are listed. Explicit futures/forward-month quotations, commodity indexes, ETFs, company shares, bonds and other financial instruments are omitted.</p></section>
<script>
(function(){{'use strict';var input=document.getElementById('meCommoditySearch'),clear=document.getElementById('meCommodityClear'),box=document.getElementById('meCommodityItems'),status=document.getElementById('meCommodityCount');if(!input||!clear||!box||!status)return;var items=Array.prototype.slice.call(box.querySelectorAll('.me-c-item'));function update(){{var q=(input.value||'').trim().toLowerCase(),shown=0;items.forEach(function(card){{var hit=!q||card.getAttribute('data-search').indexOf(q)>=0;card.hidden=!hit;if(hit)shown++}});var empty=box.querySelector('.me-c-empty');if(!shown){{if(!empty){{empty=document.createElement('div');empty.className='me-c-empty';empty.textContent='No commodity price series matches that search.';box.appendChild(empty)}}}}else if(empty)empty.remove();status.textContent='Showing '+shown+' of '+items.length+' commodity price series.'}}input.addEventListener('input',update);input.addEventListener('keydown',function(e){{if(e.key==='Escape'){{input.value='';update()}}}});clear.addEventListener('click',function(){{input.value='';update();input.focus()}});update()}})();
</script></section>'''


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = build()
    OUT.write_text(body + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(body):,} characters, {len(json.loads(DATA.read_text(encoding='utf-8'))['items'])} commodity price series). No theme file was read or written.")


if __name__ == "__main__":
    main()
