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
        formal = html.escape(item["formal_name"])
        common = html.escape(item["common_name"])
        location = html.escape(item["location"])
        series_type = html.escape(item["series_type"])
        symbol = html.escape(item["symbol"])
        value = f'{item["value"]:,.2f}'.rstrip("0").rstrip(".")
        status = " · estimate" if item.get("status") == "estimated" else ""
        haystack = html.escape((item["name"] + " " + item["basis"] + " " + item["unit"] + " " + item["formal_name"] + " " + item["location"]).casefold(), quote=True)
        entries.append(
            f'<article class="me-c-item" data-search="{haystack}">'
            f'<div class="me-c-top"><h2>{name}</h2><span class="me-c-period">{html.escape(data["price_month"])}</span></div>'
            f'<p class="me-c-price">{html.escape(value)} <small>{unit}</small></p>'
            f'<p class="me-c-code">{series_type} · {symbol}</p>'
            f'<dl class="me-c-details"><div><dt>Formal series</dt><dd>{formal}</dd></div><div><dt>Common name</dt><dd>{common}</dd></div><div><dt>Country / location</dt><dd>{location}</dd></div><div><dt>Price basis</dt><dd>{basis}{status}</dd></div></dl>'
            '</article>'
        )
    title = html.escape(data["title"])
    source = html.escape(data["source_name"])
    source_url = html.escape(data["source_url"], quote=True)
    monthly_url = html.escape(data["monthly_file_url"], quote=True)
    release = html.escape(data["release_date"])
    price_month = html.escape(data["price_month"])
    note = html.escape(data["note"])
    description = html.escape(data["meta_description"])
    keyword_value = html.escape(", ".join(data["topic_labels"]), quote=True)
    topic_chips = "".join(f'<span>{html.escape(label)}</span>' for label in data["topic_labels"])
    locations = sorted({item["location"] for item in data["items"]})
    schema = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": f"Physical commodity price benchmarks — {data['price_month']}",
        "description": data["meta_description"],
        "url": "https://millededgeindia.blogspot.com/p/commodities.html",
        "creator": {"@type": "Organization", "name": "World Bank Prospects Group"},
        "publisher": {"@type": "Organization", "name": "MILLED EDGE"},
        "dateModified": data["release_date"],
        "temporalCoverage": "2026-10",
        "spatialCoverage": [{"@type": "Place", "name": place} for place in locations],
        "citation": data["source_url"],
        "variableMeasured": [
            {"@type": "PropertyValue", "name": x["formal_name"], "unitText": x["unit"], "value": x["value"]}
            for x in data["items"]
        ],
    }
    schema_json = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    meta_json = json.dumps({"description": data["meta_description"], "keywords": ", ".join(data["topic_labels"]), "title": "Commodities | MILLED EDGE", "canonical": "https://millededgeindia.blogspot.com/p/commodities.html"}, ensure_ascii=False)
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
.me-c-code{{margin:8px 0;color:var(--c-copper);font-size:8px;font-weight:850;letter-spacing:.06em}}
.me-c-details{{margin:10px 0 0;display:grid;gap:7px}}
.me-c-details div{{display:grid;grid-template-columns:92px minmax(0,1fr);gap:8px;font-size:10px;line-height:1.4}}
.me-c-details dt{{color:var(--c-muted);font-weight:700}}
.me-c-details dd{{margin:0;color:var(--c-ink)}}
.me-c-price{{margin:13px 0 5px;font:800 25px/1.1 Georgia,serif;font-variant-numeric:tabular-nums;color:var(--c-copper);overflow-wrap:anywhere}}
.me-c-price small{{font:700 11px/1.4 Arial,Helvetica,sans-serif;color:var(--c-muted)}}
.me-c-basis{{margin:0;color:var(--c-muted);font-size:11px;line-height:1.45}}
.me-c-empty{{grid-column:1/-1;padding:22px;text-align:center;border:1px dashed var(--c-line);border-radius:12px;color:var(--c-muted)}}
.me-c-method{{margin-top:20px;padding:16px 18px;border:1px solid var(--c-line);border-radius:14px;background:#faf5ec;color:var(--c-muted);font-size:12px}}
.me-c-method h2{{margin:0 0 7px;color:var(--c-ink);font:700 17px Georgia,serif}}
.me-c-method p{{margin:7px 0}}
.me-c-method a{{color:var(--c-copper);font-weight:700}}
.me-c-topic-labels{{display:flex;flex-wrap:wrap;gap:6px;margin-top:16px}}
.me-c-topic-labels span{{padding:5px 8px;border:1px solid #e0ccb1;border-radius:999px;background:#fffdf8;color:#76543a;font-size:9px;font-weight:700}}
.me-c-faq{{margin-top:16px;padding:15px 18px;border:1px solid var(--c-line);border-radius:14px;background:#fffdf8}}
.me-c-faq h2{{margin:0 0 10px;font:700 18px Georgia,serif}}
.me-c-faq h3{{margin:12px 0 3px;font-size:12px}}
.me-c-faq p{{margin:0;color:var(--c-muted);font-size:11px}}
@media(max-width:850px){{.me-c-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
@media(max-width:540px){{.me-commodity-page{{padding:12px}}.me-c-grid{{grid-template-columns:1fr}}.me-c-toolbar{{align-items:stretch;flex-direction:column}}.me-c-toolbar button{{width:100%}}.me-c-hero{{padding:22px 17px}}}}
</style>
<header class="me-c-hero">
<p class="me-c-kicker">MILLED EDGE · physical commodity prices</p>
<h1 id="me-c-title">{title}</h1>
<p class="me-c-lead">A single, searchable board of {len(data['items'])} physical-commodity price benchmarks—including gold and silver. No category menus or subcategories, and no futures, ETFs, bonds, miners, CFDs, or other financial instruments.</p>
<div class="me-c-topic-labels" aria-label="Page topics">{topic_chips}</div>
<div class="me-c-stamp"><span>Reference month: {price_month}</span><span>Source released: {release}</span><span>Monthly benchmarks · not live quotes</span></div>
</header>
<div class="me-c-toolbar" role="search"><input id="meCommoditySearch" type="search" autocomplete="off" placeholder="Search commodity names, grades, locations or basis…" aria-label="Search all commodity price benchmarks"><button id="meCommodityClear" type="button">Clear search</button></div>
<p class="me-c-status" id="meCommodityCount" role="status" aria-live="polite">Showing {len(data['items'])} commodity price series.</p>
<div class="me-c-grid" id="meCommodityItems">{''.join(entries)}</div>
<section class="me-c-method"><h2>Price basis and limitations</h2>
<p>{note} These are source-specific grade, location, import/export, auction, fixing, spot, or physical-settlement price series—not one universal price for every physical delivery. Gold and silver figures are international benchmarks, not Indian jewellery-shop or retail cash prices; purity, duties, taxes and local premiums are not included.</p>
<p>Source: <a href="{source_url}" target="_blank" rel="noopener">{source} — November 2026 sheet (PDF)</a> · <a href="{monthly_url}" target="_blank" rel="noopener">monthly source workbook</a>.</p>
<p>Only commodity price series with a reported October 2026 value and a non-futures physical-market basis are listed. Explicit futures/forward-month quotations, aggregate commodity indexes, ETFs, company shares, bonds and other financial instruments are omitted. The source does not assign exchange tickers to these physical price series; no symbols have been invented.</p></section>
<section class="me-c-faq" aria-label="Commodity price questions"><h2>Commodity price questions</h2><h3>Are these live or intraday prices?</h3><p>No. They are the latest reported monthly averages for October 2026, released on November 3, 2026.</p><h3>Are gold and silver shown at local retail or jewellery rates?</h3><p>No. They are international reference benchmarks; local taxes, purity, import duties, dealer premiums and making charges are not included.</p><h3>Are futures or financial products included?</h3><p>No. Explicit futures and forward-month quotations and financial securities are excluded. Each listed row is a physical-commodity price series with its stated location, grade and delivery basis.</p><h3>Why does each commodity show a different location?</h3><p>Physical commodities do not have one universal cash price. The source reports specific markets, qualities and delivery bases, shown on each entry.</p></section>
<script type="application/ld+json">{schema_json}</script>
<script>(function(){{'use strict';var m={meta_json};function set(name,value,property){{var q=property?'meta[property="'+property+'"]':'meta[name="'+name+'"]',x=document.head.querySelector(q);if(!x){{x=document.createElement('meta');if(property)x.setAttribute('property',property);else x.setAttribute('name',name);document.head.appendChild(x)}}x.setAttribute('content',value)}}set('description',m.description);set('keywords',m.keywords);set('robots','index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1');set(null,m.title,'og:title');set(null,m.description,'og:description');set(null,'website','og:type');set(null,m.canonical,'og:url');set('twitter:card','summary');set('twitter:title',m.title);set('twitter:description',m.description);var c=document.head.querySelector('link[rel="canonical"]');if(!c){{c=document.createElement('link');c.rel='canonical';document.head.appendChild(c)}}c.href=m.canonical;document.title=m.title}})();</script>
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
