"""Build the transparent category-aware Top 50,000 market directory.

The TradingView scanner is the same public global directory already used by the
Market Today page. Rows are ranked *within category* using a visible public
proxy (market capitalization or reported volume), then interleaved so a single
asset class does not occupy every opening position. This is not a universal
web-search-volume ranking.

Run from the repository root:
    python scripts/build_markets_rankings.py
"""
from __future__ import annotations

import datetime as dt
import html
import json
import math
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "market-data" / "top-50000.json"
POST_OUT = ROOT / "content" / "posts" / "top-5000-market-instruments.html"
TV_URL = "https://scanner.tradingview.com/global/scan"
CG_TREND_URL = "https://api.coingecko.com/api/v3/search/trending"
AS_OF = dt.datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
CHUNK = 5000

MAJOR_CRYPTO_EXCHANGES = [
    "BINANCE", "COINBASE", "BYBIT", "OKX", "KRAKEN", "KUCOIN", "BITSTAMP",
    "BITFINEX", "UPBIT", "GATEIO", "MEXC", "BITGET", "HTX", "CRYPTOCOM",
    "BINGX", "POLONIEX", "GEMINI", "WHITEBIT", "BITMART", "COINEX",
    "PHEMEX", "DERIBIT", "BITPANDA", "BITVAVO", "KRAKENFUTURES",
]

# Exact quotas sum to 50,000. They deliberately preserve broad asset coverage;
# ranks are comparable only inside each category, not across unlike asset types.
CATEGORIES = [
    {
        "id": "stocks", "label": "Stocks & shares", "limit": 19375,
        "filters": [
            {"left": "type", "operation": "equal", "right": "stock"},
            {"left": "is_primary", "operation": "equal", "right": True},
        ],
        "sort_by": "market_cap_basic", "sort_order": "desc",
        "metric": "Market capitalization, descending",
    },
    {
        "id": "funds", "label": "Funds, ETFs & REITs", "limit": 10000,
        "filters": [{"left": "type", "operation": "equal", "right": "fund"}],
        "sort_by": "volume", "sort_order": "desc",
        "metric": "Reported trading volume, descending",
    },
    {
        "id": "bonds", "label": "Bonds", "limit": 8000,
        "filters": [{"left": "type", "operation": "equal", "right": "bond"}],
        "sort_by": "volume", "sort_order": "desc",
        "metric": "Reported trading volume, descending",
    },
    {
        "id": "futures", "label": "Futures & commodities", "limit": 6000,
        "filters": [{"left": "type", "operation": "equal", "right": "futures"}],
        "sort_by": "volume", "sort_order": "desc",
        "metric": "Reported contract volume, descending",
    },
    {
        "id": "crypto", "label": "Cryptocurrency markets", "limit": 4000,
        "filters": [
            {"left": "type", "operation": "equal", "right": "spot"},
            {"left": "subtype", "operation": "equal", "right": "crypto"},
            {"left": "exchange", "operation": "in_range", "right": MAJOR_CRYPTO_EXCHANGES},
        ],
        "sort_by": "volume", "sort_order": "desc",
        "metric": "Reported exchange trading volume, descending; CoinGecko trend signal is annotated where matched",
    },
    {
        "id": "forex", "label": "Forex & currency pairs", "limit": 2000,
        "filters": [{"left": "type", "operation": "equal", "right": "forex"}],
        "sort_by": "volume", "sort_order": "desc",
        "metric": "Reported currency-pair volume, descending",
    },
    {
        "id": "indices", "label": "World indices", "limit": 625,
        "filters": [{"left": "type", "operation": "equal", "right": "index"}],
        "sort_by": "volume", "sort_order": "desc",
        "metric": "Reported market activity where available; otherwise provider directory order",
    },
]

COLUMNS = [
    "name", "description", "exchange", "type", "subtype", "country",
    "volume", "market_cap_basic", "close", "currency",
]

