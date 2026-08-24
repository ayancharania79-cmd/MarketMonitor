#!/usr/bin/env python3
"""Assemble funds.json + quotes.json + news.json into the final dashboard HTML."""
import json, re, sys, datetime, pathlib

TOOLS = pathlib.Path(__file__).parent
BASE = TOOLS.parent
DATA = BASE / "data"

funds_raw = json.load(open(DATA / "funds.json"))
news = json.load(open(DATA / "news.json"))

quotes_path = DATA / "quotes.json"
quotes_list = json.load(open(quotes_path)) if quotes_path.exists() else []
quotes = {(q["exchange"], q["ticker"]): q for q in quotes_list}

FUND_META = {
    "Canadian Equity": {"key": "canadian", "short": "Canadian Equity", "flag": "CA"},
    "US Equity": {"key": "us", "short": "US Equity", "flag": "US"},
    "International Equity": {"key": "intl", "short": "International Equity", "flag": "INTL"},
    "Small Cap Equity": {"key": "smallcap", "short": "Small Cap Equity", "flag": "SC"},
}

funds_out = []
missing = []
for fund_name, fd in funds_raw.items():
    meta = FUND_META[fund_name]
    holdings_out = []
    for h in fd["holdings"]:
        q = quotes.get((h["exchange"], h["ticker"]))
        row = {
            "name": h["name"],
            "ticker": h["ticker"],
            "exchange": h["exchange"],
            "weight": h["weight"],
        }
        if q and q.get("price") is not None:
            row.update({
                "price": q.get("price"),
                "currency": q.get("currency"),
                "change": q.get("change"),
                "changePercent": q.get("changePercent"),
                "asOfDate": q.get("asOfDate"),
                "displaySymbol": q.get("displaySymbol") or h["ticker"],
                "sourceUrl": q.get("sourceUrl"),
            })
        else:
            row.update({
                "price": None, "currency": None, "change": None,
                "changePercent": None, "asOfDate": None,
                "displaySymbol": h["ticker"], "sourceUrl": None,
            })
            missing.append(f'{h["exchange"]}:{h["ticker"]} ({fund_name})')
        holdings_out.append(row)
    holdings_out.sort(key=lambda r: -r["weight"])
    funds_out.append({
        "key": meta["key"],
        "name": fund_name,
        "short": meta["short"],
        "currency": fd["currency"],
        "cashFxWeight": fd["cash_fx_weight"],
        "holdings": holdings_out,
    })

total_holdings = sum(len(f["holdings"]) for f in funds_out)
priced = sum(1 for f in funds_out for h in f["holdings"] if h["price"] is not None)

data = {
    "generatedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "funds": funds_out,
    "news": news,
    "meta": {
        "totalPositions": total_holdings,
        "pricedPositions": priced,
    },
}

template = (TOOLS / "dashboard_template.html").read_text()
out_html = template.replace(
    "/*__DATA__*/{}",
    json.dumps(data, ensure_ascii=False)
)

out_path = BASE / "dashboard.html"
out_path.write_text(out_html)
print(f"Wrote {out_path} ({len(out_html):,} bytes)")
print(f"Priced {priced}/{total_holdings} positions")
if missing:
    print(f"Missing quotes for {len(missing)}: {missing[:15]}{'...' if len(missing)>15 else ''}")
