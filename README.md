# Market Monitor

A single-page dashboard tracking every holding across four Dixon Mitchell equity
mandates — Canadian Equity, US Equity, International Equity, and Small Cap Equity —
with prices and curated market news, published as a Claude Artifact.

## How it works

Holdings and weights come from the four `DM_*.xlsx` fund reports and are frozen in
`data/funds.json`. Prices/changes and curated news are gathered separately (there is
no live market-data connector wired into the published page — see *Why not
real-time* below) and stored in `data/quotes.json` / `data/news.json`. The dashboard
itself is a static, self-contained HTML file built from those three JSON files plus
`tools/dashboard_template.html`.

```
data/funds.json      fund -> holdings (name, ticker, exchange, weight), extracted once from the xlsx reports
data/tickers.json    the 103 unique (exchange, ticker) pairs across all four funds
data/quotes.json     latest price/change snapshot per ticker (refreshed periodically)
data/news.json       curated headlines for the largest/most impactful holdings
tools/dashboard_template.html   page shell (HTML/CSS/JS) with a `/*__DATA__*/{}` placeholder
tools/build.py        merges the three JSON files into the template -> dashboard.html
dashboard.html        generated output, published as the Artifact
```

## Refreshing the data

```
python3 tools/build.py
```

reassembles `dashboard.html` from whatever is currently in `data/quotes.json` and
`data/news.json`. To actually refresh those:

1. Re-fetch a price snapshot for every entry in `data/tickers.json` and overwrite
   `data/quotes.json` in the same shape. Use **WebSearch only** — this
   environment's network egress policy blocks WebFetch for essentially every
   finance domain (stockanalysis.com, finance.yahoo.com, investing.com,
   tradingview.com, cnbc.com, marketwatch.com, wsj.com, google.com,
   wallstreetzen.com all return `EGRESS_BLOCKED`), so search-snippet prices are
   the only reliable source. See the agent prompt used originally, preserved in
   git history / the "Market Monitor refresh" Routine, for the exact method.
2. Optionally refresh `data/news.json` with current headlines for the
   largest-weighted holdings.
3. Run `python3 tools/build.py`.
4. Publish `dashboard.html` to the existing Artifact URL (update in place, not a
   new artifact).
5. Commit and push the updated `data/*.json` and `dashboard.html`.

A scheduled Routine runs this on a recurring basis on market days — see the Routine
named "Market Monitor Refresh" for the exact cadence and prompt.

## Why not real-time

The dashboard is a sandboxed Claude Artifact: its JavaScript can't call arbitrary
external APIs, so it can't poll a market-data feed itself. Two connector-based
options were tried and didn't pan out for this account: **Twelve Data**'s OAuth
sign-in failed at registration, and **LSEG**, while connected, has no
pricing/news entitlements enabled. Until one of those is fixed, prices are a
periodically-refreshed snapshot (see the "Updated ..." timestamp in the page
header) rather than a live tick-by-tick feed.