EXCHANGE_COUNTRY = {
    "NSE": "India", "BSE": "India", "MCX": "India", "NCDEX": "India",
    "NASDAQ": "United States", "NYSE": "United States", "AMEX": "United States",
    "CME": "United States", "CBOT": "United States", "NYMEX": "United States",
    "COMEX": "United States", "ICEUS": "United States", "CBOE": "United States",
    "LSE": "United Kingdom", "LSEETF": "United Kingdom", "EURONEXT": "Europe",
    "SSE": "China", "SZSE": "China", "HKEX": "Hong Kong", "HKEX": "Hong Kong",
    "TSE": "Japan", "JPX": "Japan", "OSE": "Japan", "KRX": "South Korea",
    "ASX": "Australia", "TSX": "Canada", "TSXV": "Canada", "B3": "Brazil",
    "SGX": "Singapore", "IDX": "Indonesia", "ADX": "United Arab Emirates",
    "DFM": "United Arab Emirates", "TADAWUL": "Saudi Arabia", "SIX": "Switzerland",
    "XETR": "Germany", "FWB": "Germany", "MIL": "Italy", "BME": "Spain",
    "Euronext": "Europe",
}


def request_json(url: str, payload: dict[str, Any] | None = None, *, attempts: int = 5) -> Any:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "User-Agent": "MilledEdgeMarketDirectory/1.0 (public market directory)",
        "Accept": "application/json",
    }
    if payload is not None:
        headers.update({
            "Content-Type": "text/plain;charset=UTF-8",
            "Origin": "https://www.tradingview.com",
        })
    for attempt in range(attempts):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            if attempt + 1 == attempts:
                raise RuntimeError(f"Public data request failed for {url}: {exc}") from exc
            time.sleep(min(2 ** attempt, 12))
    raise RuntimeError("unreachable")


def number_or_none(value: Any) -> float | None:
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def simple_name(formal: str, kind: str, subtype: str, symbol: str) -> str:
    text = (formal or symbol).strip()
    aliases = {
        "Gold": "Gold", "Silver": "Silver", "Platinum": "Platinum",
        "Palladium": "Palladium", "WTI crude oil": "WTI crude oil",
        "Brent crude oil": "Brent crude oil", "Natural gas": "Natural gas",
        "Copper": "Copper", "Bitcoin": "Bitcoin", "Ethereum": "Ethereum",
        "NVIDIA Corporation": "NVIDIA", "Apple Inc.": "Apple",
        "Microsoft Corporation": "Microsoft", "Amazon.com, Inc.": "Amazon",
        "Alphabet Inc. Class A": "Alphabet", "Meta Platforms, Inc.": "Meta",
    }
    if text in aliases:
        return aliases[text]
    # Remove common legal suffixes and technical share-class wording while
    # keeping the instrument's identifying name intact.
    import re
    name = re.sub(r"\b(Class\s+[A-Z0-9]+|Common Stock|Ordinary Shares?|Common Shares?)\b", "", text, flags=re.I)
    name = re.sub(r"\b(Incorporated|Inc|Corporation|Corp|Limited|Ltd|PLC|Company|Co|Holdings|Holding|Group|S\.A\.|N\.V\.|A\.G\.|S\.E\.)\.?\b", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name).strip(" ,.-") or text
    k, st = (kind or "").lower(), (subtype or "").lower()
    if k == "bond":
        return name
    if k == "index":
        return re.sub(r"\s+Index$", "", name, flags=re.I) or name
    if k == "forex":
        return name.replace(" vs ", " / ")
    if k == "futures":
        return name
    if k == "fund" and st == "etf" and not name.upper().endswith(" ETF"):
        return name
    return name


