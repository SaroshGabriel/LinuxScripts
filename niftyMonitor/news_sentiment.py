#!/usr/bin/env python3
"""
news_sentiment.py
─────────────────
Fetches latest financial news from free RSS feeds and uses
Claude API to analyse sentiment + market impact for:
  - Macro / global events  (war, Fed, oil, tariffs)
  - Sector-level impact    (IT, pharma, banking, auto...)
  - Individual stock news  (company-specific headlines)

Called by stock_monitor.py — can also be run standalone:
    python news_sentiment.py                    → macro + all sectors
    python news_sentiment.py --stock TATACHEM   → stock-specific
    python news_sentiment.py --sector IT        → sector deep dive
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time
import re
import sys
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich import box

console = Console()

# ─────────────────────────────────────────────────────────────
# SECTOR MAP  — which sectors do which stocks belong to
# ─────────────────────────────────────────────────────────────
SECTOR_MAP = {
    "IT":        ["TCS", "INFOSYS", "WIPRO", "HCLTECH", "TECHM"],
    "BANKING":   ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK",
                  "INDUSINDBK", "BAJFINANCE", "BAJAJFINSV", "HDFCLIFE",
                  "SBILIFE", "SHRIRAMFIN"],
    "OIL&GAS":   ["RELIANCE", "ONGC", "BPCL"],
    "AUTO":      ["MARUTI", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT",
                  "TATAMOTORS", "M&M"],
    "PHARMA":    ["SUNPHARMA", "DIVISLAB", "CIPLA", "DRREDDY", "APOLLOHOSP"],
    "FMCG":      ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM"],
    "METALS":    ["TATASTEEL", "JSWSTEEL", "HINDALCO", "COALINDIA"],
    "CEMENT":    ["ULTRACEMCO", "GRASIM"],
    "INFRA":     ["LT", "ADANIPORTS", "ADANIENT", "POWERGRID", "NTPC"],
    "CONSUMER":  ["ASIANPAINT", "TITAN", "TRENT", "BRITANNIA"],
    "CHEMICALS": ["TATACHEM"],
}

# Reverse map: stock → sector
STOCK_SECTOR = {}
for sector, stocks in SECTOR_MAP.items():
    for s in stocks:
        STOCK_SECTOR[s] = sector

# ─────────────────────────────────────────────────────────────
# MACRO KEYWORDS that affect Indian markets broadly
# ─────────────────────────────────────────────────────────────
MACRO_KEYWORDS = [
    "india stock market", "nifty", "sensex", "RBI", "repo rate",
    "rupee dollar", "FII", "FDI", "inflation india", "budget india",
    "crude oil price", "US Fed rate", "trump tariff india",
    "geopolitical", "iran war", "russia ukraine", "china india trade",
    "global recession", "US economy",
]

SECTOR_KEYWORDS = {
    "IT":        ["IT sector india", "tech layoffs", "dollar rupee", "US recession IT",
                  "infosys TCS results", "software exports india"],
    "BANKING":   ["RBI policy", "interest rate india", "NPA banks india",
                  "credit growth india", "banking sector india"],
    "OIL&GAS":   ["crude oil price", "OPEC", "petrol diesel price india",
                  "iran oil", "oil sanctions"],
    "AUTO":      ["auto sales india", "EV india", "petrol price",
                  "auto sector india", "passenger vehicle sales"],
    "PHARMA":    ["pharma india", "US FDA", "drug approval india",
                  "healthcare india", "generic drugs"],
    "FMCG":      ["FMCG india", "rural consumption india", "inflation FMCG",
                  "consumer spending india"],
    "METALS":    ["steel price india", "iron ore", "aluminium price",
                  "china steel", "metal sector india"],
    "CEMENT":    ["cement price india", "infrastructure spending",
                  "housing india", "construction sector"],
    "INFRA":     ["infrastructure india", "government capex",
                  "power sector india", "port india"],
    "CHEMICALS": ["chemical sector india", "specialty chemicals",
                  "China+1 chemicals", "agrochemicals india"],
}


# ─────────────────────────────────────────────────────────────
# RSS FEED FETCHER
# ─────────────────────────────────────────────────────────────
FREE_RSS_FEEDS = [
    # Google News (works without API key)
    "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en",
    # Yahoo Finance news
    "https://finance.yahoo.com/rss/headline?s={symbol}",
]

def fetch_rss_headlines(query: str, max_items: int = 8) -> list[str]:
    """Fetch headlines from Google News RSS for a query."""
    headlines = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"

        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; StockMonitor/2.0)"
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            xml_data = resp.read()

        root = ET.fromstring(xml_data)
        items = root.findall(".//item")

        for item in items[:max_items]:
            title = item.findtext("title", "").strip()
            pub   = item.findtext("pubDate", "").strip()
            if title:
                # Clean Google News title format "Headline - Source"
                title = re.sub(r'\s*-\s*[^-]+$', '', title).strip()
                headlines.append(f"{title} [{pub[:16]}]")

    except Exception as e:
        headlines.append(f"[RSS fetch failed: {str(e)[:60]}]")

    return headlines


def fetch_yahoo_stock_news(symbol_ns: str, max_items: int = 5) -> list[str]:
    """Fetch stock-specific news from Yahoo Finance RSS."""
    headlines = []
    try:
        # Remove .NS/.BO for Yahoo Finance news URL
        sym = symbol_ns.replace(".NS","").replace(".BO","")
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={sym}.NS&region=IN&lang=en-IN"

        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; StockMonitor/2.0)"
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            xml_data = resp.read()

        root = ET.fromstring(xml_data)
        for item in root.findall(".//item")[:max_items]:
            title = item.findtext("title","").strip()
            if title:
                headlines.append(title)

    except Exception:
        pass  # Fall back to Google News

    return headlines


# ─────────────────────────────────────────────────────────────
# CLAUDE API SENTIMENT ANALYSER
# ─────────────────────────────────────────────────────────────
def analyse_with_claude(headlines: list[str], context: str,
                        stock_name: str = None,
                        sector: str = None) -> dict:
    """
    Send headlines to Claude API for sentiment + impact analysis.
    Returns structured dict with sentiment, impact, reasoning, action.
    """
    if not headlines or all("fetch failed" in h for h in headlines):
        return {"error": "No headlines to analyse"}

    headlines_text = "\n".join(f"• {h}" for h in headlines)

    if stock_name:
        subject = f"the Indian stock {stock_name}"
        focus   = f"How do these headlines specifically affect {stock_name} stock? Consider its business model and sector ({sector or 'unknown'})."
    elif sector:
        subject = f"the Indian {sector} sector stocks"
        focus   = f"How do these headlines affect {sector} sector stocks on NSE/BSE?"
    else:
        subject = "the Indian stock market (Nifty 50, Sensex)"
        focus   = "How do these macro/global headlines affect the overall Indian stock market?"

    prompt = f"""You are a senior Indian equity research analyst. Analyse these recent news headlines and their impact on {subject}.

