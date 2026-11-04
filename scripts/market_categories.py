"""Canonical catalogue for the 18-division, 104-category markets rollout.

This catalogue defines post identity and editorial metadata. Market records and
subcategory values remain provider-driven; they are not frozen into this file.
"""
from __future__ import annotations

import re
import unicodedata

# division_key, division_title, [(category_key, category_title, short scope)]
DIVISION_SPECS = [
    ("equity-stocks", "Equity stocks", [
        ("country-region", "Country and region", "equities grouped by issuer/listing country and region"),
        ("exchange-venue", "Exchange and venue", "shares grouped by their reported listing exchange or trading venue"),
        ("sector-industry", "Sector and industry", "equities grouped by the provider's industry classifications"),
        ("market-cap", "Market capitalization", "equities grouped by reported market-capitalization bands"),
        ("share-class", "Share class", "common, preferred, and other provider-classified share types"),
        ("listing-status", "Listing and primary status", "primary listings and other supported listing records"),
    ]),
    ("depositary-receipts", "Depositary receipts", [
        ("underlying-country", "Underlying country", "depositary receipts grouped by the issuer's underlying country"),
        ("receipt-program", "Receipt program and type", "depositary receipts grouped by provider-reported receipt type"),
        ("receipt-exchange", "Exchange and venue", "depositary receipts grouped by reported listing venue"),
        ("receipt-underlying", "Issuer and underlying security", "receipts connected to their issuer and underlying security"),
    ]),
    ("bonds-fixed-income", "Bonds and fixed income", [
        ("bond-issuer-type", "Issuer type", "government, sovereign, corporate, and other reported bond issuers"),
        ("bond-country", "Country and region", "fixed-income records grouped by reported country or region"),
        ("bond-maturity", "Maturity and duration", "bonds grouped by reported maturity or duration information"),
        ("bond-credit-quality", "Credit quality", "bond records grouped by supported credit-quality classifications"),
        ("bond-coupon-structure", "Coupon and structure", "fixed, floating, inflation-linked, and other reported bond structures"),
        ("bond-currency", "Currency", "bonds grouped by their quoted or denomination currency"),
    ]),
    ("market-indices", "Market indices", [
        ("index-country", "Country and region", "benchmarks grouped by the market or region they represent"),
        ("index-scope", "Market scope", "broad-market, sector, and other supported benchmark scopes"),
        ("index-asset-class", "Asset class", "equity, bond, commodity, volatility, and other supported index classes"),
        ("index-weighting", "Index construction and format", "provider-classified main benchmarks, CFD products, crypto-capitalization indices, synthetic indices, and other index formats"),
        ("index-provider", "Index provider and family", "indices grouped by their reported provider or benchmark family"),
    ]),
    ("etfs", "Exchange-traded funds (ETFs)", [
        ("etf-asset-class", "Asset class", "equity, bond, commodity, crypto, currency, and other ETF exposures"),
        ("etf-country", "Country and region", "ETFs grouped by supported market or regional exposure"),
        ("etf-sector-theme", "Sector and theme", "sector and thematic ETF classifications where provider data exists"),
        ("etf-benchmark", "Tracked benchmark", "ETFs grouped by the benchmark they report tracking"),
        ("etf-strategy", "Investment strategy", "active, passive, leveraged, inverse, and other reported ETF strategies"),
        ("etf-distribution", "Distribution and structure", "accumulating, distributing, and other supported ETF structures"),
    ]),
    ("index-funds", "Index funds", [
        ("indexfund-country", "Country and region", "index funds grouped by the market or region they track"),
        ("indexfund-asset-class", "Asset class", "equity, fixed-income, commodity, and other index-fund exposures"),
        ("indexfund-market-cap", "Market-cap segment", "broad-market, large-cap, mid-cap, and small-cap index strategies"),
        ("indexfund-benchmark", "Tracked benchmark", "index funds grouped by their reported underlying benchmark"),
        ("indexfund-wrapper", "Fund wrapper", "ETF, mutual-fund, or other wrapper where provider data identifies it"),
    ]),
    ("mutual-funds", "Mutual funds", [
        ("mf-asset-class", "Asset class", "equity, debt, hybrid, and other supported mutual-fund asset classes"),
        ("mf-equity-style", "Equity style and market cap", "large-cap, mid-cap, small-cap, multi-cap, and flexi-cap styles"),
        ("mf-debt-duration", "Debt duration and risk", "debt schemes grouped by reported duration or credit-risk profile"),
        ("mf-geography", "Country and region", "mutual funds grouped by reported geographic investment focus"),
        ("mf-sector-theme", "Sector and theme", "sectoral and thematic mutual-fund classifications where available"),
        ("mf-tax-goal", "Tax-saving and goal-based", "supported tax-saving and solution-oriented fund categories"),
        ("mf-management-style", "Management style", "active, passive, and other reported management approaches"),
    ]),
    ("other-funds", "Other funds", [
        ("otherfund-type", "Fund type", "supported fund records outside the ETF, index-fund, and mutual-fund routes"),
        ("otherfund-asset-class", "Asset class", "other funds grouped by their reported underlying exposure"),
        ("otherfund-geography", "Country and region", "other funds grouped by reported market or regional focus"),
        ("otherfund-strategy", "Strategy and theme", "supported strategy and thematic classifications"),
        ("otherfund-provider-subtype", "Provider subtype", "funds grouped by the source's own subtype labels"),
    ]),
    ("futures", "Futures", [
        ("future-underlying", "Underlying asset class", "equity, index, commodity, currency, rates, and other underlyings"),
        ("future-contract-family", "Contract family", "futures grouped by their reported contract or product family"),
        ("future-exchange", "Country and exchange", "contracts grouped by supported country and trading venue"),
        ("future-expiry", "Expiry and tenor", "contracts grouped by available expiry or tenor data"),
        ("future-settlement", "Settlement and delivery", "cash-settled, deliverable, and other reported settlement details"),
        ("future-liquidity", "Reported activity", "futures grouped by reported volume or open-interest ranges"),
    ]),
    ("options", "Options", [
        ("option-underlying", "Underlying asset", "options grouped by their reported underlying instrument"),
        ("option-call-put", "Call and put", "call and put contracts where the source identifies the option side"),
        ("option-expiry", "Expiry", "options grouped by available expiry dates or tenor"),
        ("option-strike", "Strike and moneyness", "contracts grouped by strike or moneyness when available"),
        ("option-exchange", "Country and exchange", "options grouped by supported country and trading venue"),
        ("option-style", "Exercise style", "American, European, and other styles where identified by the source"),
    ]),
    ("commodities", "Commodities", [
        ("commodity-precious", "Precious metals and gemstones", "gold, silver, platinum, palladium, and supported gemstone benchmarks"),
        ("commodity-base-metals", "Base and industrial metals", "copper, aluminium, zinc, nickel, lead, and other supported metals"),
        ("commodity-minerals", "Minerals and elements", "iron ore, lithium, cobalt, uranium, coal, and supported mineral markets"),
        ("commodity-gases", "Gas and chemical futures", "gas-linked, fertilizer, and chemical futures available in the provider feed; industrial-gas coverage can be limited"),
        ("commodity-energy", "Energy and fuels", "WTI, Brent, natural gas, gasoline, heating oil, and supported fuels"),
        ("commodity-grains", "Grains and oilseeds", "wheat, corn, soybeans, rice, oats, and supported oilseed markets"),
        ("commodity-fibres-softs", "Fibres and soft commodities", "cotton, jute where available, sugar, coffee, cocoa, and other softs"),
        ("commodity-livestock", "Livestock", "live cattle, lean hogs, and other supported livestock contracts"),
        ("commodity-forestry", "Forestry and building materials", "lumber and other supported forestry or building-material benchmarks"),
    ]),
    ("forex", "Currencies and foreign exchange", [
        ("fx-base-currency", "Base currency", "FX pairs grouped by their base currency"),
        ("fx-quote-currency", "Quote currency", "FX pairs grouped by their quote currency"),
        ("fx-pair-class", "Major, minor, and emerging pairs", "pair classes only where the source can support the classification"),
        ("fx-region", "Country and region", "supported local and regional currency markets"),
        ("fx-venue", "Provider and venue", "pairs grouped by their reported source or trading venue"),
    ]),
    ("crypto-spot", "Cryptocurrency spot markets", [
        ("crypto-major", "Major coins and networks", "Bitcoin, Ethereum, Solana, and other supported networks"),
        ("crypto-stablecoins", "Stablecoins", "stablecoin markets where identified by the source"),
        ("crypto-defi", "Decentralized finance", "supported DeFi assets grouped by available classifications"),
        ("crypto-layer2", "Layer 2 and scaling", "supported scaling-network assets where identifiable"),
        ("crypto-exchange-tokens", "Exchange tokens", "supported exchange-related crypto assets"),
        ("crypto-infrastructure", "Infrastructure and oracles", "supported infrastructure, oracle, and protocol assets"),
        ("crypto-themes", "Gaming, payments, and other themes", "theme classifications only when supported by reliable metadata"),
        ("crypto-quote-venue", "Quote currency and venue", "spot crypto instruments grouped by quote currency or exchange"),
    ]),
    ("crypto-derivatives", "Crypto derivatives", [
        ("cryptoderiv-futures", "Crypto futures", "supported crypto-linked futures contracts"),
        ("cryptoderiv-perpetuals", "Perpetual contracts", "supported perpetual markets where the source identifies them"),
        ("cryptoderiv-options", "Crypto options", "supported crypto option records where available"),
        ("cryptoderiv-underlying", "Underlying crypto asset", "derivatives grouped by their reported underlying asset"),
        ("cryptoderiv-venue", "Exchange and venue", "crypto derivatives grouped by reported trading venue"),
    ]),
    ("economic-data", "Economic indicators", [
        ("econ-growth", "Growth and GDP", "reported GDP and economic-growth indicators"),
        ("econ-inflation", "Inflation and prices", "reported inflation and price indicators"),
        ("econ-employment", "Employment and labour", "reported employment and labour-market indicators"),
        ("econ-rates", "Rates and monetary policy", "reported policy-rate and monetary indicators"),
        ("econ-trade", "Trade and external accounts", "reported trade and external-balance indicators"),
        ("econ-fiscal", "Fiscal and public debt", "reported government-finance and public-debt indicators"),
        ("econ-production", "Production, housing, and sentiment", "other supported production, housing, and sentiment series"),
    ]),
    ("structured-products", "Structured products", [
        ("structured-protection", "Capital protection", "products classified as capital-protected when stated by the source"),
        ("structured-leverage", "Leveraged and inverse", "leveraged or inverse products where provider data identifies them"),
        ("structured-notes-warrants", "Notes and warrants", "supported structured notes, certificates, and warrant records"),
        ("structured-underlying", "Underlying asset", "products grouped by the reported underlying"),
        ("structured-issuer-maturity", "Issuer and maturity", "products grouped by issuer or maturity where available"),
    ]),
    ("reits", "REITs and listed real estate", [
        ("reit-country", "Country and region", "REITs grouped by reported listing country or region"),
        ("reit-property-sector", "Property sector", "residential, retail, industrial, office, and other supported sectors"),
        ("reit-structure", "REIT structure", "equity, mortgage, and other structures when identified"),
        ("reit-market-cap", "Market capitalization", "REITs grouped by reported market-capitalization bands"),
        ("reit-exchange", "Exchange and venue", "REITs grouped by reported listing venue"),
    ]),
    ("other-instruments", "Other and not-yet-classified instruments", [
        ("other-type", "Provider instrument type", "records grouped by the provider's reported instrument type"),
        ("other-subtype", "Provider subtype", "records grouped by the provider's reported subtype"),
        ("other-country", "Country and region", "unclassified records grouped by reported country or region"),
        ("other-exchange", "Exchange and venue", "unclassified records grouped by reported exchange or venue"),
    ]),
]