def tv_rows(category: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    total_count = 0
    start = 0
    while len(result) < category["limit"]:
        end = min(start + CHUNK, category["limit"] + 2000)
        payload = {
            "filter": category["filters"],
            "options": {"lang": "en"},
            "symbols": {"query": {"types": []}, "tickers": []},
            "columns": COLUMNS,
            "sort": {"sortBy": category["sort_by"], "sortOrder": category["sort_order"]},
            "range": [start, end],
        }
        body = request_json(TV_URL, payload)
        total_count = int(body.get("totalCount", 0))
        rows = body.get("data", [])
        if not rows:
            break
        for row in rows:
            symbol = str(row.get("s") or "").strip()
            d = row.get("d") or []
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)
            name = str(d[0] or symbol)
            formal = str(d[1] or name)
            kind = str(d[3] or "instrument")
            subtype = str(d[4] or "")
            exchange = str(d[2] or "")
            result.append({
                "symbol": symbol,
                "formalName": formal,
                "commonName": simple_name(formal, kind, subtype, name),
                "exchange": exchange,
                "type": kind,
                "subtype": subtype,
                "country": str(d[5] or EXCHANGE_COUNTRY.get(exchange, "Global")),
                "volume": number_or_none(d[6]),
                "marketCap": number_or_none(d[7]),
                "close": number_or_none(d[8]),
                "currency": str(d[9] or ""),
                "category": category["id"],
                "categoryLabel": category["label"],
                "categoryRank": len(result) + 1,
                "rankMetric": category["metric"],
                "source": "TradingView Global Scanner",
                "asOf": AS_OF,
            })
            if len(result) >= category["limit"]:
                break
        if len(rows) < end - start or start >= total_count:
            break
        start = end
        time.sleep(0.12)
    if len(result) < category["limit"]:
        raise RuntimeError(
            f"{category['label']} returned only {len(result):,} unique rows; "
            f"required {category['limit']:,}. No output was written."
        )
    return result[:category["limit"]], total_count


def coingecko_trending() -> list[dict[str, Any]]:
    try:
        body = request_json(CG_TREND_URL)
        out = []
        for pos, record in enumerate(body.get("coins", []), 1):
            item = record.get("item", {})
            out.append({
                "rank": pos,
                "id": item.get("id", ""),
                "symbol": str(item.get("symbol", "")).upper(),
                "name": item.get("name", ""),
                "marketCapRank": item.get("market_cap_rank"),
                "source": "CoinGecko Trending Search",
                "metric": "CoinGecko platform searches, last 24 hours",
                "asOf": AS_OF,
            })
        return out
    except Exception as exc:
        print(f"Warning: CoinGecko trend overlay unavailable: {exc}")
        return []


def annotate_crypto(crypto: list[dict[str, Any]], signals: list[dict[str, Any]]) -> None:
    # This signal is explicitly platform-specific; it supplements, rather than
    # masquerades as, a worldwide search-volume count.
    for item in crypto:
        item["trendSignal"] = None
    for signal in signals:
        name = str(signal.get("name", "")).casefold()
        ticker = str(signal.get("symbol", "")).upper()
        candidates = []
        for item in crypto:
            sym = item["symbol"].split(":", 1)[-1].upper()
            formal = item["formalName"].casefold()
            if (name and name in formal) or (ticker and (sym.startswith(ticker) or f"/{ticker}" in formal)):
                candidates.append(item)
        if candidates:
            candidates.sort(key=lambda x: (x.get("volume") or 0), reverse=True)
            candidates[0]["trendSignal"] = signal


def html_row(item: dict[str, Any]) -> str:
    vals = [
        str(item["categoryRank"]),
        f"<b>{html.escape(item['symbol'].upper())}</b><br><small>{html.escape(item['type'].upper())}</small>",
        html.escape(item["formalName"]),
        html.escape(item["commonName"]),
        html.escape(item["country"] or "Global"),
        html.escape(item["exchange"] or "Global"),
    ]
    return "<tr>" + "".join(f"<td>{v}</td>" for v in vals) + "</tr>"


