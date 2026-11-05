"""Render Blogger post bodies for a release batch of market category desks."""
from __future__ import annotations

import argparse
import html
import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "content" / "markets-today.html"
OUT = ROOT / "content" / "market-posts"

spec = importlib.util.spec_from_file_location("market_page_configs", Path(__file__).with_name("market_page_configs.py"))
config_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(config_module)

POST_ROW_JS = r'''
function pagePostLaneButton(x, sub){var d=x.d||[],o={symbol:x.s,name:d[1]||d[0],exchange:d[2],type:d[3],subtype:d[4],close:d[5],change:d[6],currency:d[7],volume:d[8],marketCap:d[9],country:d[10]||countryFromExchange(d[2]),commonName:friendlyName(d[1]||d[0],d[3],d[4])};WORLD[x.s]=meta(o);return '<button type="button" class="dyw-post-tile" data-post-symbol="'+esc(x.s)+'" data-post-sub="'+esc(sub.id)+'" aria-label="Open '+esc(String(o.symbol).toUpperCase())+', '+esc(o.name)+', '+esc(o.country||'Global')+'"><span class="dyw-post-ticker"><b>'+esc(String(o.symbol).toUpperCase())+'</b><i>'+esc(typeLabel(o.type,o.subtype))+'</i></span><strong>'+esc(o.name)+'</strong><small>'+esc(o.commonName)+' · '+esc(o.country||'Global')+' · '+esc(o.exchange||'Global')+'</small><span class="dyw-post-quote">'+(o.close==null?'&#8212;':cash(o.close,meta(o)))+' <em class="'+cls(o.change)+'">'+(o.change==null?'&#8212;':(o.change>=0?'+':'')+n(o.change,2)+'%')+'</em></span></button>'}
function loadPostLane(sub,view){if(view.dataset.loaded)return;view.dataset.loaded='1';var track=view.querySelector('.dyw-subcategory-track');if(!track)return;track.innerHTML='<div class="dyw-subcategory-copy"><span class="dyw-saved-empty">Loading '+esc(sub.label)+' instruments…</span></div><div class="dyw-subcategory-copy" aria-hidden="true"></div>';worldScan(sub.filters,{sortBy:'market_cap_basic',sortOrder:'desc'},[0,18],categoryColumns()).then(function(j){var rows=j.data||[],copy=rows.map(function(x){return pagePostLaneButton(x,sub)}).join('');if(!copy)copy='<span class="dyw-saved-empty">No matching public listings are currently returned for '+esc(sub.label)+'. Search the global directory or retry later.</span>';track.innerHTML='<div class="dyw-subcategory-copy">'+copy+'</div><div class="dyw-subcategory-copy" aria-hidden="true">'+copy.replace(/<button/g,'<button tabindex="-1"')+'</div>';view.dataset.speed=String(Math.max(22,Math.min(46,26+rows.length*.45)));initTickerDrag(view.parentElement)}).catch(function(){track.innerHTML='<div class="dyw-subcategory-copy"><span class="dyw-saved-empty">The market source did not respond. Please retry this row.</span></div><div class="dyw-subcategory-copy" aria-hidden="true"></div>'})}
function buildPostRows(){var index=E('dywDivisionIndex'),directory=E('dywDivisionDirectory');if(index)index.hidden=true;var head=R.querySelector('.dyw-browser .dyw-section-head');if(head){head.querySelector('h2').textContent=MARKET_POST_CONFIG.division+' / '+MARKET_POST_CONFIG.category;head.querySelector('p').textContent='Browse the subcategories below. Each lane shows a live-provider sample; use the table to page through all matches in that subcategory.'}directory.innerHTML='<div class="dyw-post-intro"><b>'+esc(MARKET_POST_CONFIG.category)+' in '+esc(MARKET_POST_CONFIG.division)+'</b><p>'+esc(MARKET_POST_CONFIG.scope)+'. The rows below group provider-listed instruments by subcategory. Quote coverage, currency, and update timing vary by instrument.</p></div>'+MARKET_POST_CONFIG.subcategories.map(function(s,i){return '<article class="dyw-post-lane" data-post-lane="'+esc(s.id)+'"><header><span>SUBCATEGORY '+String(i+1).padStart(2,'0')+'</span><button type="button" data-post-open="'+esc(s.id)+'">'+esc(s.label)+' <i>View matching table ↓</i></button></header><div class="dyw-ticker-viewport" tabindex="0" data-speed="30" aria-label="Continuously scrolling '+esc(s.label)+' instrument tiles. Drag or swipe to browse; release to resume."><div class="dyw-subcategory-track"><div class="dyw-subcategory-copy"><span class="dyw-saved-empty">Loading available instruments…</span></div><div class="dyw-subcategory-copy" aria-hidden="true"></div></div></div></article>'}).join('');['dywCompareOne','dywCompareTwo'].forEach(function(id){var c=E(id);if(c)c.addEventListener('change',renderPostComparison)});directory.addEventListener('click',function(e){var tile=e.target.closest('[data-post-symbol]');if(tile){var sub=MARKET_POST_CONFIG.subcategories.find(function(x){return x.id===tile.dataset.postSub});if(sub){activatePostSubcategory(sub,false);var obj=WORLD[tile.dataset.postSymbol];if(obj){registerWorld(obj);choose(obj.symbol,true)}}return}var open=e.target.closest('[data-post-open]');if(open){var s=MARKET_POST_CONFIG.subcategories.find(function(x){return x.id===open.dataset.postOpen});if(s)activatePostSubcategory(s,true)}});var io=window.IntersectionObserver?new IntersectionObserver(function(entries){entries.forEach(function(en){if(en.isIntersecting){var id=en.target.dataset.postLane,sub=MARKET_POST_CONFIG.subcategories.find(function(x){return x.id===id});if(sub)loadPostLane(sub,en.target.querySelector('.dyw-ticker-viewport'));io.unobserve(en.target)}})},{rootMargin:'320px'}):null;directory.querySelectorAll('.dyw-post-lane').forEach(function(row){if(io)io.observe(row);else{var sub=MARKET_POST_CONFIG.subcategories.find(function(x){return x.id===row.dataset.postLane});if(sub)loadPostLane(sub,row.querySelector('.dyw-ticker-viewport'))}});E('dywLoadMore').addEventListener('click',function(){loadCategory(false)});E('dywSearchCategory').addEventListener('click',function(){E('dywSearch').value=MARKET_POST_CONFIG.category;window.scrollTo({top:E('dywSearch').getBoundingClientRect().top+window.scrollY-100,behavior:'smooth'});setTimeout(function(){E('dywSearch').focus();searchWorld(MARKET_POST_CONFIG.category)},300)})}
function activatePostSubcategory(sub,move){currentPostSubcategory=sub;currentCategory={id:sub.id,label:sub.label,group:MARKET_POST_CONFIG.division+' / '+MARKET_POST_CONFIG.category,filters:sub.filters,sortBy:'market_cap_basic',sortOrder:'desc'};selectedDivision=MARKET_POST_CONFIG.division;selectedBrowseCategory=MARKET_POST_CONFIG.category;categoryOffset=0;pageComparableData=[];syncPostCompareOptions();R.querySelectorAll('.dyw-post-lane').forEach(function(row){row.classList.toggle('active',row.dataset.postLane===sub.id)});loadCategory(true);if(move)setTimeout(function(){E('dywCategoryTitle').scrollIntoView({behavior:'smooth',block:'start'})},70)}
function addPostHeadMeta(name,content,property){if(!content)return;var selector=property?'meta[property="'+property+'"]':'meta[name="'+name+'"]',m=document.head.querySelector(selector);if(!m){m=document.createElement('meta');if(property)m.setAttribute('property',property);else m.setAttribute('name',name);document.head.appendChild(m)}m.setAttribute('content',content)}
function applyPostMetadata(){addPostHeadMeta('description',MARKET_POST_CONFIG.search_description);addPostHeadMeta(null,MARKET_POST_CONFIG.title,'og:title');addPostHeadMeta(null,MARKET_POST_CONFIG.search_description,'og:description');addPostHeadMeta(null,'article','og:type');addPostHeadMeta(null,location.href.split('#')[0],'og:url');addPostHeadMeta('twitter:card','summary');addPostHeadMeta('twitter:title',MARKET_POST_CONFIG.title);addPostHeadMeta('twitter:description',MARKET_POST_CONFIG.search_description)}
var pageComparableData=[],currentPostSubcategory=null;
function syncPostCompareOptions(){if(!MARKET_POST_CONFIG)return;['dywCompareOne','dywCompareTwo'].forEach(function(id){var sel=E(id);if(!sel)return;var old=sel.value;sel.innerHTML='<option value="">Choose an instrument from this subcategory</option>'+pageComparableData.filter(function(o){return o.symbol!==current.symbol}).map(function(o){return '<option value="'+esc(o.symbol)+'">'+esc(String(o.symbol).toUpperCase())+' · '+esc(o.name)+'</option>'}).join('');if(old&&Array.prototype.some.call(sel.options,function(o){return o.value===old}))sel.value=old});renderPostComparison()}
function renderPostComparison(){if(!MARKET_POST_CONFIG)return;var picks=[E('dywCompareOne'),E('dywCompareTwo')].filter(Boolean).map(function(x){return x.value}).filter(Boolean),syms=[current.symbol].concat(picks).slice(0,3),box=E('dywCompareRows');if(!box)return;if(syms.length<2){box.innerHTML='<tr><td colspan="4">Choose up to two instruments from the selected subcategory to compare.</td></tr>';return}scan('global',syms,['description','close','change','currency','exchange','country']).then(function(j){box.innerHTML=(j.data||[]).map(function(x){var d=x.d||[],m={currency:d[3]||current.currency};return '<tr><td>'+esc(String(x.s).toUpperCase())+' · '+esc(d[0]||x.s)+'</td><td>'+cash(d[1],m)+'</td><td class="'+cls(d[2])+'">'+(d[2]==null?'—':(d[2]>=0?'+':'')+n(d[2],2)+'%')+'</td><td>'+esc(d[4]||'—')+' · '+esc(d[5]||'Global')+'</td></tr>'}).join('')||'<tr><td colspan="4">Comparison quotes are unavailable right now.</td></tr>'}).catch(function(){box.innerHTML='<tr><td colspan="4">Comparison data could not be loaded.</td></tr>'})}
'''

