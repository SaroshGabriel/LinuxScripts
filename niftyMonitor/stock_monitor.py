#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║        NIFTY 50 STOCK RESEARCH MONITOR  v2.0                 ║
║        Fundamental + Technical Price Levels                  ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    python stock_monitor.py                  → Full fundamental scan
    python stock_monitor.py --levels         → + Buy/Target/Stoploss table
    python stock_monitor.py --watch          → Auto-refresh every 30 min
    python stock_monitor.py --stock RELIANCE → Single stock deep dive + levels
    python stock_monitor.py --alerts         → Only buy/avoid signals
    python stock_monitor.py --export         → Save report to CSV
    python stock_monitor.py --top 10         → Top 10 by score
"""

import yfinance as yf
import pandas as pd
import time
import os
import csv
import argparse
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.rule import Rule

console = Console()

# ─────────────────────────────────────────────────────────────
# NIFTY 50 TICKERS
# ─────────────────────────────────────────────────────────────
NIFTY50 = {
    "RELIANCE":   "RELIANCE.NS",  "TCS":        "TCS.NS",
    "HDFCBANK":   "HDFCBANK.NS",  "BHARTIARTL": "BHARTIARTL.NS",
    "ICICIBANK":  "ICICIBANK.NS", "INFOSYS":    "INFY.NS",
    "SBIN":       "SBIN.NS",      "HINDUNILVR": "HINDUNILVR.NS",
    "ITC":        "ITC.NS",       "LT":         "LT.NS",
    "KOTAKBANK":  "KOTAKBANK.NS", "BAJFINANCE": "BAJFINANCE.NS",
    "ASIANPAINT": "ASIANPAINT.NS","AXISBANK":   "AXISBANK.NS",
    "MARUTI":     "MARUTI.NS",    "HCLTECH":    "HCLTECH.NS",
    "SUNPHARMA":  "SUNPHARMA.NS", "TITAN":      "TITAN.NS",
    "ULTRACEMCO": "ULTRACEMCO.NS","WIPRO":      "WIPRO.NS",
    "NESTLEIND":  "NESTLEIND.NS", "POWERGRID":  "POWERGRID.NS",
    "NTPC":       "NTPC.NS",      "ONGC":       "ONGC.NS",
    "TATAMOTORS": "TATAMOTORS.NS","ADANIENT":   "ADANIENT.NS",
    "TATASTEEL":  "TATASTEEL.NS", "BAJAJFINSV": "BAJAJFINSV.NS",
    "JSWSTEEL":   "JSWSTEEL.NS",  "TECHM":      "TECHM.NS",
    "COALINDIA":  "COALINDIA.NS", "GRASIM":     "GRASIM.NS",
    "DIVISLAB":   "DIVISLAB.NS",  "CIPLA":      "CIPLA.NS",
    "DRREDDY":    "DRREDDY.NS",   "EICHERMOT":  "EICHERMOT.NS",
    "HINDALCO":   "HINDALCO.NS",  "INDUSINDBK": "INDUSINDBK.NS",
    "M&M":        "M&M.NS",       "ADANIPORTS": "ADANIPORTS.NS",
    "BRITANNIA":  "BRITANNIA.NS", "HDFCLIFE":   "HDFCLIFE.NS",
    "SBILIFE":    "SBILIFE.NS",   "TATACONSUM": "TATACONSUM.NS",
    "APOLLOHOSP": "APOLLOHOSP.NS","BAJAJ-AUTO":  "BAJAJ-AUTO.NS",
    "BPCL":       "BPCL.NS",      "HEROMOTOCO": "HEROMOTOCO.NS",
    "SHRIRAMFIN": "SHRIRAMFIN.NS","TRENT":      "TRENT.NS",
}

# ─────────────────────────────────────────────────────────────
# SCORING + ATR THRESHOLDS
# ─────────────────────────────────────────────────────────────
T = {
    "roe_good": 15.0, "roe_ok": 10.0,
    "de_safe":   1.0, "de_ok":   2.0,
    "pe_cheap": 20.0, "pe_fair": 35.0,
    "nm_good":  15.0, "nm_ok":    8.0,
    "rg_good":  15.0, "rg_ok":    5.0,
    "score_buy": 70,  "score_watch": 50,
    "atr_sl":    1.5,   # stoploss = support - 1.5 * ATR
    "atr_rr":    2.0,   # minimum risk:reward ratio
}


# ─────────────────────────────────────────────────────────────
# 1. FUNDAMENTAL DATA FETCH
# ─────────────────────────────────────────────────────────────
def fetch_fundamentals(symbol: str, name: str) -> dict:
    try:
        tk   = yf.Ticker(symbol)
        info = tk.info

        price    = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        mktcap   = info.get("marketCap", 0)
        w52h     = info.get("fiftyTwoWeekHigh", 0)
        w52l     = info.get("fiftyTwoWeekLow",  0)

        de = info.get("debtToEquity")
        if de: de /= 100

        hist      = tk.history(period="1y")
        p_old     = float(hist["Close"].iloc[0])  if len(hist) > 1 else None
        p_now     = float(hist["Close"].iloc[-1]) if len(hist) > 1 else price
        ann_ret   = round((p_now - p_old) / p_old * 100, 2) if p_old else None

        fcf = info.get("freeCashflow")

        return dict(
            name=name, ticker=symbol, error=None,
            sector=info.get("sector","N/A"), industry=info.get("industry","N/A"),
            price=price,
            market_cap_cr=round(mktcap/1e7) if mktcap else None,
            pe=round(info.get("trailingPE") or info.get("forwardPE") or 0, 2) or None,
            pb=round(info.get("priceToBook") or 0, 2) or None,
            ev_ebitda=round(info.get("enterpriseToEbitda") or 0, 2) or None,
            roe=round((info.get("returnOnEquity")   or 0)*100, 2),
            net_margin=round((info.get("profitMargins")    or 0)*100, 2),
            gross_margin=round((info.get("grossMargins")   or 0)*100, 2),
            op_margin=round((info.get("operatingMargins")  or 0)*100, 2),
            de=round(de, 2) if de else None,
            cur_ratio=round(info.get("currentRatio") or 0, 2) or None,
            qk_ratio=round(info.get("quickRatio")    or 0, 2) or None,
            rev_gr=round((info.get("revenueGrowth")  or 0)*100, 2),
            earn_gr=round((info.get("earningsGrowth")or 0)*100, 2),
            div_yld=round((info.get("dividendYield") or 0)*100, 2),
            payout=round((info.get("payoutRatio")    or 0)*100, 2),
            insider=round((info.get("heldPercentInsiders")    or 0)*100, 2),
            inst=round((info.get("heldPercentInstitutions")   or 0)*100, 2),
            fcf_cr=round(fcf/1e7) if fcf else None,
            ann_ret=ann_ret,
            w52h=w52h, w52l=w52l,
            from_52h=round((price-w52h)/w52h*100,2) if w52h else None,
            from_52l=round((price-w52l)/w52l*100,2) if w52l else None,
        )
    except Exception as e:
        return dict(name=name, ticker=symbol, error=str(e)[:100])


# ─────────────────────────────────────────────────────────────
# 2. TECHNICAL PRICE LEVELS  (ATR + Support/Resistance)
# ─────────────────────────────────────────────────────────────
def fetch_price_levels(symbol: str) -> dict:
    """
    Calculates:
      - ATR-14 (volatility measure)
      - Swing-low support & swing-high resistance (3-month)
      - Buy zone: near support
      - Stoploss: support - 1.5 * ATR  (volatility-adjusted)
      - Target 1: buy + 2 * risk  (1:2 R:R minimum)
      - Target 2: next resistance  (technical ceiling)
      - Target 3: 52-week high  (breakout target)
      - 52W and all-time context
      - 200-SMA trend direction
    """
    try:
        tk    = yf.Ticker(symbol)
        h6    = tk.history(period="6mo")
        h5    = tk.history(period="5y")
        h1    = tk.history(period="1y")

        if len(h6) < 20:
            return {"error": "Insufficient history"}

        cl = h6["Close"]; hi = h6["High"]; lo = h6["Low"]

        cp   = float(cl.iloc[-1])
        w52h = float(hi.max()); w52l = float(lo.min())
        ath  = float(h5["High"].max()) if len(h5)>5 else w52h
        atl  = float(h5["Low"].min())  if len(h5)>5 else w52l

        # ATR-14
        pc  = cl.shift(1)
        tr  = pd.concat([hi-lo, (hi-pc).abs(), (lo-pc).abs()], axis=1).max(axis=1)
        atr = float(tr.rolling(14).mean().iloc[-1])

        # Swing lows / highs over last 3 months (~63 trading days)
        rec  = h6.tail(63)
        rlo  = rec["Low"].values;  rhi = rec["High"].values

        sups, ress = [], []
        for i in range(2, len(rlo)-2):
            if rlo[i] < rlo[i-1] and rlo[i] < rlo[i+1] and \
               rlo[i] < rlo[i-2] and rlo[i] < rlo[i+2]:
                sups.append(float(rlo[i]))
        for i in range(2, len(rhi)-2):
            if rhi[i] > rhi[i-1] and rhi[i] > rhi[i+1] and \
               rhi[i] > rhi[i-2] and rhi[i] > rhi[i+2]:
                ress.append(float(rhi[i]))

        sups_below = sorted([s for s in sups if s < cp], reverse=True)
        ress_above = sorted([r for r in ress if r > cp])

        support    = sups_below[0] if sups_below else float(rlo.min())
        resistance = ress_above[0] if ress_above else float(rhi.max())

        # Buy zone: enter near support (if already near support, use current price)
        buy   = round(cp if cp <= support + 1.5*atr else support + 0.5*atr, 2)
        buy_h = round(buy + atr, 2)

        # Stoploss: below support, 1.5 ATR clearance
        sl    = round(support - T["atr_sl"] * atr, 2)
        risk  = round(buy - sl, 2)

        # Targets
        t1    = round(buy + T["atr_rr"] * risk, 2)      # 1:2 R:R
        t2    = round(resistance, 2)                     # next resistance
        t3    = round(w52h, 2)                           # 52W high breakout

        reward = max(t1, t2) - buy
        rr     = round(reward / risk, 2) if risk > 0 else 0

        # 200-SMA trend
        sma200    = float(h1["Close"].rolling(200).mean().iloc[-1]) if len(h1)>=200 else None
        above_200 = (cp > sma200) if sma200 else None

        # Position sizing per ₹10,000
        shares_10k = int(10000 / buy) if buy > 0 else 0
        max_loss   = round(shares_10k * risk, 2)

        rng_pct = round((cp-w52l)/(w52h-w52l)*100, 1) if (w52h-w52l)>0 else 50

        return dict(
            error=None,
            cp=round(cp,2), atr=round(atr,2),
            w52h=w52h, w52l=w52l, ath=round(ath,2), atl=round(atl,2),
            rng_pct=rng_pct,
            support=round(support,2), resistance=round(resistance,2),
            all_supports   =[round(s,2) for s in sups_below[:3]],
            all_resistances=[round(r,2) for r in ress_above[:3]],
            buy=buy, buy_h=buy_h,
            sl=sl, risk=risk,
            t1=t1, t1_pct=round((t1-cp)/cp*100,1),
            t2=t2, t2_pct=round((t2-cp)/cp*100,1),
            t3=t3, t3_pct=round((t3-cp)/cp*100,1),
            rr=rr,
            sl_pct=round((cp-sl)/cp*100,1),
            sma200=round(sma200,2) if sma200 else None,
            above_200=above_200,
            shares_10k=shares_10k, max_loss=max_loss,
        )
    except Exception as e:
        return {"error": str(e)[:100]}


# ─────────────────────────────────────────────────────────────
# 3. SCORING ENGINE
# ─────────────────────────────────────────────────────────────
def score_stock(d: dict):
    sc, green, red = 0, [], []

    roe = d.get("roe", 0) or 0
    if   roe >= T["roe_good"]: sc+=20; green.append(f"ROE {roe:.1f}% (>15% ✓)")
    elif roe >= T["roe_ok"]:   sc+=10; green.append(f"ROE {roe:.1f}% (>10% ok)")
    else:                                red.append(f"ROE {roe:.1f}% (<10% weak)")

    de = d.get("de")
    if   de is None:            sc+=8
    elif de <= T["de_safe"]:    sc+=15; green.append(f"D/E {de:.2f} (low debt ✓)")
    elif de <= T["de_ok"]:      sc+=7;  green.append(f"D/E {de:.2f} (moderate)")
    else:                                red.append(f"D/E {de:.2f} (high debt ✗)")

    pe = d.get("pe")
    if   pe is None:       sc+=5
    elif pe <= 0:                        red.append(f"P/E {pe} (negative earnings ✗)")
    elif pe <= T["pe_cheap"]: sc+=15; green.append(f"P/E {pe:.1f} (cheap <20 ✓)")
    elif pe <= T["pe_fair"]:  sc+=8;  green.append(f"P/E {pe:.1f} (fair <35)")
    else:                                red.append(f"P/E {pe:.1f} (expensive >35 ✗)")

    nm = d.get("net_margin", 0) or 0
    if   nm >= T["nm_good"]: sc+=15; green.append(f"Net margin {nm:.1f}% (>15% ✓)")
    elif nm >= T["nm_ok"]:   sc+=8;  green.append(f"Net margin {nm:.1f}% (>8% ok)")
    elif nm > 0:             sc+=3;   red.append(f"Net margin {nm:.1f}% (thin)")
    else:                              red.append(f"Net margin {nm:.1f}% (loss ✗)")

    rg = d.get("rev_gr", 0) or 0
    if   rg >= T["rg_good"]: sc+=15; green.append(f"Rev growth {rg:.1f}% (>15% ✓)")
    elif rg >= T["rg_ok"]:   sc+=8;  green.append(f"Rev growth {rg:.1f}% (>5% ok)")
    elif rg > 0:             sc+=3;   red.append(f"Rev growth {rg:.1f}% (slow)")
    else:                              red.append(f"Rev growth {rg:.1f}% (shrinking ✗)")

    fcf = d.get("fcf_cr")
    if   fcf and fcf > 0: sc+=10; green.append(f"FCF ₹{fcf:.0f}Cr (positive ✓)")
    elif fcf and fcf < 0:           red.append(f"FCF ₹{fcf:.0f}Cr (burning cash ✗)")

    ins = d.get("insider", 0) or 0
    if   ins >= 50: sc+=5; green.append(f"Promoter {ins:.1f}% (high conviction ✓)")
    elif ins >= 30: sc+=3; green.append(f"Promoter {ins:.1f}% (ok)")
    else:                   red.append(f"Promoter {ins:.1f}% (low skin-in-game)")

    dy = d.get("div_yld", 0) or 0
    if   dy >= 2: sc+=5; green.append(f"Div yield {dy:.1f}% (income ✓)")
    elif dy > 0:  sc+=2

    return min(sc, 100), green, red


def sig(score):
    if score >= T["score_buy"]:   return "🟢 BUY CANDIDATE", "green"
    if score >= T["score_watch"]: return "🟡 WATCHLIST",     "yellow"
    return                               "🔴 AVOID",         "red"


# ─────────────────────────────────────────────────────────────
# 4. DISPLAY: FUNDAMENTAL TABLE
# ─────────────────────────────────────────────────────────────
def show_fundamentals(results):
    tbl = Table(
        title=f"📊 NIFTY 50 — Fundamental Scan  {datetime.now():%d %b %Y %H:%M}",
        box=box.ROUNDED, show_lines=True,
        header_style="bold cyan", title_style="bold white on dark_blue",
    )
    cols = [
        ("Company","bold white",14,"left"),  ("Price ₹","",9,"right"),
        ("Score","",7,"center"),             ("Signal","",17,"center"),
        ("P/E","",6,"right"),                ("ROE%","",7,"right"),
        ("D/E","",6,"right"),                ("Net M%","",8,"right"),
        ("RevGr%","",8,"right"),             ("FCF ₹Cr","",9,"right"),
        ("52W Pos","",10,"center"),          ("1Y Ret%","",8,"right"),
    ]
    for c,s,w,j in cols:
        tbl.add_column(c, style=s, width=w, justify=j)

    def f(v, sfx="", neg_red=True):
        if v is None: return "[dim]N/A[/dim]"
        s = f"{v}{sfx}"
        return f"[red]{s}[/red]" if neg_red and isinstance(v,(int,float)) and v<0 else s

    pool = sorted([r for r in results if not r.get("error")],
                  key=lambda x: x.get("score",0), reverse=True)
    pool += [r for r in results if r.get("error")]

    for d in pool:
        if d.get("error"):
            tbl.add_row(d["name"][:13],"—","—","[red]ERR[/red]","—","—","—","—","—","—","—","—")
            continue
        sc = d["score"]; label, col = sig(sc)
        ret = d.get("ann_ret")
        ret_s = f"[green]+{ret}%[/green]" if ret and ret>0 else f(ret,"%")
        l = d.get("from_52l"); h = d.get("from_52h")
        w52s = f"+{l:.0f}%/{h:.0f}%" if l is not None and h is not None else "N/A"
        tbl.add_row(
            d["name"][:13], f"₹{d['price']:.1f}" if d.get("price") else "—",
            f"[{col}]{sc}[/{col}]", f"[{col}]{label}[/{col}]",
            f(d.get("pe")), f(d.get("roe")), f(d.get("de")),
            f(d.get("net_margin")), f(d.get("rev_gr")), f(d.get("fcf_cr")),
            w52s, ret_s,
        )
    console.print(tbl)


# ─────────────────────────────────────────────────────────────
# 5. DISPLAY: PRICE LEVELS TABLE  (all stocks)
# ─────────────────────────────────────────────────────────────
def show_levels_table(results):
    tbl = Table(
        title=f"📈 Price Levels — 52W Range / Buy / Stoploss / Targets  "
              f"{datetime.now():%d %b %Y %H:%M}",
        box=box.ROUNDED, show_lines=True,
        header_style="bold magenta", title_style="bold white on dark_blue",
    )
    for c,w,j in [
        ("Company",13,"left"),    ("Now ₹",8,"right"),
        ("52W Low",9,"right"),    ("52W High",9,"right"),
        ("52W Pos",10,"center"),  ("BUY ZONE ₹",15,"center"),
        ("STOPLOSS ₹",11,"right"),("SL%",6,"right"),
        ("Target 1 ₹",12,"right"),("Target 2 ₹",12,"right"),
        ("Target 3 ₹",12,"right"),("R:R",6,"center"),
        ("ATR ₹",7,"right"),      ("Trend",9,"center"),
        ("Signal",17,"center"),
    ]:
        tbl.add_column(c, width=w, justify=j)

    pool = sorted([r for r in results if not r.get("error")],
                  key=lambda x: x.get("score",0), reverse=True)

    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as prog:
        task = prog.add_task("Fetching levels...", total=len(pool))
        for d in pool:
            prog.update(task, description=f"[magenta]Levels[/magenta] {d['name']}")
            lv = fetch_price_levels(d["ticker"])
            time.sleep(0.25)
            prog.advance(task)

            sc = d.get("score",0); label, col = sig(sc)
            if lv.get("error"):
                tbl.add_row(d["name"][:12], f"₹{d.get('price','?')}",
                            *["—"]*12, f"[{col}]{label}[/{col}]"); continue

            rp = lv["rng_pct"]
            rng_s = (f"[green]{rp}%↙low[/green]"  if rp<30 else
                     f"[yellow]{rp}%mid[/yellow]"  if rp<65 else
                     f"[red]{rp}%↗high[/red]")

            rr    = lv["rr"]
            rr_s  = f"[green]1:{rr}[/green]" if rr>=2 else f"[yellow]1:{rr}[/yellow]"

            trend = ("[green]↑ SMA200[/green]"  if lv.get("above_200") else
                     "[red]↓ SMA200[/red]"       if lv.get("above_200") is False else
                     "[dim]N/A[/dim]")

            tbl.add_row(
                d["name"][:12],
                f"₹{lv['cp']}",
                f"₹{lv['w52l']}", f"₹{lv['w52h']}",
                rng_s,
                f"[green]₹{lv['buy']} – {lv['buy_h']}[/green]",
                f"[red]₹{lv['sl']}[/red]",
                f"[red]-{lv['sl_pct']}%[/red]",
                f"[cyan]₹{lv['t1']} (+{lv['t1_pct']}%)[/cyan]",
                f"[cyan]₹{lv['t2']} (+{lv['t2_pct']}%)[/cyan]",
                f"[cyan]₹{lv['t3']} (+{lv['t3_pct']}%)[/cyan]",
                rr_s, f"₹{lv['atr']}", trend,
                f"[{col}]{label}[/{col}]",
            )
    console.print(tbl)


# ─────────────────────────────────────────────────────────────
# 6. DISPLAY: SINGLE STOCK DEEP DIVE
# ─────────────────────────────────────────────────────────────
def show_deep_dive(name: str, symbol: str):
    console.print(Rule(f"[bold cyan]{name} ({symbol}) — Full Deep Dive[/bold cyan]"))

    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as prog:
        t1 = prog.add_task(f"Fundamentals…", total=None)
        d  = fetch_fundamentals(symbol, name)
        prog.remove_task(t1)
        t2 = prog.add_task(f"Price levels…", total=None)
        lv = fetch_price_levels(symbol)
        prog.remove_task(t2)

    if d.get("error"):
        console.print(f"[red]Error: {d['error']}[/red]"); return

    sc, green, red = score_stock(d)
    label, col = sig(sc)

    # Overview
    console.print(Panel(
        f"[bold]Sector:[/bold] {d['sector']}   [bold]Industry:[/bold] {d['industry']}\n"
        f"[bold]Market Cap:[/bold] ₹{d.get('market_cap_cr','?')} Cr   "
        f"[bold]Price:[/bold] ₹{d.get('price','?')}   "
        f"[bold]1Y Return:[/bold] {d.get('ann_ret','?')}%",
        title="Overview", border_style="cyan"))

    # Score
    bar = "█"*int(sc/5) + "░"*(20-int(sc/5))
    console.print(Panel(f"[{col}]{bar}  {sc}/100[/{col}]\n[{col}]{label}[/{col}]",
                        title="Fundamental Score", border_style=col))

    # Flags
    g = Text(); [g.append(f"  ✅ {x}\n","green") for x in green]
    r = Text(); [r.append(f"  ❌ {x}\n","red")   for x in red]
    if not green: g.append("  (none)","dim")
    if not red:   r.append("  (none)","dim")
    console.print(Panel(g, title="[green]Green Flags[/green]", border_style="green"))
    console.print(Panel(r, title="[red]Red Flags[/red]",       border_style="red"))

    # Detailed metrics
    mt = Table(box=box.SIMPLE, header_style="bold magenta", show_header=True)
    mt.add_column("Metric",  width=24)
    mt.add_column("Value",   justify="right", width=14)
    mt.add_column("Verdict", width=24)

    def mrow(metric, val, verdict, good):
        c = "green" if good else "red"
        mt.add_row(metric,
                   str(val) if val is not None else "[dim]N/A[/dim]",
                   f"[{c}]{verdict}[/{c}]")

    pe=d.get("pe"); de=d.get("de"); roe=d.get("roe",0) or 0
    nm=d.get("net_margin",0) or 0; rg=d.get("rev_gr",0) or 0
    eg=d.get("earn_gr",0) or 0;    fcf=d.get("fcf_cr")
    cr=d.get("cur_ratio");          ins=d.get("insider",0) or 0

    mrow("P/E Ratio",          pe,    "Cheap(<20)✓" if pe and pe<20 else "Fair(<35)" if pe and pe<35 else "Expensive", pe and 0<pe<35)
    mrow("P/B Ratio",          d.get("pb"), "Undervalued" if d.get("pb") and d["pb"]<1 else "Fair+", d.get("pb") and d["pb"]<3)
    mrow("EV/EBITDA",          d.get("ev_ebitda"), "Good(<15)" if d.get("ev_ebitda") and d["ev_ebitda"]<15 else "High", d.get("ev_ebitda") and d["ev_ebitda"]<15)
    mrow("ROE %",              f"{roe:.1f}%",  "Strong(>15%)✓" if roe>=15 else "OK(>10%)" if roe>=10 else "Weak",  roe>=10)
    mrow("Net Margin %",       f"{nm:.1f}%",   "Healthy(>15%)✓" if nm>=15 else "OK(>8%)" if nm>=8 else "Thin",     nm>=8)
    mrow("Gross Margin %",     f"{d.get('gross_margin',0):.1f}%", "Good(>30%)" if d.get("gross_margin",0)>=30 else "Moderate", d.get("gross_margin",0)>=30)
    mrow("Op Margin %",        f"{d.get('op_margin',0):.1f}%",    "Good(>15%)" if d.get("op_margin",0)>=15 else "Moderate",    d.get("op_margin",0)>=15)
    mrow("Debt/Equity",        de,    "Safe(<1)✓" if de and de<1 else "Moderate" if de and de<2 else "High Debt",   de and de<1)
    mrow("Current Ratio",      cr,    "Liquid(>1.5)✓" if cr and cr>=1.5 else "Tight",   cr and cr>=1.5)
    mrow("Revenue Growth %",   f"{rg:.1f}%",   "Strong(>15%)✓" if rg>=15 else "OK(>5%)" if rg>=5 else "Slow/Shrink", rg>=5)
    mrow("Earnings Growth %",  f"{eg:.1f}%",   "Strong(>15%)✓" if eg>=15 else "OK(>5%)" if eg>=5 else "Slow",      eg>=5)
    mrow("Free Cash Flow ₹Cr", fcf,   "Positive✓" if fcf and fcf>0 else "Negative✗",    fcf and fcf>0)
    mrow("Promoter Holding %", f"{ins:.1f}%",  "High(>50%)✓" if ins>=50 else "OK(>30%)" if ins>=30 else "Low",     ins>=30)
    mrow("Institutional %",    f"{d.get('inst',0):.1f}%", "Well held(>20%)✓" if d.get("inst",0)>=20 else "Less coverage", d.get("inst",0)>=20)
    mrow("Dividend Yield %",   f"{d.get('div_yld',0):.1f}%", "Good income(>2%)✓" if d.get("div_yld",0)>=2 else "Nominal", d.get("div_yld",0)>=1)
    console.print(mt)

    # ── PRICE LEVELS ────────────────────────────────────────
    if lv.get("error"):
        console.print(f"[red]Price levels: {lv['error']}[/red]"); return

    cp=lv["cp"]; sl=lv["sl"]; buy=lv["buy"]; buy_h=lv["buy_h"]
    t1=lv["t1"]; t2=lv["t2"]; t3=lv["t3"]
    w52h=lv["w52h"]; w52l=lv["w52l"]
    sup=lv["support"]; res=lv["resistance"]
    ath=lv["ath"];     atl=lv["atl"]

    def ladder_row(label, price, color, marker="◀"):
        span = w52h - w52l
        pct  = max(0, min(1, (price-w52l)/span)) if span>0 else 0.5
        pos  = int(pct * 30)
        bar  = "─"*pos + marker + "─"*(30-pos)
        return f"[{color}]{label:12s} ₹{price:<10.2f}|{bar}|[/{color}]"

    ladder = "\n".join([
        ladder_row("ATH",       ath,  "dim",    "▲"),
        ladder_row("52W HIGH",  w52h, "dim",    "▲"),
        ladder_row("TARGET 3",  t3,   "green",  "🏁"),
        ladder_row("TARGET 2",  t2,   "green",  "🎯"),
        ladder_row("TARGET 1",  t1,   "green",  "🎯"),
        ladder_row("RESIST",    res,  "yellow", "┤"),
        ladder_row("CURRENT",   cp,   "cyan",   "●"),
        ladder_row("BUY ZONE",  buy,  "green",  "▶"),
        ladder_row("SUPPORT",   sup,  "yellow", "├"),
        ladder_row("STOPLOSS",  sl,   "red",    "✂"),
        ladder_row("52W LOW",   w52l, "dim",    "▼"),
        ladder_row("ATL",       atl,  "dim",    "▼"),
    ])

    rng = lv["rng_pct"]
    entry_hint = (
        "[green]Near 52W low — good entry zone[/green]"   if rng<30 else
        "[yellow]Mid-range — wait for pullback to buy zone[/yellow]" if rng<65 else
        "[red]Near 52W high — risky to enter now, wait for correction[/red]"
    )
    trend_txt = (
        f"[green]Price above 200-SMA (₹{lv.get('sma200','?')}) → uptrend ✓[/green]"
        if lv.get("above_200") else
        f"[red]Price below 200-SMA (₹{lv.get('sma200','?')}) → downtrend ✗[/red]"
        if lv.get("above_200") is False else "[dim]200-SMA N/A[/dim]"
    )

    detail = (
        f"\n"
        f"  [bold white]ATR-14:[/bold white]         ₹{lv['atr']}  "
        f"← average daily volatility (stoploss = {T['atr_sl']}× ATR below support)\n"
        f"\n"
        f"  [bold green]BUY ZONE   :[/bold green]  ₹{buy} → ₹{buy_h}   ← Enter anywhere in this range\n"
        f"  [bold red]STOPLOSS   :[/bold red]  ₹{sl}   ← Exit immediately if this is hit  "
        f"([red]-{lv['sl_pct']}% from buy, risk ₹{lv['risk']}/share[/red])\n"
        f"\n"
        f"  [bold cyan]TARGET 1   :[/bold cyan]  ₹{t1}  ([cyan]+{lv['t1_pct']}%[/cyan])  "
        f"← Minimum 1:2 R:R — book partial here\n"
        f"  [bold cyan]TARGET 2   :[/bold cyan]  ₹{t2}  ([cyan]+{lv['t2_pct']}%[/cyan])  "
        f"← Next resistance — book more here\n"
        f"  [bold cyan]TARGET 3   :[/bold cyan]  ₹{t3}  ([cyan]+{lv['t3_pct']}%[/cyan])  "
        f"← 52W high breakout — hold rest for this\n"
        f"\n"
        f"  [bold white]Risk:Reward:[/bold white]  1:{lv['rr']}  "
        f"{'[green]✓ Good trade setup[/green]' if lv['rr']>=2 else '[yellow]⚠ Marginal setup[/yellow]'}\n"
        f"\n"
        f"  [bold white]52W Range:[/bold white]     {rng}% from bottom → {entry_hint}\n"
        f"  [bold white]Trend:[/bold white]         {trend_txt}\n"
        f"\n"
        f"  [dim]Key supports   : {lv['all_supports']}[/dim]\n"
        f"  [dim]Key resistances: {lv['all_resistances']}[/dim]\n"
        f"\n"
        f"  [dim]Position sizing: ₹10,000 → {lv['shares_10k']} shares, "
        f"max loss if SL hits = ₹{lv['max_loss']}[/dim]"
    )

    console.print(Panel(ladder + detail,
                        title=f"[bold magenta]📈 {name} — Price Levels (ATR-based)[/bold magenta]",
                        border_style="magenta"))


# ─────────────────────────────────────────────────────────────
# 7. ALERTS ONLY
# ─────────────────────────────────────────────────────────────
def show_alerts(results):
    console.print(Rule("[bold]🔔 Signal Alerts[/bold]"))
    valid = [r for r in results if not r.get("error")]
    buys  = sorted([r for r in valid if r["score"]>=T["score_buy"]],
                   key=lambda x: x["score"], reverse=True)
    watch = sorted([r for r in valid if T["score_watch"]<=r["score"]<T["score_buy"]],
                   key=lambda x: x["score"], reverse=True)
    avoid = sorted([r for r in valid if r["score"]<T["score_watch"]],
                   key=lambda x: x["score"])

    if buys:
        console.print("\n[bold green]🟢 BUY CANDIDATES[/bold green]")
        for r in buys:
            console.print(f"  [green]▶ {r['name']:14s}[/green]  "
                          f"Score:[bold]{r['score']}[/bold]  "
                          f"P/E:{r.get('pe','?')}  ROE:{r.get('roe','?')}%  "
                          f"D/E:{r.get('de','?')}  RevGr:{r.get('rev_gr','?')}%")
    if watch:
        console.print("\n[bold yellow]🟡 WATCHLIST[/bold yellow]")
        for r in watch:
            console.print(f"  [yellow]▶ {r['name']:14s}[/yellow]  "
                          f"Score:[bold]{r['score']}[/bold]  "
                          f"P/E:{r.get('pe','?')}  ROE:{r.get('roe','?')}%")
    if avoid:
        console.print("\n[bold red]🔴 AVOID[/bold red]")
        for r in avoid:
            console.print(f"  [red]▶ {r['name']:14s}[/red]  Score:[bold]{r['score']}[/bold]")
    console.print()


# ─────────────────────────────────────────────────────────────
# 8. CSV EXPORT
# ─────────────────────────────────────────────────────────────
def export_csv(results):
    fn = f"nifty_scan_{datetime.now():%Y%m%d_%H%M}.csv"
    fields = ["name","ticker","sector","price","score","signal",
              "pe","pb","roe","net_margin","gross_margin","de","cur_ratio",
              "rev_gr","earn_gr","fcf_cr","div_yld","insider","inst",
              "ann_ret","w52h","w52l","market_cap_cr"]
    with open(fn,"w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in results:
            row = dict(r)
            row["signal"] = sig(r.get("score",0))[0] if not r.get("error") else "ERROR"
            w.writerow(row)
    console.print(f"\n[green]✓ Exported →[/green] [bold]{fn}[/bold]")


# ─────────────────────────────────────────────────────────────
# 9. SCAN RUNNER
# ─────────────────────────────────────────────────────────────
def run_scan(tickers=None):
    if tickers is None: tickers = NIFTY50
    results = []
    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console) as prog:
        task = prog.add_task("Starting...", total=len(tickers))
        for name, symbol in tickers.items():
            prog.update(task, description=f"[cyan]Fetching[/cyan] {name}")
            d = fetch_fundamentals(symbol, name)
            if not d.get("error"):
                sc, g, r = score_stock(d)
                d["score"]=sc; d["green_flags"]=g; d["red_flags"]=r
            else:
                d["score"] = 0
            results.append(d)
            prog.advance(task)
            time.sleep(0.3)
    return results


# ─────────────────────────────────────────────────────────────
# 10. WATCH MODE
# ─────────────────────────────────────────────────────────────
def watch_mode(interval):
    console.print(Panel(f"[cyan]Watch mode — every {interval} min. Ctrl+C to stop.[/cyan]",
                        border_style="cyan"))
    while True:
        os.system("clear")
        results = run_scan()
        show_fundamentals(results)
        show_alerts(results)
        nxt = datetime.now() + timedelta(minutes=interval)
        console.print(f"\n[dim]Next refresh at {nxt:%H:%M:%S}[/dim]")
        time.sleep(interval * 60)


# ─────────────────────────────────────────────────────────────
# 11. MAIN
# ─────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description="NIFTY 50 Monitor v2 — Fundamental + Price Levels + News Sentiment",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--watch",    action="store_true",  help="Auto-refresh mode")
    ap.add_argument("--interval", type=int, default=30, help="Minutes between refreshes")
    ap.add_argument("--stock",    type=str,             help="Deep dive: e.g. RELIANCE")
    ap.add_argument("--alerts",   action="store_true",  help="Only buy/watch/avoid signals")
    ap.add_argument("--levels",   action="store_true",  help="Show price levels for all stocks")
    ap.add_argument("--export",   action="store_true",  help="Export to CSV")
    ap.add_argument("--top",      type=int,             help="Only top N stocks by score")
    ap.add_argument("--news",     action="store_true",  help="Add news sentiment analysis (needs ANTHROPIC_API_KEY)")
    ap.add_argument("--sector",   type=str,             help="News sentiment for one sector e.g. IT BANKING")
    args = ap.parse_args()

    console.print(Panel(
        "[bold cyan]NIFTY 50 STOCK RESEARCH MONITOR  v2.0[/bold cyan]\n"
        "[dim]Fundamental + ATR Price Levels + AI News Sentiment | Yahoo Finance[/dim]",
        border_style="bright_blue", expand=False))

    # ── News sentiment: sector only ──────────────────────────
    if args.sector and not args.stock:
        try:
            from news_sentiment import get_sector_sentiment, display_sentiment_panel, fetch_rss_headlines
            sec = args.sector.upper()
            console.print(f"\n[bold cyan]📰 Fetching news for {sec} sector...[/bold cyan]\n")
            result = get_sector_sentiment(sec)
            display_sentiment_panel(result, f"📰 {sec} Sector — News Sentiment")
        except ImportError:
            console.print("[red]news_sentiment.py not found in same folder.[/red]")
        return

    # ── Single stock deep dive ───────────────────────────────
    if args.stock:
        name = args.stock.upper()
        sym  = NIFTY50.get(name, name if name.endswith(".NS") else name+".NS")
        show_deep_dive(name, sym)

        # News sentiment for this stock
        if args.news:
            try:
                from news_sentiment import (get_stock_sentiment, get_macro_sentiment,
                                            display_sentiment_panel, _get_api_key)
                if not _get_api_key():
                    console.print(Panel(
                        "[red]ANTHROPIC_API_KEY not set.[/red]\n"
                        "Run: [bold]export ANTHROPIC_API_KEY=sk-ant-...[/bold]\n"
                        "Or:  [bold]mkdir -p ~/.config/stock_monitor && echo 'sk-ant-...' > ~/.config/stock_monitor/api_key[/bold]",
                        border_style="red"))
                else:
                    console.print(f"\n[bold cyan]📰 Fetching news sentiment for {name}...[/bold cyan]\n")
                    result = get_stock_sentiment(name, sym)
                    display_sentiment_panel(result, f"📰 {name} — News Sentiment (AI)")
                    console.print("\n[bold cyan]📰 Fetching macro sentiment...[/bold cyan]\n")
                    macro = get_macro_sentiment()
                    display_sentiment_panel(macro, "📰 Macro — Global & India Market")
            except ImportError:
                console.print("[red]news_sentiment.py not found in same folder.[/red]")
        return

    if args.watch:
        watch_mode(args.interval); return

    console.print("\n[bold cyan]Running NIFTY 50 scan...[/bold cyan]\n")
    results = run_scan()

    if not args.alerts:
        pool = sorted([r for r in results if not r.get("error")],
                      key=lambda x: x.get("score",0), reverse=True)
        show_fundamentals(pool[:args.top] if args.top else results)

    show_alerts(results)

    if args.levels:
        console.print("\n[bold magenta]Fetching price levels...[/bold magenta]\n")
        show_levels_table(results)

    # ── Full news scan (macro + all sectors) ─────────────────
    if args.news:
        try:
            from news_sentiment import (run_full_news_scan, display_sentiment_panel,
                                        display_news_summary_table, _get_api_key)
            if not _get_api_key():
                console.print(Panel(
                    "[red]ANTHROPIC_API_KEY not set.[/red]\n"
                    "Run: [bold]export ANTHROPIC_API_KEY=sk-ant-...[/bold]",
                    border_style="red"))
            else:
                console.print("\n[bold cyan]📰 Running full news sentiment scan...[/bold cyan]\n")
                news_results = run_full_news_scan()
                display_sentiment_panel(news_results["macro"], "📰 Macro — Global & India Market")
                display_news_summary_table(news_results["sectors"])
        except ImportError:
            console.print("[red]news_sentiment.py not found in same folder.[/red]")

    if args.export:
        export_csv(results)

    valid = [r for r in results if not r.get("error")]
    console.print(Panel(
        f"[green]🟢 Buy Candidates: {sum(1 for r in valid if r['score']>=T['score_buy'])}[/green]   "
        f"[yellow]🟡 Watchlist: {sum(1 for r in valid if T['score_watch']<=r['score']<T['score_buy'])}[/yellow]   "
        f"[red]🔴 Avoid: {sum(1 for r in valid if r['score']<T['score_watch'])}[/red]   "
        f"[dim]Errors: {len(results)-len(valid)}[/dim]",
        title="Scan Summary", border_style="bright_blue"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")
