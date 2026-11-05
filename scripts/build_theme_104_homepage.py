"""Build a separate Blogger theme with a 104-category market homepage.

The source theme remains untouched. This builder adds four live market tapes,
a category directory, useful calculators, About/social contact links, and
replaces links to the two retired market pages with homepage anchors.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "content" / "theme-milled-edge-fresh.xml"
OUTPUT = ROOT / "content" / "theme-104-category-homepage.xml"
BLOG = "https://millededgeindia.blogspot.com"


def tape(title: str, key: str, intro: str, state: str) -> str:
    section_id = "me-live-tapes" if key == "funds" else f"me-tape-{key}"
    return f"""<section aria-label='{html.escape(title, quote=True)} live quotes' class='me-tape' id='{section_id}'>
<div class='me-tape-head'><div><span class='me-kicker'>MARKET TAPE · {key.upper()}</span><h2>{html.escape(title)}</h2><p>{html.escape(intro)}</p></div><span aria-live='polite' class='me-tape-state' id='me-state-{key}'>{html.escape(state)}</span></div>
<div class='me-tape-window' id='me-wrap-{key}'><div class='me-tape-track' id='me-track-{key}'><span class='me-quote me-quote-wait'>Connecting to the public quote feed…</span></div></div>
</section>"""


def _market_catalog() -> list[dict]:
    rows = []
    for batch in range(1, 6):
        rows.extend(json.loads((ROOT / f"content/market-posts/batch-{batch}-catalog.json").read_text(encoding="utf-8")))
    return rows


def _post_urls() -> dict[str, str]:
    path = ROOT / "content" / "market-post-links.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def market_today_menu() -> str:
    """Build 18 divisions: 17 expand to direct posts; Commodities opens its spot board."""
    entries, urls = _market_catalog(), _post_urls()
    groups: dict[str, list[dict]] = {}
    names: dict[str, str] = {}
    for item in entries:
        groups.setdefault(item["division_id"], []).append(item)
        names[item["division_id"]] = item["division"]
    items = []
    for number, (division_id, rows) in enumerate(groups.items(), 1):
        title = html.escape(names[division_id])
        if division_id == "commodities":
            items.append(f"<a aria-label='Open the commodities spot-reference board' class='me-menu-commodity' href='{BLOG}/#me-commodity-board'><span class='me-menu-num'>{number:02d}</span><span class='me-menu-title'>{title}</span><span class='me-menu-go'>Open spot board ↗</span></a>")
            continue
        links = "".join(
            ("<li><a href='" + html.escape(urls[x['slug']], quote=True) + "'>" + html.escape(x["category"]) + "</a></li>")
            if x["slug"] in urls else
            ("<li class='me-menu-pending'><span>" + html.escape(x["category"]) + "</span><small>Post pending</small></li>")
            for x in rows
        )
        items.append(
            f"<details class='me-menu-division' data-me-menu-division='true'><summary><span class='me-menu-num'>{number:02d}</span><span class='me-menu-title'>{title}</span><span class='me-menu-count'>{len(rows)}</span></summary><div class='me-menu-cats'><div class='me-menu-cats-inner'><ul>{links}</ul></div></div></details>"
        )
    return "<section aria-label='Market Today divisions' class='me-market-panel' hidden='hidden' id='meMarketPanel'><div class='me-market-grid'>" + "".join(items) + "</div></section>"


def category_directory() -> str:
    entries, urls = _market_catalog(), _post_urls()
    groups: dict[str, list[dict]] = {}
    names: dict[str, str] = {}
    for item in entries:
        groups.setdefault(item["division_id"], []).append(item)
        names[item["division_id"]] = item["division"]
    blocks = []
    for n, (division_id, rows) in enumerate(groups.items(), 1):
        title = html.escape(names[division_id])
        if division_id == "commodities":
            blocks.append(f"<article class='me-division me-commodity-link'><a href='{BLOG}/#me-commodity-board'><span class='me-div-num'>{n:02d}</span><span class='me-div-title'>Commodities · live spot board</span><span class='me-div-count'>Open board ↗</span></a></article>")
            continue
        links = "".join(
            ("<li><a href='" + html.escape(urls[x['slug']], quote=True) + "'>" + html.escape(x["category"]) + "</a></li>")
            if x["slug"] in urls else
            ("<li class='me-pending'><span>" + html.escape(x["category"]) + " · post pending</span></li>")
            for x in rows
        )
        blocks.append(f"<details class='me-division' id='me-dir-{html.escape(division_id)}'><summary><span class='me-div-num'>{n:02d}</span><span class='me-div-title'>{title}</span><span class='me-div-count'>{len(rows)} routes</span></summary><ul>{links}</ul></details>")
    return """<section class='me-directory' id='me-category-directory' aria-labelledby='me-directory-title'>