POST_CSS = r'''
#dyMarketWall .dyw-post-intro{margin:0 0 12px;padding:14px 16px;border-left:3px solid var(--accent);background:var(--soft);border-radius:0 10px 10px 0}
#dyMarketWall .dyw-post-intro b{font:700 18px/1.3 "Playfair Display",Georgia,serif}
#dyMarketWall .dyw-post-intro p{margin:6px 0 0;font-size:11px;line-height:1.6;color:var(--muted)}
#dyMarketWall .dyw-post-lanes{display:grid;gap:10px}
#dyMarketWall .dyw-post-lane{min-width:0;padding:10px 12px;border:1px solid var(--line);border-radius:13px;background:var(--surface)}
#dyMarketWall .dyw-post-lane.active{border-color:var(--accent);box-shadow:0 0 0 2px rgba(188,91,51,.1)}
#dyMarketWall .dyw-post-lane>header{display:flex;align-items:center;gap:12px;margin-bottom:8px}
#dyMarketWall .dyw-post-lane>header>span{font-size:8px;letter-spacing:.12em;font-weight:850;color:var(--dark);white-space:nowrap}
#dyMarketWall .dyw-post-lane>header>button{border:0;background:none;padding:0;color:var(--ink);font-weight:800;text-align:left;cursor:pointer}
#dyMarketWall .dyw-post-lane>header>button i{margin-left:5px;color:var(--muted);font-size:9px;font-style:normal;font-weight:500}
#dyMarketWall .dyw-post-tile{display:flex;flex:0 0 205px;flex-direction:column;gap:4px;justify-content:center;min-height:78px;padding:8px 10px;border:1px solid var(--line);border-radius:9px;background:#fff;color:var(--ink);text-align:left;cursor:pointer;white-space:normal}
#dyMarketWall .dyw-post-tile:hover,#dyMarketWall .dyw-post-tile:focus-visible{border-color:var(--accent);background:var(--soft)}
#dyMarketWall .dyw-post-ticker{display:flex;align-items:center;gap:6px}
#dyMarketWall .dyw-post-ticker b{font-size:9px;letter-spacing:.04em}
#dyMarketWall .dyw-post-ticker i{font-size:7px;font-style:normal;color:var(--dark);letter-spacing:.06em}
#dyMarketWall .dyw-post-tile strong{font-size:10px;line-height:1.2}
#dyMarketWall .dyw-post-tile small{font-size:8px;line-height:1.25;color:var(--muted)}
#dyMarketWall .dyw-post-quote{display:flex;justify-content:space-between;gap:8px;font-size:10px;font-weight:800;font-variant-numeric:tabular-nums}
#dyMarketWall .dyw-post-quote em{font-style:normal}
#dyMarketWall .dyw-post-quote .dyw-up{color:#16804A!important}
#dyMarketWall .dyw-post-quote .dyw-down{color:#B42318!important}
#dyMarketWall .dyw-post-compare{margin-top:14px}
@media(max-width:650px){#dyMarketWall .dyw-post-tile{flex-basis:175px}#dyMarketWall .dyw-post-lane>header{align-items:flex-start;flex-direction:column;gap:4px}}
'''