# Publication order prioritizes the equity, index, and commodity desks that
# replace the most prominent Global Snapshot boards in the first 20-post batch.
BATCH_ORDER = [
    "equity-stocks", "market-indices", "commodities", "depositary-receipts",
    "bonds-fixed-income", "etfs", "index-funds", "mutual-funds", "other-funds",
    "futures", "options", "forex", "crypto-spot", "crypto-derivatives",
    "economic-data", "structured-products", "reits", "other-instruments",
]
BATCH_SIZES = [20, 20, 22, 22, 20]


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def build_catalog() -> list[dict[str, object]]:
    pages: list[dict[str, object]] = []
    ordered = {key: (key, title, cats) for key, title, cats in DIVISION_SPECS}
    cursor = 0
    for division_key in BATCH_ORDER:
        _, division_title, categories = ordered[division_key]
        for category_key, category_title, scope in categories:
            title = f"{division_title}: {category_title} | Milled Edge"
            slug = slugify(f"{division_key}-{category_key}")
            description = (
                f"Explore {scope}. Review the source, data timing, and category methodology; "
                "market values may be delayed and are not executable quotes."
            )
            labels = ["Markets", slugify(division_title), slugify(category_title), "Global Market Data"]
            pages.append({
                "id": slug,
                "slug": slug,
                "division_id": division_key,
                "division": division_title,
                "category_id": category_key,
                "category": category_title,
                "scope": scope,
                "title": title,
                "search_description": description[:155],
                "labels": labels,
            })
    if len(pages) != 104:
        raise ValueError(f"Expected exactly 104 category posts, got {len(pages)}")
    slugs = [p["slug"] for p in pages]
    if len(set(slugs)) != len(slugs):
        raise ValueError("Duplicate category slug")
    start = 0
    for batch, size in enumerate(BATCH_SIZES, 1):
        for page in pages[start:start + size]:
            page["batch"] = batch
        start += size
    if start != 104 or [sum(p["batch"] == b for p in pages) for b in range(1, 6)] != BATCH_SIZES:
        raise ValueError("Batch split must be exactly 20+20+22+22+20")
    return pages
