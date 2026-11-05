"""Provider-filtered subcategory rows for the 104 market category posts."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("market_categories", Path(__file__).with_name("market_categories.py"))
_catalog = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_catalog)


def f(field, operation, value):
    return {"left": field, "operation": operation, "right": value}


def choices(items, field="description", operation="match"): 
    return [{"id": slug, "label": label, "filters": [f(field, operation, val)]}
            for slug, label, val in items]

COUNTRIES = [
    ("india", "India", "India"), ("united-states", "United States", "United States"),
    ("china", "China", "China"), ("united-kingdom", "United Kingdom", "United Kingdom"),
    ("japan", "Japan", "Japan"), ("hong-kong", "Hong Kong", "Hong Kong"),
    ("germany", "Germany", "Germany"), ("france", "France", "France"),
    ("canada", "Canada", "Canada"), ("australia", "Australia", "Australia"),
    ("brazil", "Brazil", "Brazil"), ("south-korea", "South Korea", "South Korea"),
    ("singapore", "Singapore", "Singapore"), ("indonesia", "Indonesia", "Indonesia"),
    ("uae", "United Arab Emirates", "United Arab Emirates"),
    ("saudi-arabia", "Saudi Arabia", "Saudi Arabia"),
]
EXCHANGES = [
    ("nse", "NSE India", "NSE"), ("bse", "BSE India", "BSE"),
    ("nyse", "NYSE", "NYSE"), ("nasdaq", "Nasdaq", "NASDAQ"),
    ("lse", "London Stock Exchange", "LSE"), ("tokyo", "Tokyo Stock Exchange", "TSE"),
    ("hkex", "Hong Kong Exchange", "HKEX"), ("sse", "Shanghai Exchange", "SSE"),
    ("szse", "Shenzhen Exchange", "SZSE"), ("tsx", "Toronto Exchange", "TSX"),
    ("asx", "Australian Exchange", "ASX"), ("euronext", "Euronext", "EURONEXT"),
]
SECTORS = [
    ("technology-services", "Technology services", "Technology Services"),
    ("electronic-technology", "Electronic technology", "Electronic Technology"),
    ("finance", "Finance", "Finance"), ("energy-minerals", "Energy minerals", "Energy Minerals"),
    ("health-technology", "Health technology", "Health Technology"),
    ("consumer-nondurables", "Consumer non-durables", "Consumer Non-Durables"),
    ("producer-manufacturing", "Producer manufacturing", "Producer Manufacturing"),
    ("utilities", "Utilities", "Utilities"), ("transportation", "Transportation", "Transportation"),
    ("non-energy-minerals", "Non-energy minerals", "Non-Energy Minerals"),
]

PAGE_ROWS = {
    "equity-stocks-country-region": ("stock", choices(COUNTRIES, "country", "equal")),
    "equity-stocks-exchange-venue": ("stock", choices(EXCHANGES, "exchange", "equal")),
    "equity-stocks-sector-industry": ("stock", choices(SECTORS, "sector", "equal")),
    "equity-stocks-market-cap": ("stock", [
        {"id":"mega-cap","label":"Mega cap · above $200B","filters":[f("market_cap_basic","egreater",200_000_000_000)]},
        {"id":"large-cap","label":"Large cap · $10B–$200B","filters":[f("market_cap_basic","egreater",10_000_000_000),f("market_cap_basic","eless",200_000_000_000)]},
        {"id":"mid-cap","label":"Mid cap · $2B–$10B","filters":[f("market_cap_basic","egreater",2_000_000_000),f("market_cap_basic","eless",10_000_000_000)]},
        {"id":"small-cap","label":"Small cap · $300M–$2B","filters":[f("market_cap_basic","egreater",300_000_000),f("market_cap_basic","eless",2_000_000_000)]},
        {"id":"micro-cap","label":"Micro cap · below $300M","filters":[f("market_cap_basic","eless",300_000_000)]},
    ]),
    "equity-stocks-share-class": ("stock", [
        {"id":"common","label":"Common shares","filters":[f("subtype","match","common")]},
        {"id":"preferred","label":"Preferred shares","filters":[f("subtype","match","preferred")]},
        {"id":"non-primary","label":"Non-primary listings","filters":[f("is_primary","equal",False)]},
    ]), 
    "equity-stocks-listing-status": ("stock", [
        {"id":"primary-listings","label":"Primary listings","filters":[f("is_primary","equal",True)]},
        {"id":"other-listings","label":"Other supported listings","filters":[f("is_primary","equal",False)]},
    ]),
    "market-indices-index-country": ("index", [
        {"id":"india","label":"India","filters":[f("exchange","in_range",["NSE","BSE"])]},
        {"id":"united-states","label":"United States","filters":[f("exchange","in_range",["SP","DJ","NASDAQ","CBOE"])]},
        {"id":"china","label":"China","filters":[f("exchange","in_range",["SSE","SZSE"])]},
        {"id":"united-kingdom","label":"United Kingdom","filters":[f("name","match","FTSE")]},
        {"id":"japan","label":"Japan-linked benchmarks","filters":[f("description","match","Japan")]}, 
        {"id":"hong-kong","label":"Hong Kong","filters":[f("exchange","equal","HSI")]},
        {"id":"germany","label":"Germany","filters":[f("exchange","equal","XETR")]},
        {"id":"france","label":"France","filters":[f("name","match","CAC")]},
        {"id":"canada","label":"Canada","filters":[f("exchange","equal","TSX")]},
        {"id":"australia","label":"Australia","filters":[f("description","match","ASX")]}, 
        {"id":"brazil","label":"Brazil","filters":[f("exchange","equal","BMFBOVESPA")]},
        {"id":"south-korea","label":"South Korea","filters":[f("name","match","KOSPI")]},
        {"id":"singapore","label":"Singapore","filters":[f("name","match","STI")]},
        {"id":"indonesia","label":"Indonesia","filters":[f("exchange","equal","IDX")]},
        {"id":"uae","label":"United Arab Emirates","filters":[f("exchange","equal","DFM")]},
        {"id":"saudi-arabia","label":"Saudi Arabia","filters":[f("exchange","equal","TADAWUL")]},
    ]),
    "market-indices-index-scope": ("index", [
        {"id":"main-benchmarks","label":"Main benchmark indices","filters":[f("subtype","equal","main")]},
        {"id":"cfd-index-products","label":"CFD index products","filters":[f("subtype","equal","cfd")]},
        {"id":"crypto-market-cap","label":"Crypto market-cap indices","filters":[f("subtype","equal","crypto")]},
        {"id":"synthetic-indices","label":"Synthetic indices","filters":[f("subtype","equal","synthetic")]},
        {"id":"other-index-types","label":"Other provider index types","filters":[f("subtype","equal","index_other")]},
    ]),
    "market-indices-index-asset-class": ("index", [
        {"id":"equity-benchmarks","label":"Main market benchmarks","filters":[f("subtype","equal","main")]},
        {"id":"bond-indices","label":"Bond indices","filters":[f("description","match","bond")]},
        {"id":"commodity-indices","label":"Commodity indices","filters":[f("description","match","commodity")]},
        {"id":"crypto-indices","label":"Crypto capitalization indices","filters":[f("subtype","equal","crypto")]},
        {"id":"other-asset-indices","label":"Other asset indices","filters":[f("subtype","equal","index_other")]},
    ]),
    "market-indices-index-weighting": ("index", [
        {"id":"main-benchmarks","label":"Main benchmarks","filters":[f("subtype","equal","main")]},
        {"id":"cfd-products","label":"CFD index products","filters":[f("subtype","equal","cfd")]},
        {"id":"crypto-capitalization","label":"Crypto capitalization indices","filters":[f("subtype","equal","crypto")]},
        {"id":"synthetic-indices","label":"Synthetic indices","filters":[f("subtype","equal","synthetic")]},
        {"id":"other-provider-types","label":"Other provider index types","filters":[f("subtype","equal","index_other")]},
    ]),
    "market-indices-index-provider": ("index", choices([
        ("sp-dow-jones","S&P Dow Jones","S&P"),("msci","MSCI","MSCI"),("ftse-russell","FTSE Russell","FTSE"),
        ("cboe","CBOE benchmarks","CBOE"),("nifty","Nifty indices","Nifty"),
        ("nikkei","Nikkei and Japan-linked benchmarks","Japan"),("other-providers","Other providers","index")],"description","match")),
    "commodities-commodity-precious": ("futures", choices([
        ("gold","Gold","gold"),("silver","Silver","silver"),("platinum","Platinum","platinum"),
        ("palladium","Palladium","palladium"),("diamond","Diamond · where listed","diamond")])),
    "commodities-commodity-base-metals": ("futures", choices([
        ("copper","Copper","copper"),("aluminium","Aluminium","aluminium"),("zinc","Zinc","zinc"),
        ("nickel","Nickel","nickel"),("lead","Lead","lead"),("other-base-metals","Other base metals","metal")])),
    "commodities-commodity-minerals": ("futures", choices([
        ("iron-ore","Iron ore","iron ore"),("lithium","Lithium","lithium"),("cobalt","Cobalt","cobalt"),
        ("uranium","Uranium","uranium"),("coal","Coal","coal")])),
    "commodities-commodity-gases": ("futures", choices([
        ("natural-gas","Natural-gas contracts","natural gas"),
        ("fertilizers","Fertilizer contracts","fertilizer"),
        ("chemical-products","Chemical-product contracts","chemicals")])), 
    "commodities-commodity-energy": ("futures", choices([
        ("wti","WTI crude oil","WTI"),("brent","Brent crude oil","Brent"),("natural-gas","Natural gas","natural gas"),
        ("gasoline","Gasoline","gasoline"),("heating-oil","Heating oil","heating oil"),("other-fuels","Other fuels","fuel")])),
    "commodities-commodity-grains": ("futures", choices([
        ("wheat","Wheat","wheat"),("corn","Corn","corn"),("soybeans","Soybeans","soybean"),
        ("rice","Rice","rice"),("oats","Oats","oats"),("soymeal","Soybean meal","soybean meal")])),
    "commodities-commodity-fibres-softs": ("futures", choices([
        ("cotton","Cotton","cotton"),("sugar","Sugar","sugar"),
        ("coffee","Coffee","coffee"),("cocoa","Cocoa","cocoa")])), 
    "commodities-commodity-livestock": ("futures", choices([
        ("live-cattle","Live cattle","cattle"),("lean-hogs","Lean hogs","hog"),("other-livestock","Other livestock","livestock")])),
    "commodities-commodity-forestry": ("futures", choices([
        ("lumber","Lumber contracts","lumber")])), 
}

BASE_TYPE = {
    "depositary-receipts":"dr", "bonds-fixed-income":"bond", "etfs":"fund",
    "index-funds":"fund", "mutual-funds":"fund", "other-funds":"fund",
    "futures":"futures", "options":"futures", "forex":"forex",
    "crypto-spot":"spot", "crypto-derivatives":"futures", "economic-data":"economic",
    "structured-products":"multi", "reits":"stock", "other-instruments":"multi",
}
ALL_TYPES = ["stock","bond","fund","futures","forex","spot","economic","dr","index"]


def row(label, field, operation, value, *, slug=None, type_override=None):
    return {"id": slug or _catalog.slugify(label), "label": label,
            "filters": [f(field, operation, value)], "type_override": type_override}


def drows(items):
    return [row(label, "description", "match", term, slug=slug) for slug,label,term in items]


def country_rows(codes=("India","United States","United Kingdom","Canada","Australia")):
    return [row(c, "country", "equal", c, slug=_catalog.slugify(c)) for c in codes]


def exchange_rows(codes=("NYSE","NASDAQ","LSE","NSE","BSE")):
    return [row(c, "exchange", "equal", c, slug=_catalog.slugify(c)) for c in codes]


def generic_rows(page):
    """Provider-aware rows for the remaining 84 category destinations.

    Where TradingView does not expose the requested facet, rows use a clearly
    named, supported source slice rather than fabricate issuer/rating/option data.
    """
    d, cid = page["division_id"], page["category_id"]
    if d == "depositary-receipts":
        return {
            "underlying-country": country_rows(("United States","India","United Kingdom","Canada","China")),
            "receipt-program": drows([("adr","American depositary receipts","ADR"),("gdr","Global depositary receipts","GDR"),("depositary","Other depositary receipt records","depositary")]),
            "receipt-exchange": exchange_rows(("NYSE","NASDAQ","LSE")),
            "receipt-underlying": drows([("technology","Technology issuers","technology"),("banking","Banking issuers","bank"),("energy","Energy issuers","energy"),("healthcare","Healthcare issuers","health")]),
        }[cid]
    if d == "bonds-fixed-income":
        return {
            "bond-issuer-type":[row("Corporate bonds","subtype","equal","corporate",slug="corporate"),row("Government bonds","subtype","equal","government",slug="government")],
            "bond-country":country_rows(("United States","India","United Kingdom","Germany","France")),
            "bond-maturity":drows([("2026","Maturing in 2026","2026"),("2030","Maturing in 2030","2030"),("2035","Maturing in 2035","2035"),("2040","Maturing in 2040","2040")]),
            "bond-credit-quality":[row("Bond records (ratings are not normalized by this feed)","type","equal","bond",slug="reported-bonds")],
            "bond-coupon-structure":drows([("fixed","Fixed-coupon text matches","fixed"),("floating","Floating-rate text matches","floating")]),
            "bond-currency":[row(x,"currency","equal",x,slug=x.lower()) for x in ("USD","EUR")],
        }[cid]
    if d == "etfs":
        return {
            "etf-asset-class":drows([("equity","Equity ETFs","equity"),("fixed-income","Bond and fixed-income ETFs","bond"),("commodity","Commodity ETFs","gold"),("crypto","Crypto-related ETFs","crypto"),("broad-index","Index-tracking ETFs","index")]),
            "etf-country":country_rows(("United States","India","Canada","Australia","United Kingdom")),
            "etf-sector-theme":drows([("technology","Technology ETFs","technology"),("energy","Energy ETFs","energy"),("healthcare","Healthcare ETFs","health"),("financials","Financial-sector ETFs","financial")]),
            "etf-benchmark":drows([("sp500","S&P 500 references","S&P 500"),("msci","MSCI benchmark references","MSCI"),("nasdaq","Nasdaq benchmark references","Nasdaq"),("ftse","FTSE benchmark references","FTSE")]),
            "etf-strategy":drows([("leveraged","Leveraged ETFs","leveraged"),("inverse","Inverse ETFs","inverse"),("active","Active-management references","active"),("passive","Passive/index references","passive")]),
            "etf-distribution":drows([("distribution","Distribution references","distribution"),("accumulation","Accumulation references","accumulating"),("dividend","Dividend-focused ETFs","dividend")]),
        }[cid]
    if d == "index-funds":
        return {
            "indexfund-country":country_rows(("United States","India","United Kingdom","Canada","Australia")),
            "indexfund-asset-class":drows([("equity","Equity index-fund records","equity"),("fixed-income","Fixed-income index-fund records","bond"),("commodity","Commodity index-fund records","commodity"),("multi-asset","Multi-asset index-fund references","multi asset")]),
            "indexfund-market-cap":drows([("large-cap","Large-cap index references","large cap"),("mid-cap","Mid-cap index references","mid cap"),("small-cap","Small-cap index references","small cap"),("broad-market","Broad-market index references","broad market")]),
            "indexfund-benchmark":drows([("sp500","S&P benchmark references","S&P"),("msci","MSCI benchmark references","MSCI"),("nasdaq","Nasdaq benchmark references","Nasdaq"),("ftse","FTSE benchmark references","FTSE")]),
            "indexfund-wrapper":[row("ETF wrappers","subtype","equal","etf",slug="etf"),row("Mutual-fund wrappers","subtype","equal","mutual",slug="mutual"),row("Closed-end wrappers","subtype","equal","closedend",slug="closed-end")],
        }[cid]
    if d == "mutual-funds":
        return {
            "mf-asset-class":drows([("equity","Equity mutual-fund records","equity"),("debt","Debt and bond-fund records","bond"),("hybrid","Hybrid-fund references","hybrid"),("commodity","Commodity-fund references","commodity")]),
            "mf-equity-style":drows([("large-cap","Large-cap style references","large cap"),("mid-cap","Mid-cap style references","mid cap"),("small-cap","Small-cap style references","small cap"),("multi-cap","Multi-cap references","multi cap"),("multi-asset","Multi-asset style references","multi asset")]),
            "mf-debt-duration":drows([("short-duration","Short-duration references","short duration"),("long-duration","Long-duration references","long duration"),("credit-risk","Credit-risk references","credit risk"),("corporate-debt","Corporate-debt references","corporate bond")]),
            "mf-geography":country_rows(("India","United States","United Kingdom","Canada","Australia")),
            "mf-sector-theme":drows([("technology","Technology funds","technology"),("energy","Energy funds","energy"),("healthcare","Healthcare funds","health"),("financials","Financial-sector funds","financial")]),
            "mf-tax-goal":drows([("tax","Tax-saving references","tax"),("retirement","Retirement references","retirement"),("income","Income-oriented references","income")]),
            "mf-management-style":drows([("active","Active-management references","active"),("passive","Passive/index references","passive"),("index","Index-oriented references","index")]),
        }[cid]
    if d == "other-funds":
        return {
            "otherfund-type":[row("Closed-end funds","subtype","equal","closedend",slug="closed-end"),row("ETF records","subtype","equal","etf",slug="etf"),row("Mutual-fund records","subtype","equal","mutual",slug="mutual")],
            "otherfund-asset-class":drows([("equity","Equity exposure","equity"),("bonds","Bond exposure","bond"),("gold","Gold and commodity exposure","gold"),("crypto","Crypto exposure","crypto")]),
            "otherfund-geography":country_rows(("United States","India","United Kingdom","Canada","Australia")),
            "otherfund-strategy":drows([("leveraged","Leveraged strategies","leveraged"),("inverse","Inverse strategies","inverse"),("income","Income strategies","income"),("index","Index strategies","index")]),
            "otherfund-provider-subtype":[row(x,"subtype","equal",v,slug=x.lower()) for x,v in (("ETF","etf"),("Mutual","mutual"),("Closed-end","closedend"))],
        }[cid]
    if d == "futures":
        return {
            "future-underlying":[row("Equity-index futures","description","match","index",slug="equity-index"),row("Rates and bond futures","description","match","bond",slug="rates"),row("Currency futures","description","match","currency",slug="currency"),row("Commodity futures","description","match","oil",slug="commodity"),row("Crypto-classified futures","subtype","equal","crypto",slug="crypto")],
            "future-contract-family":[row(x,"subtype","equal",v,slug=x.lower().replace(" ","-")) for x,v in (("Continuous","continuous"),("Micro","micro"),("Mini","mini"),("Crypto-linked","crypto"))],
            "future-exchange":exchange_rows(("CME","CBOT","NYMEX","EUREX","SGX")),
            "future-expiry":drows([("2026","2026 contract references","2026"),("2027","2027 contract references","2027"),("2028","2028 contract references","2028")]),
            "future-settlement":[row("Provider-listed futures (settlement terms require contract-source verification)","type","equal","futures",slug="all-reported-futures")],
            "future-liquidity":[row("Higher reported activity","volume","egreater",0,slug="active"),row("Open-interest / activity fields where supplied","type","equal","futures",slug="reported-activity")],
        }[cid]
    if d == "options":
        # The global scan does not return standalone option-contract records;
        # these are explicitly identified underlyings, not fabricated options.
        base_types={"option-underlying":["stock","index","futures"],"option-call-put":["stock","index","futures"],"option-expiry":["futures"],"option-strike":["stock","index"],"option-exchange":["stock","futures"],"option-style":["stock","index"]}[cid]
        return [row(label,"type","in_range",types,slug=slug,type_override=types) for slug,label,types in [
            ("equity-underlyings","Equity underlyings (not option contracts)",["stock"]),
            ("index-underlyings","Index underlyings (not option contracts)",["index"]),
            ("futures-underlyings","Futures underlyings (not option contracts)",["futures"]),
        ] if any(x in base_types for x in types)]
    if d == "forex":
        return {
            "fx-base-currency":[row(x+" pairs","name","match",x,slug=x.lower()) for x in ("USD","EUR","GBP","JPY","INR")],
            "fx-quote-currency":[row(x+" quote-currency matches","name","match",x,slug=x.lower()) for x in ("USD","EUR","JPY","AUD","CAD")],
            "fx-pair-class":[row("Synthetic pairs","subtype","equal","synthetic",slug="synthetic"),row("CFD pairs","subtype","equal","cfd",slug="cfd"),row("Spread-bet pairs","subtype","equal","spreadbet",slug="spread-bet")],
            "fx-region":[row(x+"-linked pairs","name","match",x,slug=x.lower()) for x in ("JPY","INR","CNY","AUD","NZD")],
            "fx-venue":[row(x,"exchange","equal",x,slug=x.lower()) for x in ("FX_IDC","OANDA","SAXO","FOREXCOM")],
        }[cid]
    if d == "crypto-spot":
        return {
            "crypto-major":drows([("bitcoin","Bitcoin markets","Bitcoin"),("ethereum","Ethereum markets","Ethereum"),("solana","Solana markets","Solana")]),
            "crypto-stablecoins":drows([("tether","Tether markets","Tether"),("usd-coin","USD Coin markets","USD Coin"),("dai","DAI markets","DAI")]),
            "crypto-defi":drows([("uniswap","Uniswap/DeFi references","Uniswap"),("aave","Aave/DeFi references","Aave"),("defi","Other DeFi-labelled records","DeFi")]),
            "crypto-layer2":drows([("arbitrum","Arbitrum markets","Arbitrum"),("optimism","Optimism markets","Optimism"),("polygon","Polygon markets","Polygon")]),
            "crypto-exchange-tokens":drows([("bnb","BNB markets","BNB"),("okb","OKB markets","OKB"),("exchange","Exchange-token references","exchange token")]),
            "crypto-infrastructure":drows([("chainlink","Chainlink markets","Chainlink"),("pyth","Pyth markets","Pyth"),("oracle","Oracle-labelled records","oracle")]),
            "crypto-themes":drows([("gaming","Gaming-labelled records","gaming"),("payments","Payment-labelled records","payment"),("metaverse","Metaverse-labelled records","metaverse")]),
            "crypto-quote-venue":[row("USDT quote pairs","name","match","USDT",slug="usdt"),row("USD quote pairs","name","match","USD",slug="usd"),row("Binance listings","exchange","equal","BINANCE",slug="binance"),row("Coinbase listings","exchange","equal","COINBASE",slug="coinbase")],
        }[cid]
    if d == "crypto-derivatives":
        return {
            "cryptoderiv-futures":[row("Crypto subtype futures","subtype","equal","crypto",slug="crypto-futures")],
            "cryptoderiv-perpetuals":[row("Crypto-classified derivative records (perpetual status needs venue verification)","subtype","equal","crypto",slug="crypto-classified")],
            "cryptoderiv-options":[row("Listed crypto futures underlying set (option contracts are not exposed by this scan)","subtype","equal","crypto",slug="crypto-underlyings")],
            "cryptoderiv-underlying":[row("Bitcoin-linked contracts","description","match","Bitcoin",slug="bitcoin"),row("Ethereum-linked contracts","description","match","Ethereum",slug="ethereum"),row("Other crypto-classified contracts","subtype","equal","crypto",slug="other-crypto")],
            "cryptoderiv-venue":[row(x,"exchange","equal",x,slug=x.lower()) for x in ("BINANCE","OKX","BYBIT","CME")],
        }[cid]
    if d == "economic-data":
        terms={"econ-growth":[("gdp","GDP and growth series","GDP"),("growth","Growth series","growth")],
               "econ-inflation":[("inflation","Inflation series","inflation"),("cpi","Consumer-price series","CPI"),("prices","Price-index series","price index")],
               "econ-employment":[("employment","Employment series","employment"),("unemployment","Unemployment series","unemployment"),("labour","Labour-market series","labor")],
               "econ-rates":[("policy-rate","Policy-rate series","interest rate"),("central-bank","Central-bank series","central bank"),("rate-series","Rate and monetary series","rate")],
               "econ-trade":[("trade","Trade series","trade"),("exports","Export series","export"),("imports","Import series","import")],
               "econ-fiscal":[("debt","Public-debt series","debt"),("fiscal","Fiscal series","fiscal"),("deficit","Deficit series","deficit")],
               "econ-production":[("production","Production series","production"),("housing","Housing series","housing"),("sentiment","Sentiment series","sentiment")]}[cid]
        return drows(terms)
    if d == "structured-products":
        return {
            "structured-protection":[row("Certificate records (capital protection is not verified by the feed)","description","match","certificate",slug="certificates"),row("Warrant records (terms require issuer-document verification)","description","match","warrant",slug="warrants")],
            "structured-leverage":[row("Leveraged listed products","description","match","leveraged",slug="leveraged"),row("Inverse listed products","description","match","inverse",slug="inverse")],
            "structured-notes-warrants":[row("Warrant records","description","match","warrant",slug="warrants"),row("Certificate records","description","match","certificate",slug="certificates"),row("Note records","description","match","note",slug="notes")],
            "structured-underlying":drows([("gold","Gold-linked product references","gold"),("index","Index-linked product references","index"),("crypto","Crypto-linked product references","crypto")]),
            "structured-issuer-maturity":drows([("2026","2026 maturity references","2026"),("2030","2030 maturity references","2030"),("issuer","Issuer references","certificate")]),
        }[cid]
    if d == "reits":
        return {
            "reit-country":country_rows(("United States","India","United Kingdom","Canada","Australia")),
            "reit-property-sector":drows([("residential","Residential property","residential"),("retail","Retail property","retail"),("industrial","Industrial property","industrial"),("office","Office property","office")]),
            "reit-structure":[row("Mortgage REIT references","description","match","mortgage reit",slug="mortgage"),row("Provider-labelled REIT listings (structure not normalized)","description","match","REIT",slug="reported-reits")],
            "reit-market-cap":[row("Reported market-cap data","market_cap_basic","egreater",0,slug="reported-cap")],
            "reit-exchange":exchange_rows(("NYSE","NASDAQ","LSE","NSE","BSE")),
        }[cid]
    if d == "other-instruments":
        return {
            "other-type":[row(t.upper()+" records","type","equal",t,slug=t) for t in ALL_TYPES],
            "other-subtype":[row(label,"subtype","equal",sub,slug=slug,type_override=typ) for slug,label,typ,sub in (("corporate-bonds","Corporate bonds","bond","corporate"),("government-bonds","Government bonds","bond","government"),("crypto-spot","Crypto spot","spot","crypto"),("crypto-futures","Crypto futures","futures","crypto"),("etfs","ETFs","fund","etf"))],
            "other-country":country_rows(("United States","India","United Kingdom","Canada","Australia")),
            "other-exchange":exchange_rows(("NYSE","NASDAQ","CME","FX_IDC","BINANCE")),
        }[cid]
    raise KeyError(f"No provider-row template for {d}/{cid}")


def build_page_configs(batch=None) -> list[dict]:
    catalog = _catalog.build_catalog()
    if batch is not None:
        catalog = [p for p in catalog if p["batch"] == batch]
    configs = []
    for page in catalog:
        if page["slug"] in PAGE_ROWS:
            base_type, subs = PAGE_ROWS[page["slug"]]
            if base_type == "futures" and page["division_id"] == "commodities":
                base_filters = [f("type", "in_range", ["futures", "spot"])]
            else:
                base_filters = [f("type", "equal", base_type)]
            subcategories = [{"id":s["id"],"label":s["label"],"filters":base_filters+s["filters"]} for s in subs]
        else:
            division = page["division_id"]
            bt = BASE_TYPE[division]
            if bt == "multi":
                types = ALL_TYPES if division == "other-instruments" else ["stock","fund","dr"]
                base_filters = [f("type","in_range",types)]
            else:
                base_filters = [f("type","equal",bt)]
            subcategories=[]
            for sub in generic_rows(page):
                override = sub.get("type_override")
                filters = list(sub["filters"])
                if override:
                    filters = [x for x in filters if x["left"] != "type"]
                    own_type = f("type","in_range",override) if isinstance(override,list) else f("type","equal",override)
                    combined = [own_type] + [x for x in base_filters if x["left"] != "type"] + filters
                else:
                    combined = base_filters + filters
                subcategories.append({"id":sub["id"],"label":sub["label"],"filters":combined})
        configs.append({**page,"base_filters":base_filters,"subcategories":subcategories})
    return configs
