# 📊 NIFTY 50 Stock Research Monitor
### Automated Fundamental Analysis for Arch Linux

---

## What This Does

Continuously monitors all 50 NIFTY 50 companies and scores each one
across 8 fundamental parameters. Gives you a clear **BUY / WATCH / AVOID**
signal for each stock, so you can research like a proper analyst.

---

## Scoring System (100 pts total)

| Parameter         | Max Score | What's "Good"            |
|-------------------|-----------|--------------------------|
| ROE               | 20 pts    | > 15%                    |
| Debt/Equity       | 15 pts    | < 1.0                    |
| P/E Ratio         | 15 pts    | < 20 = cheap, < 35 = fair|
| Net Profit Margin | 15 pts    | > 15%                    |
| Revenue Growth    | 15 pts    | > 15% YoY                |
| Free Cash Flow    | 10 pts    | Must be positive         |
| Promoter Holding  | 5 pts     | > 50% = high conviction  |
| Dividend Yield    | 5 pts     | > 2% = bonus             |

**Signals:**
- 🟢 Score ≥ 70 → **BUY CANDIDATE** (research further before buying)
- 🟡 Score 50–69 → **WATCHLIST** (monitor, not yet)
- 🔴 Score < 50 → **AVOID**

---

## Setup (One Time)

```bash
cd ~/nifty_monitor
chmod +x setup.sh
./setup.sh
```

Optionally installs a **systemd timer** to auto-scan every 30 min.

---

## Usage

```bash
# Full NIFTY 50 scan with table + signals
./run.sh

# Watch mode — auto-refresh every 30 min in terminal
./run.sh --watch

# Deep dive on a single stock
./run.sh --stock RELIANCE
./run.sh --stock HDFCBANK
./run.sh --stock TCS

# Only show buy/watch/avoid signals (no full table)
./run.sh --alerts

# Export scan results to timestamped CSV
./run.sh --export

# Show only top 10 stocks by score
./run.sh --top 10

# Combine flags
./run.sh --alerts --export
./run.sh --top 15 --export
```

---

## Adding Custom Stocks (Outside NIFTY 50)

Open `stock_monitor.py` and add to the `NIFTY50` dict:

```python
NIFTY50 = {
    ...
    "NIITLTD": "NIITLTD.NS",   # Your existing holding
    "IRFC":    "IRFC.NS",
}
```

Then run:
```bash
./run.sh --stock NIITLTD
```

---

## Adjusting Scoring Thresholds

Edit `THRESHOLDS` dict in `stock_monitor.py`:

```python
THRESHOLDS = {
    "roe_good": 15.0,       # Increase for stricter ROE filter
    "pe_cheap": 20.0,       # Lower for stricter valuation
    "score_buy": 70,        # Raise to 80 to be more selective
    ...
}
```

---

## Output Files

- `nifty_scan_YYYYMMDD_HHMM.csv` — exported scan results
- `scan_log.txt` — systemd timer logs (if timer enabled)

---

## Data Source

Yahoo Finance via `yfinance` library. Data is delayed ~15 min during
market hours. Fundamental data (ROE, margins, etc.) is quarterly/annual.

---

## ⚠️ Disclaimer

This tool is for **research and education only**. Signals are based on
publicly available data and a simple scoring model. Always verify with
Screener.in, company filings, and your own judgment before investing.
**Never invest borrowed money in equities.**