HEADLINES:
{headlines_text}

CONTEXT: {context}

{focus}

Respond ONLY in this exact JSON format, no markdown, no extra text:
{{
  "sentiment": "BULLISH" | "BEARISH" | "NEUTRAL" | "MIXED",
  "impact_score": <integer -10 to +10, where -10=very negative, 0=neutral, +10=very positive>,
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "key_risks": ["risk1", "risk2", "risk3"],
  "key_tailwinds": ["tailwind1", "tailwind2"],
  "short_term_outlook": "<1-2 sentence outlook for next 1-4 weeks>",
  "long_term_outlook": "<1-2 sentence outlook for next 3-12 months>",
  "action_hint": "BUY_DIP" | "HOLD" | "REDUCE" | "AVOID" | "WATCH",
  "top_headline_impact": "<the single most impactful headline and why in 1 sentence>"
}}"""

    try:
        import urllib.request
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 600,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type":      "application/json",
                "anthropic-version": "2023-06-01",
                # API key loaded from env var ANTHROPIC_API_KEY
            },
            method="POST"
        )

        # Load API key from environment or config file
        api_key = _get_api_key()
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY not set. Run: export ANTHROPIC_API_KEY=your_key"}

        req.add_header("x-api-key", api_key)

        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())

        raw = data["content"][0]["text"].strip()
        # Strip markdown fences if present
        raw = re.sub(r'^```json\s*|\s*```$', '', raw, flags=re.MULTILINE).strip()
        return json.loads(raw)

    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}"}
    except Exception as e:
        return {"error": str(e)[:120]}


def _get_api_key() -> str:
    """Load Anthropic API key from env var or ~/.config/stock_monitor/api_key."""
    import os
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return key
    # Fallback: config file
    config_path = os.path.expanduser("~/.config/stock_monitor/api_key")
    if os.path.exists(config_path):
        with open(config_path) as f:
            return f.read().strip()
    return ""


# ─────────────────────────────────────────────────────────────
# DISPLAY HELPERS
# ─────────────────────────────────────────────────────────────
def sentiment_color(sentiment: str) -> str:
    return {"BULLISH":"green","BEARISH":"red","NEUTRAL":"yellow","MIXED":"cyan"}.get(sentiment,"white")

def action_color(action: str) -> str:
    return {"BUY_DIP":"green","HOLD":"yellow","REDUCE":"orange3",
            "AVOID":"red","WATCH":"cyan"}.get(action,"white")

def impact_bar(score: int) -> str:
    """Visual bar: -10 to +10"""
    score   = max(-10, min(10, score))
    mid     = 10
    bar     = ["─"] * 21
    bar[mid] = "┼"
    pos     = mid + score
    bar[pos] = "█"
    col     = "green" if score > 0 else "red" if score < 0 else "yellow"
    return f"[{col}]{''.join(bar)}[/{col}]  [{col}]{score:+d}[/{col}]"


def display_sentiment_panel(result: dict, title: str):
    """Render one sentiment analysis panel."""
    if result.get("error"):
        console.print(Panel(f"[red]Analysis unavailable: {result['error']}[/red]",
                            title=title, border_style="red"))
        return

    sent  = result.get("sentiment","?")
    score = result.get("impact_score", 0)
    conf  = result.get("confidence","?")
    action= result.get("action_hint","?")
    sc    = sentiment_color(sent)
    ac    = action_color(action)

    risks     = result.get("key_risks",[])
    tailwinds = result.get("key_tailwinds",[])

    content = (
        f"  [bold]Sentiment:[/bold]   [{sc}]{sent}[/{sc}]   "
        f"[bold]Confidence:[/bold] {conf}   "
        f"[bold]Action:[/bold] [{ac}]{action}[/{ac}]\n"
        f"  [bold]Impact Score:[/bold] {impact_bar(score)}\n"
        f"\n"
        f"  [bold]Key Headline:[/bold]\n"
        f"  [italic]{result.get('top_headline_impact','N/A')}[/italic]\n"
        f"\n"
    )

    if risks:
        content += "  [bold red]⚠ Risks:[/bold red]\n"
        for r in risks:
            content += f"    [red]• {r}[/red]\n"

    if tailwinds:
        content += "\n  [bold green]✓ Tailwinds:[/bold green]\n"
        for t in tailwinds:
            content += f"    [green]• {t}[/green]\n"

    content += (
        f"\n  [bold]Short-term (1–4 wks):[/bold] {result.get('short_term_outlook','N/A')}\n"
        f"  [bold]Long-term  (3–12 mo):[/bold] {result.get('long_term_outlook','N/A')}\n"
    )

    console.print(Panel(content, title=title, border_style=sc))


def display_news_summary_table(sector_results: dict):
    """Compact table showing sentiment for all sectors at once."""
    tbl = Table(
        title=f"📰 News Sentiment — All Sectors  {datetime.now():%d %b %Y %H:%M}",
        box=box.ROUNDED, show_lines=True,
        header_style="bold cyan", title_style="bold white on dark_blue",
    )
    tbl.add_column("Sector",        style="bold white", width=12)
    tbl.add_column("Sentiment",     justify="center",   width=10)
    tbl.add_column("Impact",        justify="center",   width=25)
    tbl.add_column("Confidence",    justify="center",   width=10)
    tbl.add_column("Action",        justify="center",   width=12)
    tbl.add_column("Key Risk",                          width=35)

    for sector, res in sector_results.items():
        if res.get("error"):
            tbl.add_row(sector,"—","—","—","—",f"[red]{res['error'][:35]}[/red]")
            continue
        sent  = res.get("sentiment","?")
        score = res.get("impact_score",0)
        conf  = res.get("confidence","?")
        action= res.get("action_hint","?")
        sc    = sentiment_color(sent)
        ac    = action_color(action)
        risk  = res.get("key_risks",["N/A"])[0] if res.get("key_risks") else "N/A"
        tbl.add_row(
            sector,
            f"[{sc}]{sent}[/{sc}]",
            impact_bar(score),
            conf,
            f"[{ac}]{action}[/{ac}]",
            risk[:35],
        )
    console.print(tbl)


# ─────────────────────────────────────────────────────────────
# HIGH-LEVEL API  (called by stock_monitor.py)
# ─────────────────────────────────────────────────────────────
def get_macro_sentiment() -> dict:
    """Fetch + analyse macro/global news affecting Indian markets."""
    console.print("[dim]Fetching macro news...[/dim]")
    headlines = []
    for q in ["india stock market nifty", "global economy india impact",
               "crude oil rupee dollar", "US Fed RBI interest rate"]:
        headlines += fetch_rss_headlines(q, max_items=4)
        time.sleep(0.3)

    headlines = list(dict.fromkeys(headlines))[:15]  # dedupe, cap at 15

    return analyse_with_claude(
        headlines,
        context="Indian equity market context. Focus on Nifty 50 and macro factors.",
    )


def get_sector_sentiment(sector: str) -> dict:
    """Fetch + analyse news for a specific sector."""
    keywords = SECTOR_KEYWORDS.get(sector, [sector + " india stock"])
    headlines = []
    for kw in keywords[:3]:
        headlines += fetch_rss_headlines(kw, max_items=4)
        time.sleep(0.3)
    headlines = list(dict.fromkeys(headlines))[:12]

    return analyse_with_claude(
        headlines,
        context=f"Indian {sector} sector stocks on NSE/BSE.",
        sector=sector,
    )


def get_stock_sentiment(stock_name: str, ticker_symbol: str) -> dict:
    """Fetch + analyse news for a specific stock."""
    sector = STOCK_SECTOR.get(stock_name, "")
    headlines = []

    # Stock-specific Yahoo Finance news
    headlines += fetch_yahoo_stock_news(ticker_symbol, max_items=5)
    time.sleep(0.3)

    # Google News for the company
    headlines += fetch_rss_headlines(f"{stock_name} stock india", max_items=5)
    time.sleep(0.3)

    # Sector news for context
    if sector:
        headlines += fetch_rss_headlines(
            SECTOR_KEYWORDS.get(sector, [sector])[0], max_items=3)

    headlines = list(dict.fromkeys(headlines))[:14]

    return analyse_with_claude(
        headlines,
        context=f"Indian stock {stock_name} ({ticker_symbol}), sector: {sector}.",
        stock_name=stock_name,
        sector=sector,
    )


def run_full_news_scan() -> dict:
    """
    Run macro + all sector sentiment scans.
    Returns dict: { 'macro': {...}, 'sectors': { 'IT': {...}, ... } }
    """
    results = {}

    console.print("\n[bold cyan]📰 Fetching macro news...[/bold cyan]")
    results["macro"] = get_macro_sentiment()

    console.print("[bold cyan]📰 Fetching sector news...[/bold cyan]")
    sector_results = {}
    for sector in SECTOR_MAP:
        console.print(f"  [dim]→ {sector}[/dim]", end="\r")
        sector_results[sector] = get_sector_sentiment(sector)
        time.sleep(0.5)
    results["sectors"] = sector_results

    return results


# ─────────────────────────────────────────────────────────────
# STANDALONE USAGE
# ─────────────────────────────────────────────────────────────
def main():
    import argparse
    ap = argparse.ArgumentParser(description="News Sentiment Analyser")
    ap.add_argument("--stock",  type=str, help="Stock name e.g. TATACHEM")
    ap.add_argument("--sector", type=str, help="Sector e.g. IT BANKING OIL&GAS")
    ap.add_argument("--macro",  action="store_true", help="Macro analysis only")
    ap.add_argument("--all",    action="store_true", help="Full scan — macro + all sectors")
    args = ap.parse_args()

    console.print(Panel(
        "[bold cyan]📰 News Sentiment Analyser[/bold cyan]\n"
        "[dim]Powered by Google News RSS + Claude AI[/dim]",
        border_style="cyan", expand=False))

    if not _get_api_key():
        console.print(Panel(
            "[red]ANTHROPIC_API_KEY not set![/red]\n\n"
            "Set it with:\n"
            "  [bold]export ANTHROPIC_API_KEY=sk-ant-...[/bold]\n\n"
            "Or save permanently:\n"
            "  [bold]mkdir -p ~/.config/stock_monitor[/bold]\n"
            "  [bold]echo 'sk-ant-...' > ~/.config/stock_monitor/api_key[/bold]",
            border_style="red"))
        sys.exit(1)

    if args.stock:
        from stock_monitor import NIFTY50
        name   = args.stock.upper()
        symbol = NIFTY50.get(name, name+".NS")
        console.print(f"\n[bold]Analysing {name}...[/bold]\n")
        headlines = []
        headlines += fetch_yahoo_stock_news(symbol, 5)
        headlines += fetch_rss_headlines(f"{name} stock india", 6)
        for h in headlines: console.print(f"  [dim]• {h}[/dim]")
        result = get_stock_sentiment(name, symbol)
        display_sentiment_panel(result, f"📰 {name} — News Sentiment")

    elif args.sector:
        sec = args.sector.upper()
        console.print(f"\n[bold]Analysing {sec} sector...[/bold]\n")
        result = get_sector_sentiment(sec)
        display_sentiment_panel(result, f"📰 {sec} Sector — News Sentiment")

    elif args.macro or not args.all:
        console.print("\n[bold]Macro analysis...[/bold]\n")
        result = get_macro_sentiment()
        display_sentiment_panel(result, "📰 Macro — Global & India Market Sentiment")

    if args.all:
        results = run_full_news_scan()
        display_sentiment_panel(results["macro"], "📰 Macro Sentiment")
        display_news_summary_table(results["sectors"])
        for sector, res in results["sectors"].items():
            display_sentiment_panel(res, f"📰 {sector} Sector")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")