def build_post(entries: list[dict[str, Any]], metadata: dict[str, Any], trends: list[dict[str, Any]]) -> str:
    top = entries[:5000]
    categories: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for overall_rank, item in enumerate(top, 1):
        categories.setdefault(item["category"], []).append((overall_rank, item))
    sections = []
    for category in CATEGORIES:
        rows = categories.get(category["id"], [])
        if not rows:
            continue
        body = "".join(html_row(item) for _, item in rows)
        metric = category["metric"]
        sections.append(
            f"<details><summary>{html.escape(category['label'])} · {len(rows):,} instruments</summary>"
            f"<p class='source-note'>Source: <a href='https://www.tradingview.com/markets/'>TradingView Global Scanner</a> · rank basis: {html.escape(metric)} · as of {html.escape(AS_OF)}.</p>"
            "<div class='table-wrap'><table><thead><tr><th>Category rank</th><th>Symbol / type</th><th>Formal name</th><th>Common name</th><th>Country</th><th>Exchange</th></tr></thead>"
            f"<tbody>{body}</tbody></table></div></details>"
        )
    trends_html = ""
    if trends:
        trend_rows = "".join(
            f"<li><b>{html.escape(x['symbol'])}</b> — {html.escape(x['name'])}"
            f" (CoinGecko platform trend rank {x['rank']})</li>"
            for x in trends
        )
        trends_html = (
            "<details><summary>CoinGecko trending crypto searches · platform-specific signal</summary>"
            f"<p>These are CoinGecko's platform search-trend results for the last 24 hours, "
            f"retrieved {html.escape(AS_OF)}; they are not a global Google-search ranking.</p><ul>{trend_rows}</ul></details>"
        )
    category_notes = "".join(
        f"<li><b>{html.escape(c['label'])}:</b> {html.escape(c['metric'])} — "
        f"TradingView Global Scanner, checked {html.escape(AS_OF)}.</li>"
        for c in CATEGORIES
    )
    return f"""<style>.mkt5k{{max-width:1100px;margin:auto;font:14px/1.6 Arial,sans-serif;color:#241610}}.mkt5k header{{padding:24px 18px;background:#f6e3d3;border-radius:16px}}.mkt5k details{{margin:12px 0;padding:10px 12px;border:1px solid #eadcc8;border-radius:10px;background:#fffdf8}}.mkt5k summary{{cursor:pointer;font-weight:800;color:#9c4522}}.mkt5k .source-note{{font-size:11px;color:#6e5d4b}}.mkt5k .table-wrap{{overflow-x:auto;max-height:70vh}}.mkt5k table{{width:100%;border-collapse:collapse;font-size:11px}}.mkt5k th,.mkt5k td{{padding:6px 7px;border-bottom:1px solid #eadcc8;text-align:left;vertical-align:top}}.mkt5k th{{position:sticky;top:0;background:#f8f0e3}}.mkt5k td small{{color:#6e5d4b}}</style><article class="mkt5k">
<header>
<p style="margin:0;color:#9c4522;font-weight:bold;letter-spacing:.14em;text-transform:uppercase">MILLED EDGE · MARKET DIRECTORY</p>
<h1 style="font-size:clamp(28px,5vw,42px);line-height:1.12;margin:10px 0">Top 5,000 Market Instruments</h1>
<p>A category-aware public market-activity directory across global shares, funds and ETFs, bonds, futures and commodities, crypto, forex, and indices.</p>
<p><b>As of {html.escape(AS_OF)}.</b> This is not a universal “most searched” ranking. No public source reports comparable worldwide search counts for 5,000 instruments. The list uses a transparent category-balanced order; each row carries its own rank basis, source, country, and date.</p>
<p><a href="https://millededgeindia.blogspot.com/p/markets-today.html">Open the full Markets Today directory</a> · <a href="https://raw.githubusercontent.com/kushalkumardagaca-png/milled-edge-automation/main/content/market-data/top-50000.json">Download the Top 50,000 directory data</a></p>
</header>
<section><h2>Methodology and source notes</h2><p>The 5,000 entries are the first 5,000 rows from a balanced 50,000-item category index. Each asset class is ranked separately; positions across unlike categories are not a single comparable popularity score. Market capitalization and reported trading volume are market-visibility proxies, not direct web searches.</p><ul>{category_notes}</ul>
<p>For an additional platform-specific search signal, CoinGecko's public <a href="https://docs.coingecko.com/reference/trending-search">Trending Search</a> reports its trending coins for the last 24 hours (default top 15). Yahoo Finance's <a href="https://finance.yahoo.com/lookup/">Trending Tickers</a> and a public report on ETF.com comparison-tool interest are separate platform signals and do not publish an all-market, 50,000-row query-count ranking. <a href="https://trends.google.com/trends/">Google Trends</a> uses normalized relative interest, not absolute counts.</p>
{trends_html}</section>
<section><h2>The Top 5,000 list</h2><p>Expand an asset class to view symbols, formal and common names, country, exchange, rank basis, and as-of date. A row's rank is category-local; no universal cross-asset search rank is implied.</p>
{''.join(sections)}</section>
<footer style="margin-top:24px;padding:14px;border-top:1px solid #eadcc8;color:#6e5d4b;font-size:12px">Market information is for education and discovery, not investment advice. Data may be delayed, incomplete, or revised by providers.</footer>
</article>"""