<div class='me-directory-head'><span class='me-kicker'>95 CATEGORY ROUTES · 18 MARKET DIVISIONS</span><h2 id='me-directory-title'>One directory. Eighteen market divisions.</h2><p>Choose a division to see its published categories. Each category opens its post directly. Commodities opens a single spot-reference board; it is not subdivided into futures, funds, or related instruments.</p></div><div class='me-division-grid'>""" + "".join(blocks) + "</div></section>"


def commodity_board() -> str:
    rows = [
        ("TVC:GOLD", "GOLD", "Gold", "troy oz"), ("TVC:SILVER", "SILVER", "Silver", "troy oz"),
        ("TVC:PLATINUM", "PLATINUM", "Platinum", "troy oz"), ("TVC:PALLADIUM", "PALLADIUM", "Palladium", "troy oz"),
        ("OANDA:XCUUSD", "COPPER", "Copper", "lb"), ("OANDA:WHEATUSD", "WHEAT", "Wheat", "bushel"),
        ("OANDA:SUGARUSD", "SUGAR", "Sugar", "lb"), ("OANDA:CORNUSD", "CORN", "Corn", "bushel"),
        ("OANDA:SOYBNUSD", "SOYBEANS", "Soybeans", "bushel"), ("OANDA:NATGASUSD", "NATURAL GAS", "Natural gas", "MMBtu"),
    ]
    cards = "".join(
        f"<article class='me-spot-card' data-me-spot='{symbol}' data-me-unit='{unit}'><span>{ticker} · {symbol.split(':')[0]}</span><h3>{name}</h3><b class='me-spot-price'>Connecting…</b><small class='me-spot-change'>Waiting for provider quote</small><small class='me-spot-inr' hidden='hidden'></small></article>"
        for symbol, ticker, name, unit in rows
    )
    return "<section aria-labelledby='me-commodity-title' class='me-spot-board' id='me-commodity-board'><div class='me-spot-head'><span class='me-kicker'>MARKET TODAY · COMMODITIES</span><h2 id='me-commodity-title'>Commodity price board</h2><p>Flat list of distinct commodity prices; this board excludes futures contracts, ETFs, miners, and other related securities. The provider classifies these live references as commodity CFDs, not physical cash-market offers. Gold, silver, platinum, and palladium are quoted per troy ounce; other unit labels follow each provider benchmark.</p></div><div aria-live='polite' class='me-spot-grid' id='meSpotGrid'>" + cards + "</div><p class='me-spot-foot' id='meSpotUpdated'>Only direct commodity references returned by the public provider are shown. Local physical/retail rates, premiums, taxes, and grade/location adjustments are not represented. Indicative INR per gram for precious metals is a reference conversion only.</p></section>"

def social_about() -> str:
    profiles = [
        ("Instagram", "https://www.instagram.com/milledge"),
        ("X", "https://x.com/MilledEdge"),
        ("LinkedIn", "https://www.linkedin.com/company/milled-edge/"),
        ("Facebook", "https://www.facebook.com/milledge"),
        ("Bluesky", "https://bsky.app/profile/milledge.bsky.social"),
        ("Mastodon", "https://mastodon.social/@milledge"),
        ("Tumblr", "https://www.tumblr.com/milledge"),
    ]
    links = "".join(f"<a href='{url}' rel='noopener noreferrer' target='_blank'>{name} <span aria-hidden='true'>↗</span></a>" for name, url in profiles)
    return f"""<section class='me-about-panel' id='me-about-contact' aria-labelledby='me-about-heading'><div><span class='me-kicker'>ABOUT THE DESK</span><h2 id='me-about-heading'>Clear money writing, with the working shown.</h2><p><strong>MILLED EDGE</strong> is an independent financial-education publication written and published by <strong>Kushal Kumar Daga</strong>. Coverage connects personal finance, business finance and market context. Editorial practice: define the question, check sources and dates, show assumptions, explain limits, and correct material errors. The site is educational—not personalised investment, legal or tax advice.</p><div class='me-about-actions'><a href='{BLOG}/p/about-milled-edge.html'>Read About MILLED EDGE ↗</a><a href='mailto:kushalkumardaga.ca@gmail.com'>kushalkumardaga.ca@gmail.com</a><a href='{BLOG}/p/contact-milled-edge.html'>Contact desk ↗</a></div></div><div class='me-social'><h3>Connect on every listed social profile</h3><div class='me-social-links'>{links}</div><p>Profiles listed on the Contact page; links open in a new tab.</p></div></section>"""


def ticker_script() -> str:
    return r"""/* ME 104 HOME — four source-attributed, drag-aware market tapes */