COMPARE_HTML = '''<div class="dyw-card wide dyw-post-compare"><h3>Compare instruments in this subcategory</h3><p class="dyw-sub">The two selectors are populated from the active subcategory, so comparisons stay within the same browse group.</p><div class="dyw-picker"><label class="dyw-control"><span>Comparison instrument 1</span><select class="dyw-select" id="dywCompareOne"><option value="">Choose an instrument from this subcategory</option></select></label><label class="dyw-control"><span>Comparison instrument 2</span><select class="dyw-select" id="dywCompareTwo"><option value="">Choose an instrument from this subcategory</option></select></label></div><table class="dyw-table"><thead><tr><th>Instrument</th><th>Price</th><th>Day change</th><th>Exchange / country</th></tr></thead><tbody id="dywCompareRows"><tr><td colspan="4">Select a subcategory and up to two comparison instruments.</td></tr></tbody></table><p class="dyw-note">Comparison uses provider-reported quotes; currencies may differ unless a synchronized display conversion is available.</p></div>'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise ValueError(f"Expected exactly one {label} marker, found {n}")
    return text.replace(old, new, 1)


def make_template() -> str:
    text = SOURCE.read_text(encoding="utf-8")
    # Remove page-publisher tokens that belong only to the source template and
    # otherwise render as stray plain text in Blogger post bodies.
    text = re.sub(r"(?m)^\s*(?:DY_SEO_META_(?:START|END)|DY_BRAND_IDENTITY_(?:START|END)|DY_PAGE_FAMILY_(?:START|END)|DY_BRAND_SEO_(?:START|END))\s*$", "", text)
    # Category posts use global search; there is intentionally no top-level country selector.
    text = text.replace("use the country selector above to prioritize local results.", "browse listing-country groups here; global search remains available above.")
    text = text.replace('<h1>World markets. One command centre.</h1><p>Search the global 450,000+ instrument universe, then browse stocks, indices, commodities, crypto, ETFs, funds, bonds and currencies.</p>', '<h1>{{POST_H1}}</h1><p>{{POST_DECK}}</p>')
    old_browser = re.search(r'<section class="dyw-browser">.*?</section>', text, re.S)
    if not old_browser:
        raise ValueError("Could not locate browser section in Markets Today source")
    browser = '''<section class="dyw-browser"><div class="dyw-section-head"><h2>{{POST_DIVISION}} / {{POST_CATEGORY}}</h2><p>{{POST_BROWSER_NOTE}}</p></div><nav class="dyw-division-index" id="dywDivisionIndex" aria-label="Market division index" hidden></nav><div class="dyw-division-directory" id="dywDivisionDirectory"></div><div class="dyw-ranking" id="dywInstrumentResults"><div class="dyw-ranking-head"><div><span id="dywCategoryPath">Loading category path</span><h3 id="dywCategoryTitle">Select a subcategory</h3></div><div class="dyw-ranking-count"><b id="dywCategoryCount">—</b><span>instruments available</span></div></div><p class="dyw-results-intro">Select an instrument tile to open its analysis below. The table pages through all provider matches for the selected subcategory.</p><div class="dyw-rank-labels"><span># / Instrument</span><span id="dywRankLabelMarket">Exchange / country</span><span id="dywRankLabelValue">Price</span><span id="dywRankLabelMove">Change</span></div><div id="dywCategoryList"><div class="dyw-saved-empty">Choose a subcategory to load its instrument table.</div></div><div class="dyw-ranking-foot"><p id="dywRemaining">Select a subcategory above to load matching instruments.</p><div><button id="dywLoadMore" type="button">Load 50 more</button><button id="dywSearchCategory" type="button">Search this subcategory</button></div></div></div></section>'''
    text = text[:old_browser.start()] + browser + text[old_browser.end():]
    text = text.replace('</style>\n\n<header class="dyw-hero">', POST_CSS + '\n</style>\n\n<header class="dyw-hero">', 1)
    text = replace_once(text, 'function buildCategories(){var index=E(\'dywDivisionIndex\'),directory=E(\'dywDivisionDirectory\');',
                        'function buildCategories(){if(MARKET_POST_CONFIG){buildPostRows();return}var index=E(\'dywDivisionIndex\'),directory=E(\'dywDivisionDirectory\');', 'buildCategories start')
    text = text.replace("function buildCategories(){if(MARKET_POST_CONFIG){buildPostRows();return}", POST_ROW_JS + "\nfunction buildCategories(){if(MARKET_POST_CONFIG){buildPostRows();return}", 1)
    old_select = "function selectCategory(id,move){currentCategory=CATEGORIES[id]||CATEGORIES.global;categoryOffset=0;selectedDivision='Popular';selectedBrowseCategory='Market screens';MARKET_DIVISIONS.forEach(function(d){d.categories.forEach(function(cat){if(cat.items.indexOf(currentCategory.id)>=0){selectedDivision=d.title;selectedBrowseCategory=cat.title}})});R.querySelectorAll('[data-cat]').forEach(function(b){b.classList.toggle('active',b.dataset.cat===currentCategory.id)});loadCategory(true);if(move)setTimeout(function(){E('dywCategoryTitle').scrollIntoView({behavior:'smooth',block:'start'})},80)}"
    text = replace_once(text, old_select,
        "function selectCategory(id,move){if(MARKET_POST_CONFIG){var ps=MARKET_POST_CONFIG.subcategories.find(function(x){return x.id===id});if(ps){activatePostSubcategory(ps,!!move);return}}currentCategory=CATEGORIES[id]||CATEGORIES.global;categoryOffset=0;selectedDivision='Popular';selectedBrowseCategory='Market screens';MARKET_DIVISIONS.forEach(function(d){d.categories.forEach(function(cat){if(cat.items.indexOf(currentCategory.id)>=0){selectedDivision=d.title;selectedBrowseCategory=cat.title}})});R.querySelectorAll('[data-cat]').forEach(function(b){b.classList.toggle('active',b.dataset.cat===currentCategory.id)});loadCategory(true);if(move)setTimeout(function(){E('dywCategoryTitle').scrollIntoView({behavior:'smooth',block:'start'})},80)}",
        'selectCategory')
    old_dir = "function loadDirectory(){worldScan([],null,[0,1],['name']).then(function(j){E('dywUniverse').textContent=Number(j.totalCount||0).toLocaleString('en-IN');E('dywClock').textContent='Global directory connected · '+Number(j.totalCount||0).toLocaleString('en-IN')+' instruments'}).catch(function(){});buildCategories();selectCategory('global')}"
    text = replace_once(text, old_dir,
        "function loadDirectory(){worldScan([],null,[0,1],['name']).then(function(j){E('dywUniverse').textContent=Number(j.totalCount||0).toLocaleString('en-IN');E('dywClock').textContent='Global directory connected · '+Number(j.totalCount||0).toLocaleString('en-IN')+' instruments'}).catch(function(){});buildCategories();if(MARKET_POST_CONFIG){if(MARKET_POST_CONFIG.subcategories.length)activatePostSubcategory(MARKET_POST_CONFIG.subcategories[0],false)}else selectCategory('global')}",
        'loadDirectory')
    text = text.replace("request.then(function(j){categoryTotal=j.totalCount||0;var html=", "request.then(function(j){categoryTotal=j.totalCount||0;if(MARKET_POST_CONFIG){pageComparableData=(pageComparableData||[]).concat(j.data||[]).filter(function(x,i,a){return a.findIndex(function(y){return y.s===x.s})===i}).slice(-250);syncPostCompareOptions()}var html=",1)
    # Add peer comparison after every analytical panel but before the analysis section ends.
    text = replace_once(text, '</div>\n</section>\n<footer class="dyw-footer">', '</div>\n'+COMPARE_HTML+'\n</section>\n<footer class="dyw-footer">', 'analysis closing section')
    # Metadata loader is injected in the main inline script by the post renderer.
    text = text.replace("(function(){'use strict';var R=document.getElementById('dyMarketWall');if(!R)return;", "(function(){'use strict';var R=document.getElementById('dyMarketWall');if(!R)return;var MARKET_POST_CONFIG=window.ME_MARKET_POST_CONFIG||null;if(MARKET_POST_CONFIG)applyPostMetadata();", 1)
    # First article section supplies distinctive, readable text before market widgets.
    text = text.replace('<section class="dyw-command">', '{{POST_EDITORIAL}}\n<section class="dyw-command">', 1)
    return text