def main() -> None:
    all_categories: list[dict[str, Any]] = []
    totals: dict[str, int] = {}
    for category in CATEGORIES:
        print(f"Fetching {category['label']} ({category['limit']:,}) via {category['sort_by']}…", flush=True)
        rows, total = tv_rows(category)
        all_categories.append({"category": category, "rows": rows})
        totals[category["id"]] = total
        print(f"  received {len(rows):,} of {total:,}", flush=True)

    trends = coingecko_trending()
    crypto = next(x["rows"] for x in all_categories if x["category"]["id"] == "crypto")
    annotate_crypto(crypto, trends)

    # Interleave category-local ranks to keep the opening of the composite list
    # representative. `rank` is a directory position, not a cross-asset score.
    entries: list[dict[str, Any]] = []
    max_len = max(len(x["rows"]) for x in all_categories)
    rank = 0
    for category_rank in range(max_len):
        for group in all_categories:
            rows = group["rows"]
            if category_rank >= len(rows):
                continue
            rank += 1
            item = rows[category_rank]
            item["rank"] = rank
            entries.append(item)
    if len(entries) != 50000:
        raise RuntimeError(f"Expected exactly 50,000 entries, got {len(entries)}")

    metadata = {
        "title": "Category-aware Top 50,000 market directory",
        "asOf": AS_OF,
        "total": len(entries),
        "rankMeaning": "Balanced directory position; categoryRank is the comparable rank within that category.",
        "searchRankDisclaimer": "Not a universal web-search-volume ranking. Public trend signals are platform-specific; long-tail order uses category-appropriate market-cap or reported-volume proxies.",
        "source": "TradingView Global Scanner",
        "sourceUrl": "https://scanner.tradingview.com/global/scan",
        "trendingSource": "CoinGecko Trending Search",
        "trendingSourceUrl": "https://docs.coingecko.com/reference/trending-search",
        "categoryCounts": {x["category"]["id"]: len(x["rows"]) for x in all_categories},
        "categoryUniverseCounts": totals,
        "categories": [
            {"id": c["id"], "label": c["label"], "limit": c["limit"], "metric": c["metric"]}
            for c in CATEGORIES
        ],
        "cryptoTrendingSearch": trends,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    POST_OUT.parent.mkdir(parents=True, exist_ok=True)
    compact_entries = [
        {
            "s": x["symbol"], "n": x["formalName"], "a": x["commonName"],
            "x": x["exchange"], "t": x["type"], "u": x["subtype"],
            "c": x["country"], "g": x["category"], "r": x["rank"],
            "cr": x["categoryRank"],
            "tr": (x.get("trendSignal") or {}).get("rank") if x.get("trendSignal") else None,
        }
        for x in entries
    ]
    OUT.write_text(json.dumps({"metadata": metadata, "entries": compact_entries}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    POST_OUT.write_text(build_post(entries, metadata, trends), encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    print(f"Wrote {POST_OUT} ({POST_OUT.stat().st_size:,} bytes; 5,000 rows)")


if __name__ == "__main__":
    main()