function inr(v,dg){try{return '\u20b9'+Number(v).toLocaleString('en-IN',{maximumFractionDigits:dg==null?2:dg});}catch(e){return String(v);}}
var tapeGroups={
 commodities:[
  {s:'TVC:GOLD',n:'Gold',u:'/ troy oz'},{s:'TVC:SILVER',n:'Silver',u:'/ troy oz'},
  {s:'TVC:PLATINUM',n:'Platinum',u:'/ troy oz'},{s:'TVC:PALLADIUM',n:'Palladium',u:'/ troy oz'},
  {s:'OANDA:XCUUSD',n:'Copper',u:'/ lb'},{s:'OANDA:WHEATUSD',n:'Wheat',u:'/ bushel'},
  {s:'OANDA:SUGARUSD',n:'Sugar',u:'/ lb'},{s:'OANDA:CORNUSD',n:'Corn',u:'/ bushel'},
  {s:'OANDA:SOYBNUSD',n:'Soybeans',u:'/ bushel'},{s:'OANDA:NATGASUSD',n:'Natural gas',u:'/ MMBtu'}
 ],
 funds:[
  {s:'AMEX:SPY',n:'S&P 500 ETF',market:'US'},{s:'NASDAQ:QQQ',n:'Nasdaq 100 ETF',market:'US'},{s:'AMEX:VT',n:'Global equity ETF',market:'Global'},
  {s:'AMEX:VOO',n:'S&P 500 index ETF',market:'US'},{s:'NASDAQ:BND',n:'US total bond ETF',market:'US'},{s:'NASDAQ:TLT',n:'US Treasury bond ETF',market:'US'},
  {s:'TVC:US10Y',n:'US 10-year yield',suffix:'% yield',market:'US'},
  {n:'Mutual-fund NAVs',note:'NAVs update on fund-provider schedules; this feed does not expose a comparable intraday NAV.'}
 ],
 equities:[
  {s:'NASDAQ:AAPL',n:'Apple',market:'US'},{s:'NASDAQ:MSFT',n:'Microsoft',market:'US'},{s:'NASDAQ:NVDA',n:'NVIDIA',market:'US'},{s:'NASDAQ:GOOGL',n:'Alphabet',market:'US'},{s:'NASDAQ:AMZN',n:'Amazon',market:'US'},
  {s:'NASDAQ:META',n:'Meta',market:'US'},{s:'NASDAQ:AVGO',n:'Broadcom',market:'US'},{s:'NYSE:BRK.B',n:'Berkshire Hathaway',market:'US'},
  {s:'NSE:RELIANCE',n:'Reliance Industries',market:'IN'},{s:'NSE:TCS',n:'Tata Consultancy Services',market:'IN'},{s:'NSE:HDFCBANK',n:'HDFC Bank',market:'IN'},
  {s:'SSE:600519',n:'Kweichow Moutai',market:'CN'},{s:'SZSE:300750',n:'CATL',market:'CN'},{s:'HKEX:700',n:'Tencent',market:'CN'},
  {s:'LSE:AZN',n:'AstraZeneca',market:'GB'},{s:'LSE:SHEL',n:'Shell',market:'GB'},{s:'LSE:HSBA',n:'HSBC',market:'GB'}
 ],
 other:[
  {s:'NSE:NIFTY',n:'Nifty 50',unit:'index points',market:'IN'},{s:'TVC:UKX',n:'FTSE 100',unit:'index points',market:'GB'},{s:'SSE:000001',n:'Shanghai Composite',unit:'index points',market:'CN'},
  {s:'FX:EURUSD',n:'EUR / USD',market:'FX'},{s:'FX:USDINR',n:'USD / INR',market:'FX'},{s:'CRYPTO:BTCUSD',n:'Bitcoin / USD',market:'Crypto'},{s:'CRYPTO:ETHUSD',n:'Ether / USD',market:'Crypto'},{s:'CBOE:VIX',n:'VIX',unit:'index points',market:'US'}
 ]
};
var localFunds={US:[{s:'AMEX:VTI',n:'US total-market ETF',market:'US'}],IN:[{s:'NSE:NIFTYBEES',n:'Nifty 50 ETF',market:'IN'},{s:'NSE:SBINIFTY50',n:'SBI Nifty 50 ETF',market:'IN'},{s:'NSE:GOLDBEES',n:'Gold ETF',market:'IN'},{s:'NSE:LIQUIDBEES',n:'Liquid ETF',market:'IN'}],CN:[{s:'SSE:510300',n:'CSI 300 ETF',market:'CN'},{s:'SSE:510500',n:'CSI 500 ETF',market:'CN'}],GB:[{s:'LSE:VUSA',n:'S&P 500 UCITS ETF',market:'GB'},{s:'LSE:ISF',n:'FTSE 100 ETF',market:'GB'},{s:'LSE:IGLS',n:'Gilts ETF',market:'GB'}]};
var ipCountry='';
function symbolCountry(){return fetch('https://ipapi.co/country_code/',{cache:'force-cache'}).then(function(r){if(!r.ok)throw Error('region');return r.text();}).then(function(x){return String(x||'').trim().toUpperCase().slice(0,2);}).catch(function(){return '';});}
function priceText(v,cur,item){var n=Number(v);if(!isFinite(n))return '—';var d=Math.abs(n)<1?4:Math.abs(n)<100?2:2;var s=n.toLocaleString(undefined,{minimumFractionDigits:Math.abs(n)<1?Math.min(d,4):2,maximumFractionDigits:d});var p={USD:'$',INR:'₹',CNY:'CN¥',HKD:'HK$',GBP:'£',GBX:'GBp',USX:'US¢'}[cur]||'';if(item&&item.s==='TVC:US10Y')return s+'%';if(item&&item.unit)return s+' '+item.unit;if(item&&item.u)return p+s+' · '+item.u;return p+s+(cur?' '+(cur==='GBX'?'':''):'');}
function deltaText(v,cur,item){var n=Number(v);if(!isFinite(n))return '';var p={USD:'$',INR:'₹',CNY:'CN¥',HKD:'HK$',GBP:'£',GBX:'GBp',USX:'US¢'}[cur]||'';var q=(n>0?'+':'')+n.toLocaleString(undefined,{maximumFractionDigits:4});if(item&&item.s==='TVC:US10Y')return q+' pts';return (p?p+q:q);}
function makeQuote(item,row,country){var c=D.createElement('span');c.className='me-quote';if(item.market&&item.market===country)c.classList.add('is-local');var name=D.createElement('b');name.textContent=item.n;c.appendChild(name);var q=row&&row.d||[];if(row){var price=D.createElement('span');price.className='me-price';price.textContent=priceText(q[1],q[4],item);c.appendChild(price);var ch=Number(q[2]),abs=Number(q[3]);var delta=D.createElement('i');delta.className='me-change '+(ch>=0?'up':'down');delta.textContent=(ch>=0?'▲ ':'▼ ')+deltaText(abs,q[4],item)+' · '+(ch>=0?'+':'')+ch.toFixed(2)+'%';c.appendChild(delta);var sym=D.createElement('small');sym.textContent=item.s;c.appendChild(sym);}else{var note=D.createElement('small');note.className='me-noquote';note.textContent=item.note||'No quote returned by the connected feed.';c.appendChild(note);}return c;}
function paintTape(key,items,country,status){var track=D.getElementById('me-track-'+key),state=D.getElementById('me-state-'+key);if(!track)return;var rows={};var syms=items.filter(function(x){return x.s;}).map(function(x){return x.s;});var p={symbols:{tickers:syms},columns:['name','close','change','change_abs','currency']};fetch('https://scanner.tradingview.com/global/scan',{method:'POST',headers:{'Content-Type':'text/plain;charset=UTF-8'},body:JSON.stringify(p)}).then(function(r){if(!r.ok)throw Error('quote feed');return r.json();}).then(function(j){(j.data||[]).forEach(function(x){rows[x.s]=x;});track.innerHTML='';items.forEach(function(x){track.appendChild(makeQuote(x,x.s?rows[x.s]:null,country));});var htmlNodes=Array.prototype.slice.call(track.children);htmlNodes.forEach(function(x){var cl=x.cloneNode(true);cl.setAttribute('aria-hidden','true');track.appendChild(cl);});if(state){var t=new Date();state.textContent=(status||'')+' · Updated '+t.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})+' · source timing varies';}var wrap=D.getElementById('me-wrap-'+key);if(wrap&&!wrap.getAttribute('data-me-wired')){wrap.setAttribute('data-me-wired','1');marquee('me-wrap-'+key,'me-track-'+key,42);}}).catch(function(){if(state)state.textContent='Market feed did not respond · retrying';if(!track.children.length){track.innerHTML='';items.forEach(function(x){track.appendChild(makeQuote(x,null,country));});var nodes=Array.prototype.slice.call(track.children);nodes.forEach(function(x){var cl=x.cloneNode(true);cl.setAttribute('aria-hidden','true');track.appendChild(cl);});var wrap=D.getElementById('me-wrap-'+key);if(wrap&&!wrap.getAttribute('data-me-wired')){wrap.setAttribute('data-me-wired','1');marquee('me-wrap-'+key,'me-track-'+key,42);}}});}
function refreshTapes(){if(D.hidden)return;var country=ipCountry;var fundList=tapeGroups.funds.slice();if(localFunds[country])fundList=fundList.concat(localFunds[country]);var region={US:'United States',IN:'India',CN:'China',GB:'United Kingdom'}[country]||'global fallback';paintTape('commodities',tapeGroups.commodities,country,'Latest provider quote');paintTape('funds',fundList,country,'Global funds + '+region+' IP-country basket (approximate)');paintTape('equities',tapeGroups.equities,country,'Global watchlist · US · India · China · UK; '+(region==='global fallback'?'country lookup unavailable':region+' highlighted'));paintTape('other',tapeGroups.other,country,'Indices · currencies · digital assets · volatility');}
function refreshSpotBoard(){var root=D.getElementById('meSpotGrid');if(!root)return;var cards=root.querySelectorAll('[data-me-spot]'),symbols=Array.prototype.map.call(cards,function(x){return x.getAttribute('data-me-spot')});symbols.push('FX:USDINR');fetch('https://scanner.tradingview.com/global/scan',{method:'POST',headers:{'Content-Type':'text/plain;charset=UTF-8'},body:JSON.stringify({symbols:{tickers:symbols},columns:['name','description','close','change','change_abs','currency','update_mode']})}).then(function(r){if(!r.ok)throw Error('spot feed');return r.json()}).then(function(j){var rows={};(j.data||[]).forEach(function(x){rows[x.s]=x.d||[]});var fx=Number((rows['FX:USDINR']||[])[2]);Array.prototype.forEach.call(cards,function(card){var s=card.getAttribute('data-me-spot'),d=rows[s],price=card.querySelector('.me-spot-price'),change=card.querySelector('.me-spot-change'),inr=card.querySelector('.me-spot-inr');if(!d||!isFinite(Number(d[2]))){price.textContent='Quote unavailable';change.textContent='No value returned by the connected public feed.';inr.hidden=true;return}var v=Number(d[2]),cur=d[5]||'USD',pct=Number(d[3]);price.textContent=(cur==='USD'?'$':cur+' ')+v.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:4})+' / '+card.getAttribute('data-me-unit');change.textContent=(pct>=0?'▲ +':'▼ ')+pct.toFixed(2)+'% · '+(d[6]||'provider timing varies');change.className='me-spot-change '+(pct>=0?'up':'down');if(cur==='USD'&&fx>0&&card.getAttribute('data-me-unit')==='troy oz'){inr.textContent='Indicative ₹/g '+(v*fx/31.1034768).toLocaleString('en-IN',{maximumFractionDigits:2})+' · reference conversion only';inr.hidden=false}else inr.hidden=true});var stamp=D.getElementById('meSpotUpdated');if(stamp)stamp.textContent='Provider values retrieved '+new Date().toLocaleString()+' · CFD reference quotes, not physical or retail prices.'}).catch(function(){Array.prototype.forEach.call(cards,function(card){card.querySelector('.me-spot-price').textContent='Quote unavailable';card.querySelector('.me-spot-change').textContent='The public quote feed did not respond; please retry later.';card.querySelector('.me-spot-inr').hidden=true});var stamp=D.getElementById('meSpotUpdated');if(stamp)stamp.textContent='No spot-reference values were returned. This board does not substitute futures or related instruments.'});}
symbolCountry().then(function(code){ipCountry=code;refreshTapes();});refreshTapes();refreshSpotBoard();setInterval(refreshTapes,60000);setInterval(refreshSpotBoard,60000);
"""


def main() -> None:
    theme = SOURCE.read_text(encoding="utf-8")
    # Leave provider-search status under the search module, not the generic form handler.
    theme = theme.replace("D.querySelectorAll('form').forEach(function(f){var s=f.querySelector('.dy-form-status');", "D.querySelectorAll('form').forEach(function(f){if(f.id==='dywSearchForm')return;var s=f.querySelector('.dy-form-status');")
    theme = theme.replace("ph.textContent='DY';", "ph.textContent='ME';").replace("fallback.textContent='DY';", "fallback.textContent='ME';")
    # Remove the unwanted personal byline from the masthead and footer.
    theme = theme.replace("<span class='tb-line'><span class='tb-b' id='tbType'>By Kushal Kumar Daga</span><span aria-hidden='true' class='tb-caret'/><svg aria-hidden='true' class='tb-squig' viewBox='0 0 92 8'><path d='M2 6c12-6 24 4 36-1s26-5 52 1'/></svg></span>", "")
    theme = theme.replace("<span class='ft-by'>By Kushal Kumar Daga</span><p class='ft-legal'>Published by MILLED EDGE. Written by Kushal Kumar Daga, the short form of the publisher&#39;s legal name, Kushal Kumar Daga, which is the name used on ownership, payment and platform records.</p>", "<p class='ft-legal'>Published by MILLED EDGE. Publisher and contact details are available on the About and Contact pages.</p>")
    # Remove the obsolete masthead typewriter and its author-name string.
    old_typewriter = """/* brand typing loop */
