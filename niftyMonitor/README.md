# niftyMonitor — Market Research Monitor

> A terminal market-research scanner: scores Indian equities on fundamentals and
> flags **BUY / WATCH / AVOID**, with crypto, metals, and forex thrown in.
> `v3.0`.

A Python CLI that pulls quotes and fundamentals, scores each stock across 8
parameters out of 100, and prints colour-coded signals in a rich terminal table.
Covers the NIFTY 50 plus **27 sectors (~270 stocks)**, and extends to crypto,
precious metals, forex, and US stocks.

---

## What It Scans

| Mode | Flag | Covers |
|------|------|--------|
| NIFTY 50 fundamental scan | _(default)_ | All 50 NIFTY companies, scored + signalled |
| Sector scan | `--sectorscan` | 27 sectors × ~10 stocks (~270 names) |
| Single sector | `--sector IT` | One sector's stocks (`--listsectors` to enumerate) |
| Single-stock deep dive | `--stock RELIANCE` | Full breakdown for one ticker |
| Price levels | `--levels` | Support/resistance levels for NIFTY 50 |
| Crypto | `--crypto` | BTC, ETH, and top crypto |
| Metals | `--metals` | Gold & silver (INR + USD) |
| Forex | `--forex` | Top currencies vs USD |
| US stocks | `--usstocks` | US equities |
| Everything | `--all` | All of the above in one run |

Output controls: `--alerts` (signals only), `--top N`, `--export` (timestamped
CSV), `--watch` (auto-refresh), `--interval MIN`, `--listsectors`.

---

## Scoring (100 pts)

| Parameter | Max | "Good" |
|-----------|-----|--------|
| ROE | 20 | > 15% |
| Debt / Equity | 15 | < 1.0 |
| P/E ratio | 15 | < 20 cheap, < 35 fair |
| Net profit margin | 15 | > 15% |
| Revenue growth | 15 | > 15% YoY |
| Free cash flow | 10 | positive |
| Promoter holding | 5 | > 50% |
| Dividend yield | 5 | > 2% |

**Signals:** score >= 70 -> BUY CANDIDATE · 50-69 -> WATCHLIST · < 50 -> AVOID.
(The live terminal output uses green/amber/red indicators for these.)

---

## Setup

```bash
cd niftyMonitor
./setup.sh          # creates .venv, installs deps; optional systemd timer
```

Optional — the crypto/metals/forex/US modes use **Twelve Data** as the primary
source and fall back to Yahoo Finance. To enable them, drop a free API key at:

```
~/.config/stock_monitor/twelvedata_key
```

The key is read from that file at runtime — never hard-coded or committed.
NIFTY/sector fundamentals work on Yahoo Finance alone, no key needed.

---

## Usage

```bash
./run.sh                       # NIFTY 50 scan with table + signals
./run.sh --sectorscan          # all 27 sectors
./run.sh --sector PHARMA       # one sector
./run.sh --stock HDFCBANK      # single-stock deep dive
./run.sh --alerts --export     # signals only, save to CSV
./run.sh --top 15              # top 15 by score
./run.sh --watch --interval 30 # auto-refresh every 30 min
./run.sh --listsectors         # list sectors and their stocks
```

---

## Add Your Own Stocks / Tune Scoring

Add tickers to the `NIFTY50` / `SECTORS` structures in `stock_monitor.py`
(`"NIITLTD": "NIITLTD.NS"`), or adjust the `THRESHOLDS` dict to make the filters
stricter (e.g. raise `score_buy` to 80, lower `pe_cheap`).

---

## Data & Limits

- **Yahoo Finance** (`yfinance`) for equities; data is delayed ~15 min during
  market hours, fundamentals are quarterly/annual.
- **Twelve Data** free tier: 8 calls/min, 800/day — used for crypto/forex/metals.

---

## Disclaimer

For **research and education only**. Signals come from public data and a simple
scoring model — always verify against company filings and your own judgment
before investing, and never invest borrowed money.