def render_post(template: str, cfg: dict, publication_date: bool = False) -> str:
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
    config = {
        **cfg,
        "date_published": today if publication_date or cfg.get("batch") == 1 else None,
    }
    # page-specific headline and explanatory copy; never rely on ticker values as the only prose.
    h1 = f"{cfg['division']}: {cfg['category']} market directory"
    deck = f"Explore {cfg['scope']}. Browse provider-classified subcategories, compare reported market data, and open an instrument's chart and analysis."
    browser_note = f"{cfg['category']} within {cfg['division']}. Each row is a subcategory of this category; quote coverage and update timing depend on the provider."
    references = {
        'Equity stocks': [('TradingView market scanner','https://www.tradingview.com/markets/stocks/'),('U.S. SEC EDGAR filings','https://www.sec.gov/edgar/search/'),('NSE India','https://www.nseindia.com/'),('BSE India','https://www.bseindia.com/')],
        'Market indices': [('TradingView market scanner','https://www.tradingview.com/markets/indices/'),('S&P Dow Jones Indices','https://www.spglobal.com/spdji/en/'),('Nasdaq Indexes','https://www.nasdaq.com/solutions/indexes')],
        'Commodities': [('TradingView commodity markets','https://www.tradingview.com/markets/commodities/'),('CME Group contract resources','https://www.cmegroup.com/markets.html'),('ICE markets','https://www.ice.com/markets'),('London Metal Exchange','https://www.lme.com/')],
        'Depositary receipts': [('SEC EDGAR company filings','https://www.sec.gov/edgar/search/'),('Investor.gov international investing','https://www.investor.gov/introduction-investing/investing-basics/investment-products/american-depositary-receipts-adrs')],
        'Bonds and fixed income': [('U.S. Treasury marketable securities','https://treasurydirect.gov/marketable-securities/'),('FINRA fixed-income data','https://www.finra.org/finra-data/fixed-income'),('Reserve Bank of India','https://www.rbi.org.in/')],
        'Exchange-traded funds (ETFs)': [('SEC ETF resources','https://www.investor.gov/introduction-investing/investing-basics/investment-products/exchange-traded-funds-etfs'),('TradingView fund scanner','https://www.tradingview.com/markets/etf/funds/portfolio-allocation/market-cap/'),('NSE India','https://www.nseindia.com/')],
        'Index funds': [('SEC investor resources','https://www.investor.gov/'),('U.S. SEC EDGAR filings','https://www.sec.gov/edgar/search/'),('AMFI India','https://www.amfiindia.com/')],
        'Mutual funds': [('SEC mutual-fund resources','https://www.investor.gov/introduction-investing/investing-basics/investment-products/mutual-funds-and-exchange-traded-funds-etfs'),('AMFI India','https://www.amfiindia.com/'),('U.S. SEC EDGAR filings','https://www.sec.gov/edgar/search/')],
        'Other funds': [('U.S. SEC EDGAR filings','https://www.sec.gov/edgar/search/'),('AMFI India','https://www.amfiindia.com/'),('TradingView fund scanner','https://www.tradingview.com/markets/etf/funds/portfolio-allocation/market-cap/')],
        'Futures': [('CME Group contract resources','https://www.cmegroup.com/markets.html'),('ICE markets','https://www.ice.com/markets'),('U.S. CFTC','https://www.cftc.gov/MarketReports/index.htm')],
        'Options': [('Options Industry Council education','https://www.optionseducation.org/'),('Options Clearing Corporation','https://www.theocc.com/'),('U.S. CFTC','https://www.cftc.gov/')],
        'Currencies and foreign exchange': [('Bank for International Settlements','https://www.bis.org/statistics/rpfx22.htm'),('Reserve Bank of India','https://www.rbi.org.in/'),('TradingView forex scanner','https://www.tradingview.com/markets/currencies/rates-all/')],
        'Cryptocurrency spot markets': [('U.S. SEC investor resources','https://www.investor.gov/'),('TradingView crypto markets','https://www.tradingview.com/markets/cryptocurrencies/prices-all/')],
        'Crypto derivatives': [('CME Group cryptocurrency products','https://www.cmegroup.com/markets/cryptocurrencies.html'),('U.S. CFTC','https://www.cftc.gov/'),('TradingView futures markets','https://www.tradingview.com/markets/futures/quotes-all/')],
        'Economic indicators': [('FRED economic data','https://fred.stlouisfed.org/'),('World Bank Data','https://data.worldbank.org/'),('IMF Data','https://www.imf.org/en/Data')],
        'Structured products': [('FINRA structured notes overview','https://www.finra.org/investors/investing/investment-products/structured-notes'),('SEC EDGAR filings','https://www.sec.gov/edgar/search/'),('Investor.gov','https://www.investor.gov/')],
        'REITs and listed real estate': [('SEC REIT investor resources','https://www.investor.gov/introduction-investing/investing-basics/investment-products/real-estate-investment-trusts-reits'),('Nareit investor resources','https://www.reit.com/investing'),('SEC EDGAR filings','https://www.sec.gov/edgar/search/')],
    }.get(cfg['division'], [('TradingView global scanner','https://www.tradingview.com/markets/')])
    refs_html = ''.join('<li><a href="'+html.escape(url,quote=True)+'" rel="noopener noreferrer">'+html.escape(label)+'</a></li>' for label,url in references)
    article_schema = {
        '@context':'https://schema.org','@type':'BlogPosting','headline':cfg['title'],
        'description':cfg['search_description'],'dateModified':today,
        'author':{'@type':'Organization','name':'Milled Edge','url':'https://milledgeindia.blogspot.com/p/about-milled-edge.html'},
        'publisher':{'@type':'Organization','name':'Milled Edge','url':'https://milledgeindia.blogspot.com/'},
        'articleSection':cfg['division'],'keywords':', '.join([cfg['division'],cfg['category']]+cfg['labels']),
    }
    if config["date_published"]:
        article_schema["datePublished"] = config["date_published"]
    schema_html='<script type="application/ld+json">'+json.dumps(article_schema,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+'</script>'
    coverage_note = {
        "Options": "<p><strong>Coverage note:</strong> the connected global scanner does not return standalone call/put option contracts. These rows therefore show related underlyings—not option contracts. Verify strike, expiry, exercise style, settlement, and contract terms against the relevant exchange or clearing-house option chain.</p>",
        "Crypto derivatives": "<p><strong>Coverage note:</strong> provider subtype and symbol text are used to identify crypto-linked derivative records. The source does not consistently distinguish perpetuals from dated futures or expose a standalone crypto-options chain; verify product terms with the venue.</p>",
        "Structured products": "<p><strong>Coverage note:</strong> scanner labels such as certificate or warrant are discovery cues only; they do not establish capital protection, leverage, issuer credit, or payoff terms. Consult the current issuer prospectus and exchange documents.</p>",
        "Economic indicators": "<p><strong>Coverage note:</strong> provider labels, release calendars, units, seasonal adjustment, and revision history can differ. Verify each series with its originating statistical agency before comparing observations.</p>",
    }.get(cfg["division"], "")
    editorial = (
        '<section class="dyw-post-intro"><p class="dyw-eyebrow">'+html.escape(cfg['division'])+' / '+html.escape(cfg['category'])+'</p>'
        '<h2>How to use this market directory</h2><p>'+html.escape(cfg['search_description'])+'</p>'
        '<p>This page groups instruments by '+html.escape(cfg['scope'])+'. Select a subcategory row to load its matching instrument table; each table is paginated so additional provider matches remain available. Select a ticker to open the quote, chart, technical panels, related coverage, and news where supported.</p>' + coverage_note +
        '<h2>Classification, sources, and data limits</h2><p>Provider type, subtype, issuer country, exchange, and quote fields are used when supplied. Category matches can be incomplete when a provider has missing metadata; an absent result does not prove that a market or instrument does not exist. Price and activity fields may be delayed, may differ across venues, and are not executable offers.</p>'
        '<p>Use primary issuer, exchange, benchmark, or contract documents to verify instrument terms before relying on a figure:</p><ul>'+refs_html+'</ul>'
        '<p><strong>Editorial and risk note:</strong> Milled Edge provides market information and educational context, not personalized investment advice. Automated data collection and formatting do not constitute independent verification of every quote. See the <a href="/p/financial-disclaimer-milled-edge.html">financial disclaimer</a>.</p>'
        '<p>Category content last reviewed '+html.escape(today)+'; live quote timestamps are shown separately and do not represent an editorial review.</p></section>'+schema_html
    )
    out = template.replace('{{POST_H1}}', html.escape(h1)).replace('{{POST_DECK}}', html.escape(deck))
    out = out.replace('{{POST_DIVISION}}', html.escape(cfg['division'])).replace('{{POST_CATEGORY}}', html.escape(cfg['category']))
    out = out.replace('{{POST_BROWSER_NOTE}}', html.escape(browser_note)).replace('{{POST_EDITORIAL}}', editorial)
    # Config JSON is placed just before the application's main IIFE and escaped for a script block.
    marker = "<script>\n(function(){'use strict';var R=document.getElementById('dyMarketWall');if(!R)return;"
    config_js = '<script>window.ME_MARKET_POST_CONFIG='+json.dumps(config,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';</script>\n'
    if marker not in out:
        raise ValueError('Main application script marker not found')
    out = out.replace(marker, config_js+marker, 1)
    return out.rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', type=int, default=1, choices=range(1,6))
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--publication-date', action='store_true', help='include datePublished for content being published now')
    args = ap.parse_args()
    template = make_template()
    pages = [p for p in config_module.build_page_configs() if p['batch'] == args.batch]
    target = OUT / f"batch-{args.batch}"
    target.mkdir(parents=True, exist_ok=True)
    catalog_path = OUT / f"batch-{args.batch}-catalog.json"
    if not args.dry_run:
        catalog_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for p in pages:
        body = render_post(template, p, publication_date=args.publication_date)
        unresolved = [mark for mark in ('{{POST_H1}}','{{POST_DECK}}','{{POST_DIVISION}}','{{POST_CATEGORY}}','{{POST_BROWSER_NOTE}}','{{POST_EDITORIAL}}') if mark in body]
        if unresolved:
            raise SystemExit(f"Unresolved placeholders in {p['slug']}: {unresolved}")
        if len(body) > 1_000_000:
            raise SystemExit(f"Post body too large for {p['slug']}: {len(body)}")
        path = target / f"{p['slug']}.html"
        if not args.dry_run:
            path.write_text(body, encoding='utf-8')
        print(f"{p['slug']}: {len(body):,} chars, {len(p['subcategories'])} subcategory lanes")
    print(f"Batch {args.batch}: {len(pages)} Blogger post bodies; {'dry-run only' if args.dry_run else f'wrote {target}'}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