(function(){
 var el = document.getElementById('tbType');
 if (!el) return;
 var W = 'By Kushal Kumar Daga';
 if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches){ el.textContent = W; return; }
 el.textContent = W;
 var sq = document.querySelector('.tb-squig path');
 var i = W.length, del = true, hold = 46;
 function redraw(){ if (!sq) return; sq.style.animation = 'none'; void sq.getBoundingClientRect(); sq.style.animation = ''; }
 setInterval(function(){
 if (!del){ i++; el.textContent = W.slice(0, i); if (i >= W.length){ del = true; hold = 46; redraw(); } }
 else { if (hold > 0){ hold--; } else { i--; el.textContent = W.slice(0, i); if (i <= 0){ del = false; hold = 10; } } }
 }, 110);
})();"""
    theme = theme.replace(old_typewriter, "/* Removed: personal-name masthead byline. */")
    # Rebrand the loader and inherited Daily Yield favicon artwork.
    theme = theme.replace("<b>DY</b>", "<b>ME</b>")
    theme = theme.replace("Daily%20Yield%20logo", "MILLED%20EDGE%20logo")
    theme = theme.replace("if(u.href===location.href)return;e.preventDefault();", "if(u.href===location.href)return;if(u.origin===location.origin&&u.pathname===location.pathname&&u.hash)return;e.preventDefault();")
    theme = theme.replace("%3ED%3C%2Ftext%3E", "%3EM%3C%2Ftext%3E").replace("%3EY%3C%2Ftext%3E", "%3EE%3C%2Ftext%3E")
    if "<b:skin><![CDATA[" not in theme or "KC-HOME-DESK v1" not in theme:
        raise SystemExit("Source theme does not match expected base")
    # Retired page routes become anchors in the refreshed homepage.
    theme = theme.replace(BLOG + "/p/markets-today.html", BLOG + "/#me-live-tapes")
    theme = theme.replace(BLOG + "/p/global-snapshot.html", BLOG + "/#me-category-directory")
    theme = theme.replace("/p/markets-today.html", "/#me-live-tapes")
    theme = theme.replace("/p/global-snapshot.html", "/#me-category-directory")
    theme = theme.replace("Markets<br/>Today", "Live<br/>Markets")
    theme = theme.replace("Global<br/>Snapshot", "95<br/>Categories")
    old_pair = """ <li><a class='kd-n1' href='https://millededgeindia.blogspot.com/#me-live-tapes'><b aria-hidden='true'/><span>Live<br/>Markets</span><em aria-hidden='true'/></a></li>
 <li><a class='kd-n1' href='https://millededgeindia.blogspot.com/#me-category-directory'><b aria-hidden='true'/><span>95<br/>Categories</span><em aria-hidden='true'/></a></li>"""
    new_button = " <li><button aria-controls='meMarketPanel' aria-expanded='false' class='kd-n1 me-market-trigger' id='meMarketToggle' type='button'><b aria-hidden='true'/><span>Market<br/>Today</span><em aria-hidden='true'/></button></li>"
    if old_pair not in theme:
        raise SystemExit("Could not locate the two market navigation buttons to replace")
    theme = theme.replace(old_pair, new_button, 1)
    nav_rows = " </ul>\n <ul class='tabs kd-r2'>"
    if nav_rows not in theme:
        raise SystemExit("Could not locate the two navigation rows")
    panel_script = market_today_menu() + "\n<script>//<![CDATA[\n(function(){var paths=" + json.dumps([u.split('.com', 1)[1] for slug,u in _post_urls().items() if slug.startswith('commodities-')]) + ";if(paths.indexOf(location.pathname)>=0)location.replace('/#me-commodity-board');})();\n//]]></script>\n<script>//<![CDATA[\n(function(){var b=document.getElementById('meMarketToggle'),p=document.getElementById('meMarketPanel'),nav=document.querySelector('#page_list_top .kd-nav');if(!b||!p||!nav)return;function close(){p.hidden=true;b.setAttribute('aria-expanded','false');}b.addEventListener('click',function(){var open=p.hidden;p.hidden=!open;b.setAttribute('aria-expanded',String(open));});document.addEventListener('click',function(e){if(!nav.contains(e.target))close();});document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!p.hidden){close();b.focus();}});p.querySelectorAll('[data-me-menu-division]').forEach(function(d){var hovering=false,summary=d.querySelector('summary');d.addEventListener('pointerenter',function(e){if(e.pointerType==='mouse'||e.pointerType==='pen'){hovering=true;d.open=true;}});d.addEventListener('pointerleave',function(e){if(e.pointerType==='mouse'||e.pointerType==='pen'){hovering=false;d.open=false;}});if(summary)summary.addEventListener('click',function(e){if(hovering){e.preventDefault();d.open=true;}});});})();\n//]]></script>"
    theme = theme.replace(nav_rows, " </ul>\n " + panel_script + "\n <ul class='tabs kd-r2'>", 1)
    theme = theme.replace("Markets Today", "Live Market Tapes")
    theme = theme.replace("markets today", "live market tapes")
    theme = theme.replace("Global Snapshot", "Market Explorer")
    theme = theme.replace("global snapshot", "market explorer")
    theme = theme.replace("MILLED EDGE publishes finance news, practical money guides, market insights and transparent calculations, written by Kushal Kumar Daga. Contact kushalkumardaga.ca@gmail.com.", "MILLED EDGE offers financial education, practical calculators and 95 active category routes across 18 divisions, with sources and data timing made clear.")
    theme = theme.replace("aria-label='Market Explorer' class='fab'", "aria-label='95 Market Categories' class='fab'")
    theme = theme.replace("data-tip='Market Explorer'", "data-tip='95 Market Categories'")
    theme = theme.replace("title='Market Explorer'", "title='95 Market Categories'")
    theme = theme.replace("<b>Markets Today</b>", "<b>Live Market Tapes</b>")
    theme = theme.replace("<b>Global Snapshot</b>", "<b>95 Market Categories</b>")
    theme = theme.replace("<span><b>Global Snapshot</b><i>boards &#183; commodities &#183; crypto</i></span>", "<span><b>Market Explorer</b><i>18 divisions · 104 categories</i></span>")
    theme = theme.replace("<span class='kd-eg-fine'>Replies usually arrive within 2&#8211;3 working days &#183; comments remain open on every Post</span>", "<span class='kd-eg-fine'>Corrections and questions go to one editorial inbox; responses depend on capacity.</span>")
    # Swap the old single pulse strip for the commodity tape above the hero.
    old_top = " <div aria-label='Live market pulse' class='kh-pulse' id='khPulse'><span class='kh-plab'>market pulse</span><div class='kh-ptrack' id='khPTrack'><span class='kh-pchip kh-pwait'>connecting to live boards&#8230;</span></div></div>"
    if old_top not in theme:
        raise SystemExit("Could not locate the existing top market-pulse strip")
    theme = theme.replace(old_top, tape("Precious metals · spot references", "commodities", "Gold · silver · platinum · palladium. Global CFD reference quotes are distinct from local physical or retail prices.", "Waiting for precious-metal reference quotes") + commodity_board(), 1)
    # Add the post-hero fund tape after the hero's local script.
    hero_end = " </script>\n <div class='kd-tabswrap' id='kdDeskWrap'>"
    if hero_end not in theme:
        raise SystemExit("Could not locate the homepage hero end")
    theme = theme.replace(hero_end, " </script>\n" + tape("Funds, ETFs, index funds & bonds", "funds", "Global funds plus an approximate IP-country exchange basket. Bond yields and ETF prices are not the same measure; mutual-fund NAVs usually update on provider schedules.", "Waiting for fund and bond quotes") + "\n <div class='kd-tabswrap' id='kdDeskWrap'>", 1)
    # Add the wider market tape after the news wire, and the 104-route directory.
    news_end = "</section>\n<section class='kd-sec' id='kd-tools'>"
    if news_end not in theme:
        raise SystemExit("Could not locate the news wire section")
    theme = theme.replace(news_end, "</section>\n" + tape("Other market divisions", "other", "Indices · foreign exchange · digital assets · volatility; a cross-asset view, not a recommendation.", "Waiting for cross-asset quotes") + "\n" + category_directory() + "\n<section class='kd-sec' id='kd-tools'>", 1)
    # Add equities after the working calculators.
    calc_end = "</section>\n<section class='kd-sec kd-legal' id='kd-legal'>"
    if calc_end not in theme:
        raise SystemExit("Could not locate the end of the home calculator bench")
    theme = theme.replace(calc_end, "</section>\n" + tape("Global and country equity watchlists", "equities", "Large-cap examples from global markets and the US, India, China and UK. Listed companies are a watchlist, not a live market-cap ranking.", "Waiting for equity quotes") + "\n<section class='kd-sec kd-legal' id='kd-legal'>", 1)
    # Add About-derived context and all seven profiles from the Contact page.
    about_end = "</section>\n<section class='kd-sec' id='kd-news'>"
    if about_end not in theme:
        raise SystemExit("Could not locate the About section")
    theme = theme.replace(about_end, "</section>\n" + social_about() + "\n<section class='kd-sec' id='kd-news'>", 1)
    # Replace legacy live-market code, retaining the small calculator helper below it.
    begin = "/* ---------- KC-HOME-V3: market pulse (60s) + home calculator bench ---------- */"
    stop = " function num(id){"
    a, b = theme.find(begin), theme.find(stop, theme.find(begin))
    if a < 0 or b < 0:
        raise SystemExit("Could not isolate the legacy market-pulse engine")
    theme = theme[:a] + " (function(){\n" + ticker_script() + theme[b:]
    # Add styles before the Blogger skin CDATA closes.
    css = r"""
