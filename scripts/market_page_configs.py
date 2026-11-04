"""Provider-filtered subcategory rows for the first 20 market category posts."""
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
    "equity-stocks-share-class": ("stock", choices([
        ("common","Common shares","common"),("preferred","Preferred shares","preferred"),
        ("other-classes","Other share classes","other")],"subtype","match")),
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
        ("nasdaq","Nasdaq indices","Nasdaq"),("nifty","Nifty indices","Nifty"),
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
        ("hydrogen","Hydrogen · where listed","hydrogen"),("nitrogen","Nitrogen · where listed","nitrogen"),
        ("other-industrial-gases","Other industrial gases","industrial gas")])),
    "commodities-commodity-energy": ("futures", choices([
        ("wti","WTI crude oil","WTI"),("brent","Brent crude oil","Brent"),("natural-gas","Natural gas","natural gas"),
        ("gasoline","Gasoline","gasoline"),("heating-oil","Heating oil","heating oil"),("other-fuels","Other fuels","fuel")])),
    "commodities-commodity-grains": ("futures", choices([
        ("wheat","Wheat","wheat"),("corn","Corn","corn"),("soybeans","Soybeans","soybean"),
        ("rice","Rice","rice"),("oats","Oats","oats"),("soymeal","Soybean meal","soybean meal")])),
    "commodities-commodity-fibres-softs": ("futures", choices([
        ("cotton","Cotton","cotton"),("jute","Jute · where listed","jute"),("sugar","Sugar","sugar"),
        ("coffee","Coffee","coffee"),("cocoa","Cocoa","cocoa"),("other-softs","Other soft commodities","soft commodity")])),
    "commodities-commodity-livestock": ("futures", choices([
        ("live-cattle","Live cattle","cattle"),("lean-hogs","Lean hogs","hog"),("other-livestock","Other livestock","livestock")])),
    "commodities-commodity-forestry": ("futures", choices([
        ("lumber","Lumber","lumber"),("other-forestry","Other forestry materials","forestry")])),
}

BASE_TYPE = {
    "equity-stocks":"stock", "market-indices":"index", "commodities":"futures",
}


def build_page_configs() -> list[dict]:
    pages = _catalog.build_catalog()[:20]
    configs = []
    for page in pages:
        base_type, subs = PAGE_ROWS[page["slug"]]
        if base_type == "futures" and page["division_id"] == "commodities":
            # commodity spot instruments are included alongside futures when the
            # provider can represent the combination; name filters avoid inventing symbols.
            base_filters = [f("type", "in_range", ["futures", "spot"])]
        else:
            base_filters = [f("type", "equal", base_type)]
        subcategories = []
        for sub in subs:
            subcategories.append({
                "id": sub["id"], "label": sub["label"],
                "filters": base_filters + sub["filters"],
            })
        configs.append({**page, "base_filters": base_filters, "subcategories": subcategories})
    return configs