/* MARKET TODAY navigation: six columns x three divisions, expands between nav rows */
#page_list_top .me-market-trigger{font:inherit;color:inherit;cursor:pointer;text-align:left;appearance:none;-webkit-appearance:none;}
#page_list_top .me-market-trigger span{color:#241610;}
#page_list_top .me-market-trigger:focus-visible,#page_list_top .me-menu-division summary:focus-visible{outline:3px solid #bc5b33;outline-offset:3px;}
.me-market-panel{width:min(1240px,calc(100% - 28px));max-height:72vh;overflow:auto;margin:8px auto 12px;padding:12px;background:#fffaf0;border:1px solid #e6d3b4;border-radius:18px;box-shadow:0 20px 48px -28px rgba(36,22,16,.48);animation:meMarketOpen .32s cubic-bezier(.22,.7,.3,1) both;}
.me-market-panel[hidden]{display:none!important;}
@keyframes meMarketOpen{from{opacity:0;transform:translateY(-10px) scale(.985)}to{opacity:1;transform:none}}
.me-market-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;align-items:start;}
.me-menu-commodity{min-width:0;min-height:42px;display:grid;grid-template-columns:auto 1fr;align-items:center;gap:5px 7px;padding:8px;border:1px solid #bc5b33;border-radius:11px;background:#fff2e7;color:#241610;text-decoration:none;transition:transform .25s,box-shadow .25s;}.me-menu-commodity:hover{transform:translateY(-2px);box-shadow:0 8px 18px -14px rgba(36,22,16,.7)}.me-menu-commodity .me-menu-go{grid-column:2;color:#9c4522;font:700 8px/1.2 Inter,Arial,sans-serif}.me-menu-pending,.me-pending{color:#89765c;font:500 9px/1.35 Inter,Arial,sans-serif}.me-menu-pending small{display:block;margin-top:2px;font-size:7px}.me-division.me-commodity-link{display:flex;align-items:stretch}.me-commodity-link>a{display:flex;align-items:center;gap:8px;width:100%;padding:12px;color:inherit;text-decoration:none}.me-commodity-link .me-div-title{flex:1}.me-spot-board{max-width:1280px;margin:16px auto;padding:clamp(16px,3vw,28px);border:1px solid #eadcc8;border-radius:20px;background:linear-gradient(135deg,#fffaf0,#f6e8d3);box-sizing:border-box}.me-spot-head{max-width:900px;margin:0 auto 16px;text-align:center}.me-spot-head h2{margin:5px 0 8px;color:#241610;font:800 clamp(23px,3vw,34px)/1.2 'Playfair Display',Georgia,serif}.me-spot-head p,.me-spot-foot{margin:0 auto;color:#6e5d4b;font:500 11px/1.65 Inter,Arial,sans-serif}.me-spot-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.me-spot-card{min-width:0;display:flex;flex-direction:column;gap:7px;padding:15px;border:1px solid #eadcc8;border-radius:13px;background:#fffdf8}.me-spot-card>span{color:#a34e2c;font:800 8px/1.3 Inter,Arial,sans-serif;letter-spacing:.16em}.me-spot-card h3{margin:0;color:#241610;font:700 17px/1.2 'Playfair Display',Georgia,serif}.me-spot-price{font:800 clamp(16px,2vw,22px)/1.2 Inter,Arial,sans-serif;font-variant-numeric:tabular-nums}.me-spot-change,.me-spot-inr{color:#6e5d4b;font:600 9px/1.45 Inter,Arial,sans-serif}.me-spot-change.up{color:#147449}.me-spot-change.down{color:#b13737}.me-spot-foot{margin-top:12px;font-size:9px;text-align:center}
.me-menu-division{min-width:0;border:1px solid #eadcc8;border-radius:11px;background:#fffdf8;overflow:visible;}
.me-menu-division>summary{min-height:42px;display:flex;align-items:center;gap:6px;padding:8px;list-style:none;cursor:pointer;}
.me-menu-division>summary::-webkit-details-marker{display:none;}
.me-menu-num{flex:none;color:#a34e2c;font:800 9px/1 Inter,Arial,sans-serif;}
.me-menu-title{flex:1;min-width:0;color:#241610;font:700 11px/1.25 'Playfair Display',Georgia,serif;text-align:left;}
.me-menu-count{flex:none;color:#89765c;font:700 8px/1 Inter,Arial,sans-serif;}
.me-menu-cats{display:grid;grid-template-rows:0fr;opacity:0;transform:translateY(-5px);transition:grid-template-rows .3s ease,opacity .24s ease,transform .3s ease;}
.me-menu-division[open] .me-menu-cats{grid-template-rows:1fr;opacity:1;transform:none;}
.me-menu-cats-inner{min-height:0;overflow:hidden;}
.me-menu-cats ul{display:grid;gap:4px;list-style:none;margin:0;padding:0 8px 9px;}
.me-menu-cats a{display:block;padding:4px 5px;border-radius:6px;color:#795b3b;text-decoration:none;font:500 9px/1.3 Inter,Arial,sans-serif;}
.me-menu-cats a:hover{background:#f6e8d3;color:#9c4522;text-decoration:underline;}
@media(max-width:900px){.me-market-grid{grid-template-columns:repeat(3,minmax(0,1fr));}}
@media(max-width:560px){.me-market-panel{width:calc(100% - 16px);padding:8px;max-height:68vh}.me-market-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.me-menu-division>summary{padding:7px;min-height:46px}.me-menu-title{font-size:10px}}
@media(max-width:360px){.me-market-grid{grid-template-columns:1fr;}}
@media(prefers-reduced-motion:reduce){.me-market-panel,.me-menu-cats{animation:none!important;transition:none!important}}
/* 104-category homepage: live tapes, category explorer, author and social links */
.kv-btn.dark,.kv-btn.light{background:var(--ink)!important;color:#F8F0E3!important;border-color:var(--ink)!important}.kv-btn.dark:hover,.kv-btn.light:hover{background:var(--accent-dark)!important;border-color:var(--accent-dark)!important;color:#fff!important}
.me-tape,.me-directory,.me-about-panel{max-width:1280px;margin:18px auto;padding:16px clamp(14px,3vw,28px);box-sizing:border-box}
.me-tape{background:linear-gradient(115deg,#fffaf0,#f6e8d3);border:1px solid #e8d7bb;border-radius:18px;box-shadow:0 14px 30px -26px rgba(36,22,16,.42);overflow:hidden}
.me-tape-head{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin-bottom:10px}
.me-tape-head h2,.me-directory-head h2,.me-about-panel h2{font:800 clamp(20px,2.8vw,28px)/1.18 'Playfair Display',Georgia,serif;color:#241610;margin:4px 0}
.me-tape-head p,.me-directory-head p,.me-about-panel p{font:400 12px/1.65 Inter,Arial,sans-serif;color:#6e5d4b;margin:0;max-width:780px}
.me-kicker{display:block;font:800 9px/1.4 Inter,Arial,sans-serif;letter-spacing:.22em;color:#a34e2c;text-transform:uppercase}
.me-tape-state{flex:0 0 auto;color:#806a50;font:600 10px/1.5 Inter,Arial,sans-serif;text-align:right}
.me-tape-window{position:relative;overflow:hidden;touch-action:pan-y;user-select:none;-webkit-user-select:none}
.me-tape-window::before,.me-tape-window::after{content:"";position:absolute;z-index:2;top:0;bottom:0;width:28px;pointer-events:none}
.me-tape-window::before{left:0;background:linear-gradient(90deg,#fff9ef,transparent)}.me-tape-window::after{right:0;background:linear-gradient(270deg,#f8ecd9,transparent)}
.me-tape-track{display:flex;align-items:stretch;gap:9px;width:max-content;will-change:transform;padding:4px 8px 8px}
.me-quote{flex:0 0 auto;min-width:150px;max-width:225px;display:flex;flex-direction:column;gap:4px;padding:10px 12px;background:#fffdf8;border:1px solid #eadcc8;border-radius:12px;color:#241610;font:600 11px/1.35 Inter,Arial,sans-serif;font-variant-numeric:tabular-nums}
.me-quote.is-local{border-color:#bc5b33;box-shadow:inset 0 0 0 1px rgba(188,91,51,.14)}
.me-quote>b{font:800 10px/1.3 Inter,Arial,sans-serif;letter-spacing:.04em;color:#5d4934}.me-price{font:800 15px/1.25 'Playfair Display',Georgia,serif;white-space:nowrap}.me-change{font:800 10px/1.3 Inter,Arial,sans-serif;font-style:normal;white-space:nowrap}.me-change.up{color:#147449}.me-change.down{color:#b13737}.me-quote small{font:500 8px/1.3 Inter,Arial,sans-serif;color:#8c7a64;letter-spacing:.06em}.me-quote .me-noquote{font:500 9px/1.45 Inter,Arial,sans-serif;white-space:normal;max-width:190px}.me-quote-wait{min-width:220px;color:#8c7a64}
.me-directory{padding-top:26px;padding-bottom:28px}.me-directory-head{text-align:center;margin:0 auto 18px;max-width:820px}.me-directory-head .me-directory-all{display:inline-block;margin-top:12px;padding:9px 14px;border-radius:999px;background:#bc5b33;color:#fffdf8;text-decoration:none;font:700 10px/1.4 Inter,Arial,sans-serif}.me-division-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}.me-division{border:1px solid #eadcc8;border-radius:12px;background:#fffdf8;overflow:hidden}.me-division summary{display:flex;align-items:center;gap:8px;list-style:none;cursor:pointer;padding:12px;min-height:42px}.me-division summary::-webkit-details-marker{display:none}.me-div-num{font:800 9px/1 Inter,Arial,sans-serif;color:#bc5b33}.me-div-title{flex:1;font:700 12px/1.3 'Playfair Display',Georgia,serif;color:#241610}.me-div-count{font:700 8px/1.3 Inter,Arial,sans-serif;color:#89765c;white-space:nowrap}.me-division ul{list-style:none;margin:0;padding:0 12px 10px;display:grid;grid-template-columns:1fr 1fr;gap:5px 8px}.me-division li a{font:500 9px/1.35 Inter,Arial,sans-serif;color:#795b3b;text-decoration:none}.me-division li a:hover{text-decoration:underline;color:#9c4522}
.me-about-panel{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(260px,.8fr);gap:24px;align-items:center;padding:clamp(20px,3vw,34px);background:#fffdf8;border:1px solid #eadcc8;border-radius:20px}.me-about-actions,.me-social-links{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}.me-about-actions a,.me-social-links a{padding:8px 11px;border:1px solid #e6d3b4;border-radius:999px;background:#faf3e7;color:#8f4829;text-decoration:none;font:700 10px/1.25 Inter,Arial,sans-serif}.me-social h3{font:700 15px/1.3 'Playfair Display',Georgia,serif;color:#241610;margin:0}.me-social p{font-size:10px;margin-top:10px}
@media(max-width:760px){.me-spot-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.me-tape-head{align-items:flex-start;flex-direction:column;gap:5px}.me-tape-state{text-align:left}.me-division-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.me-about-panel{grid-template-columns:1fr;gap:18px}.me-quote{min-width:138px}}
@media(max-width:460px){.me-spot-grid{grid-template-columns:1fr 1fr}.me-division-grid{grid-template-columns:1fr}.me-tape{margin:12px auto;padding:13px 10px}.me-division ul{grid-template-columns:1fr 1fr}.me-about-panel{margin:16px 10px}}
@media(prefers-reduced-motion:reduce){.me-tape-track{transform:none!important}}
"""
    close = "]]></b:skin>"
    if close not in theme:
        raise SystemExit("Could not locate Blogger skin close")
    theme = theme.replace(close, css + "\n" + close, 1)
    # Update legacy tool/search descriptors to the new homepage destinations.
    theme = theme.replace("Markets Today — live prices, charts and technicals", "Live market tapes — prices, changes and data timing")
    theme = theme.replace("Global Snapshot — concise cross-asset summary", "104-category market directory — 18 divisions")
    theme = theme.replace("Global share board", "Global and country equity watchlists")
    theme = theme.replace("Gold & silver prices", "Commodities market tape")
    theme = "\n".join(line.rstrip() for line in theme.splitlines()) + "\n"
    OUTPUT.write_text(theme, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(theme):,} characters)")
    if len(json.loads((ROOT / "content/market-posts/batch-1-catalog.json").read_text())) + sum(len(json.loads((ROOT / f"content/market-posts/batch-{n}-catalog.json").read_text())) for n in range(2, 6)) != 104:
        raise SystemExit("Category catalog does not contain 104 routes")
    for forbidden in ("/p/markets-today.html", "/p/global-snapshot.html"):
        if forbidden in theme:
            raise SystemExit(f"Retired route remains in new theme: {forbidden}")
    if theme.count("class='me-tape'") != 4:
        raise SystemExit("Homepage must include exactly four live market tapes")
    if "id='me-commodity-board'" not in theme or "TVC:PALLADIUM" not in theme:
        raise SystemExit("Dedicated commodity spot-reference board is missing")
    if theme.count("data-me-menu-division='true'") != 17 or theme.count("class='me-menu-commodity'") != 1 or theme.count("id='meMarketToggle'") != 1:
        raise SystemExit("Market Today navigation must contain one toggle, 17 category divisions, and one commodity-board route")
    if "id='meMarketPanel'" not in theme or "class='tabs kd-r2'" not in theme:
        raise SystemExit("Market Today panel or second navigation row is missing")
    if "Live<br/>Markets" in theme or "95<br/>Categories" in theme:
        raise SystemExit("Obsolete separate market navigation buttons remain")


if __name__ == "__main__":
    main()
