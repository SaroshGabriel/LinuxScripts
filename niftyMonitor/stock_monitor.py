#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║        MARKET RESEARCH MONITOR  v3.0                         ║
║        Stocks · Crypto · Metals · Forex                      ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    ./run.sh                        → NIFTY 50 fundamental scan
    ./run.sh --sectorscan           → 10 stocks × 10 sectors (100 stocks)
    ./run.sh --stock RELIANCE       → Single stock deep dive
    ./run.sh --crypto               → BTC, ETH, SHIB + top crypto
    ./run.sh --metals               → Gold & Silver (INR + USD)
    ./run.sh --forex                → Top 10 currencies vs USD
    ./run.sh --all                  → Everything in one go
    ./run.sh --levels               → Price levels for NIFTY 50
    ./run.sh --alerts               → Buy/Watch/Avoid signals only
    ./run.sh --export               → Save all results to CSV
    ./run.sh --watch                → Auto-refresh every 30 min
    ./run.sh --top 10               → Top 10 stocks by score
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
# NIFTY 50
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
    "ADANIENT":   "ADANIENT.NS",  "TATASTEEL":  "TATASTEEL.NS",
    "BAJAJFINSV": "BAJAJFINSV.NS","JSWSTEEL":   "JSWSTEEL.NS",
    "TECHM":      "TECHM.NS",     "COALINDIA":  "COALINDIA.NS",
    "GRASIM":     "GRASIM.NS",    "DIVISLAB":   "DIVISLAB.NS",
    "CIPLA":      "CIPLA.NS",     "DRREDDY":    "DRREDDY.NS",
    "EICHERMOT":  "EICHERMOT.NS", "HINDALCO":   "HINDALCO.NS",
    "INDUSINDBK": "INDUSINDBK.NS","M&M":        "M&M.NS",
    "ADANIPORTS": "ADANIPORTS.NS","BRITANNIA":  "BRITANNIA.NS",
    "HDFCLIFE":   "HDFCLIFE.NS",  "SBILIFE":    "SBILIFE.NS",
    "TATACONSUM": "TATACONSUM.NS","APOLLOHOSP": "APOLLOHOSP.NS",
    "BAJAJ-AUTO": "BAJAJ-AUTO.NS","BPCL":       "BPCL.NS",
    "HEROMOTOCO": "HEROMOTOCO.NS","SHRIRAMFIN": "SHRIRAMFIN.NS",
    "TRENT":      "TRENT.NS",     "TATACHEM":   "TATACHEM.BO",
}

# ─────────────────────────────────────────────────────────────
# SECTOR SCAN — 10 stocks × 10 sectors
# ─────────────────────────────────────────────────────────────
SECTORS = {
    "IT": {
        "TCS":          "TCS.NS",
        "INFOSYS":      "INFY.NS",
        "HCLTECH":      "HCLTECH.NS",
        "WIPRO":        "WIPRO.NS",
        "TECHM":        "TECHM.NS",
        "LTIM":         "LTIM.NS",
        "MPHASIS":      "MPHASIS.NS",
        "PERSISTENT":   "PERSISTENT.NS",
        "COFORGE":      "COFORGE.NS",
        "OFSS":         "OFSS.NS",
    },
    "BANKING": {
        "HDFCBANK":     "HDFCBANK.NS",
        "ICICIBANK":    "ICICIBANK.NS",
        "SBIN":         "SBIN.NS",
        "KOTAKBANK":    "KOTAKBANK.NS",
        "AXISBANK":     "AXISBANK.NS",
        "INDUSINDBK":   "INDUSINDBK.NS",
        "BANDHANBNK":   "BANDHANBNK.NS",
        "FEDERALBNK":   "FEDERALBNK.NS",
        "IDFCFIRSTB":   "IDFCFIRSTB.NS",
        "RBLBANK":      "RBLBANK.NS",
    },
    "PHARMA": {
        "SUNPHARMA":    "SUNPHARMA.NS",
        "DIVISLAB":     "DIVISLAB.NS",
        "CIPLA":        "CIPLA.NS",
        "DRREDDY":      "DRREDDY.NS",
        "APOLLOHOSP":   "APOLLOHOSP.NS",
        "LUPIN":        "LUPIN.NS",
        "AUROPHARMA":   "AUROPHARMA.NS",
        "TORNTPHARM":   "TORNTPHARM.NS",
        "ALKEM":        "ALKEM.NS",
        "IPCA":         "IPCALAB.NS",
    },
    "AUTO": {
        "MARUTI":       "MARUTI.NS",
        "BAJAJ-AUTO":   "BAJAJ-AUTO.NS",
        "HEROMOTOCO":   "HEROMOTOCO.NS",
        "EICHERMOT":    "EICHERMOT.NS",
        "M&M":          "M&M.NS",
        "TVSMOTOR":     "TVSMOTOR.NS",
        "ASHOKLEY":     "ASHOKLEY.NS",
        "MOTHERSON":    "MOTHERSON.NS",
        "BOSCHLTD":     "BOSCHLTD.NS",
        "BALKRISIND":   "BALKRISIND.NS",
    },
    "FMCG": {
        "HINDUNILVR":   "HINDUNILVR.NS",
        "ITC":          "ITC.NS",
        "NESTLEIND":    "NESTLEIND.NS",
        "BRITANNIA":    "BRITANNIA.NS",
        "TATACONSUM":   "TATACONSUM.NS",
        "DABUR":        "DABUR.NS",
        "MARICO":       "MARICO.NS",
        "GODREJCP":     "GODREJCP.NS",
        "EMAMILTD":     "EMAMILTD.NS",
        "COLPAL":       "COLPAL.NS",
    },
    "METALS": {
        "TATASTEEL":    "TATASTEEL.NS",
        "JSWSTEEL":     "JSWSTEEL.NS",
        "HINDALCO":     "HINDALCO.NS",
        "COALINDIA":    "COALINDIA.NS",
        "NMDC":         "NMDC.NS",
        "SAIL":         "SAIL.NS",
        "VEDL":         "VEDL.NS",
        "NATIONALUM":   "NATIONALUM.NS",
        "JINDALSTEL":   "JINDALSTEL.NS",
        "APLAPOLLO":    "APLAPOLLO.NS",
    },
    "INFRA": {
        "LT":           "LT.NS",
        "ADANIPORTS":   "ADANIPORTS.NS",
        "POWERGRID":    "POWERGRID.NS",
        "NTPC":         "NTPC.NS",
        "ADANIENT":     "ADANIENT.NS",
        "IRFC":         "IRFC.NS",
        "RVNL":         "RVNL.NS",
        "PFC":          "PFC.NS",
        "RECLTD":       "RECLTD.NS",
        "CUMMINSIND":   "CUMMINSIND.NS",
    },
    "OIL&GAS": {
        "RELIANCE":     "RELIANCE.NS",
        "ONGC":         "ONGC.NS",
        "BPCL":         "BPCL.NS",
        "IOC":          "IOC.NS",
        "GAIL":         "GAIL.NS",
        "OIL":          "OIL.NS",
        "MGL":          "MGL.NS",
        "IGL":          "IGL.NS",
        "PETRONET":     "PETRONET.NS",
        "HINDPETRO":    "HINDPETRO.NS",
    },
    "CHEMICALS": {
        "TATACHEM":     "TATACHEM.BO",
        "PIDILITIND":   "PIDILITIND.NS",
        "SRF":          "SRF.NS",
        "DEEPAKNTR":    "DEEPAKNTR.NS",
        "AARTIIND":     "AARTIIND.NS",
        "NAVINFLUOR":   "NAVINFLUOR.NS",
        "ALKYLAMINE":   "ALKYLAMINE.NS",
        "GALAXYSURF":   "GALAXYSURF.NS",
        "FINEORG":      "FINEORG.NS",
        "VINATIORGA":   "VINATIORGA.NS",
    },
    "CONSUMER": {
        "ASIANPAINT":   "ASIANPAINT.NS",
        "TITAN":        "TITAN.NS",
        "TRENT":        "TRENT.NS",
        "BAJFINANCE":   "BAJFINANCE.NS",
        "HAVELLS":      "HAVELLS.NS",
        "VOLTAS":       "VOLTAS.NS",
        "WHIRLPOOL":    "WHIRLPOOL.NS",
        "VGUARD":       "VGUARD.NS",
        "CROMPTON":     "CROMPTON.NS",
        "DIXON":        "DIXON.NS",
    },
    "DEFENCE": {
        "HAL":          "HAL.NS",
        "BEL":          "BEL.NS",
        "BHEL":         "BHEL.NS",
        "COCHINSHIP":   "COCHINSHIP.NS",
        "GRSE":         "GRSE.NS",
        "MIDHANI":      "MIDHANI.NS",
        "MAZDOCK":      "MAZDOCK.NS",
        "DATAPATTNS":   "DATAPATTNS.NS",
        "BEML":         "BEML.NS",
        "PARAS":        "PARAS.NS",
    },
    "REALTY": {
        "DLF":          "DLF.NS",
        "GODREJPROP":   "GODREJPROP.NS",
        "OBEROIRLTY":   "OBEROIRLTY.NS",
        "PRESTIGE":     "PRESTIGE.NS",
        "PHOENIXLTD":   "PHOENIXLTD.NS",
        "SOBHA":        "SOBHA.NS",
        "BRIGADE":      "BRIGADE.NS",
        "MAHLIFE":      "MAHLIFE.NS",
        "SUNTECK":      "SUNTECK.NS",
        "KOLTEPATIL":   "KOLTEPATIL.NS",
    },
    "TELECOM": {
        "BHARTIARTL":   "BHARTIARTL.NS",
        "IDEA":         "IDEA.NS",
        "INDUSTOWER":   "INDUSTOWER.NS",
        "TATACOMM":     "TATACOMM.NS",
        "RAILTEL":      "RAILTEL.NS",
        "HFCL":         "HFCL.NS",
        "STLTECH":      "STLTECH.NS",
        "TEJASNET":     "TEJASNET.NS",
        "GTLINFRA":     "GTLINFRA.NS",
        "VINDHYATEL":   "VINDHYATEL.NS",
    },
    "HEALTHCARE": {
        "APOLLOHOSP":   "APOLLOHOSP.NS",
        "MAXHEALTH":    "MAXHEALTH.NS",
        "FORTIS":       "FORTIS.NS",
        "NH":           "NH.NS",
        "METROPOLIS":   "METROPOLIS.NS",
        "LALPATHLAB":   "LALPATHLAB.NS",
        "MEDANTA":      "MEDANTA.NS",
        "KIMS":         "KIMS.NS",
        "THYROCARE":    "THYROCARE.NS",
        "KRSNAA":       "KRSNAA.NS",
    },
    "INSURANCE": {
        "HDFCLIFE":     "HDFCLIFE.NS",
        "SBILIFE":      "SBILIFE.NS",
        "ICICIPRULI":   "ICICIPRULI.NS",
        "ICICIGI":      "ICICIGI.NS",
        "NIACL":        "NIACL.NS",
        "STARHEALTH":   "STARHEALTH.NS",
        "GICRE":        "GICRE.NS",
        "LICI":         "LICI.NS",
        "BAJAJFINSV":   "BAJAJFINSV.NS",
        "GODIGIT":      "GODIGIT.NS",
    },
    "AIRLINES": {
        "INDIGO":       "INDIGO.NS",
        "SPICEJET":     "SPICEJET.NS",
        "GMRINFRA":     "GMRINFRA.NS",
        "BLUEDART":     "BLUEDART.NS",
        "IRCTC":        "IRCTC.NS",
        "THOMASCOOK":   "THOMASCOOK.NS",
        "MAHINDRA":     "M&MFIN.NS",
        "INTERGLOBE":   "INTERGLOBE.NS",
        "GIPCL":        "GIPCL.NS",
        "AIAENG":       "AIAENG.NS",
    },
    "POWER": {
        "TATAPOWER":    "TATAPOWER.NS",
        "ADANIGREEN":   "ADANIGREEN.NS",
        "JSWEN":        "JSWENERGY.NS",
        "TORNTPOWER":   "TORNTPOWER.NS",
        "CESC":         "CESC.NS",
        "NHPC":         "NHPC.NS",
        "SJVN":         "SJVN.NS",
        "INDIAGRID":    "INDIAGRID.NS",
        "POWERINDIA":   "POWERINDIA.NS",
        "RPOWER":       "RPOWER.NS",
    },
    "NBFC": {
        "MUTHOOTFIN":   "MUTHOOTFIN.NS",
        "MANAPPURAM":   "MANAPPURAM.NS",
        "CHOLAFIN":     "CHOLAFIN.NS",
        "LTFH":         "LTFH.NS",
        "POONAWALLA":   "POONAWALLA.NS",
        "SUNDARMFIN":   "SUNDARMFIN.NS",
        "MASFIN":       "MASFIN.NS",
        "AAVAS":        "AAVAS.NS",
        "HOMEFIRST":    "HOMEFIRST.NS",
        "CREDITACC":    "CREDITACC.NS",
    },
    "AGRI": {
        "CHAMBLFERT":   "CHAMBLFERT.NS",
        "COROMANDEL":   "COROMANDEL.NS",
        "UPL":          "UPL.NS",
        "PIIND":        "PIIND.NS",
        "DHANUKA":      "DHANUKA.NS",
        "RALLIS":       "RALLIS.NS",
        "BAYER":        "BAYERCROP.NS",
        "KSCL":         "KSCL.NS",
        "ASTERDM":      "ASTERDM.NS",
        "GODREJAGRO":   "GODREJAGRO.NS",
    },
    "LOGISTICS": {
        "DELHIVERY":    "DELHIVERY.NS",
        "BLUEDART":     "BLUEDART.NS",
        "TCIEXPRESS":   "TCIEXPRESS.NS",
        "VRLLOG":       "VRLLOG.NS",
        "MAHLOG":       "MAHLOG.NS",
        "GATI":         "GATI.NS",
        "ALLCARGO":     "ALLCARGO.NS",
        "XPRESSBEES":   "XPRESSBEES.NS",
        "AEGISLOG":     "AEGISLOG.NS",
        "TVSSCS":       "TVSSCS.NS",
    },
    "MEDIA": {
        "ZEEL":         "ZEEL.NS",
        "SUNTV":        "SUNTV.NS",
        "PVRINOX":      "PVRINOX.NS",
        "TIPSINDLTD":   "TIPSINDLTD.NS",
        "NAZARA":       "NAZARA.NS",
        "NETWORK18":    "NETWORK18.NS",
        "TV18BRDCST":   "TV18BRDCST.NS",
        "SAREGAMA":     "SAREGAMA.NS",
        "BALAJITELE":   "BALAJITELE.NS",
        "DIOCL":        "DIOCL.NS",
    },
    "HOSPITALITY": {
        "INDHOTEL":     "INDHOTEL.NS",
        "LEMONTREE":    "LEMONTREE.NS",
        "EIHOTEL":      "EIHOTEL.NS",
        "CHALET":       "CHALET.NS",
        "MAHINDRAHOLIDAY": "MHRIL.NS",
        "ITCHOTELS":    "ITCHOTELS.NS",
        "KAMAT":        "KAMAT.NS",
        "TAJGVK":       "TAJGVK.NS",
        "WONDERLA":     "WONDERLA.NS",
        "DEVYANI":      "DEVYANI.NS",
    },
    "TEXTILES": {
        "VARDHMAN":     "VTL.NS",
        "ARVIND":       "ARVIND.NS",
        "PAGEIND":      "PAGEIND.NS",
        "WELSPUNIND":   "WELSPUNIND.NS",
        "KPRMILL":      "KPRMILL.NS",
        "RAYMOND":      "RAYMOND.NS",
        "TRIDENT":      "TRIDENT.NS",
        "GRASIM":       "GRASIM.NS",
        "NITIN":        "NITINSPIN.NS",
        "ALOKTEXT":     "ALOKTEXT.NS",
    },
    "JEWELLERY": {
        "KALYANKJIL":   "KALYANKJIL.NS",
        "RAJESHEXPO":   "RAJESHEXPO.NS",
        "SENCO":        "SENCO.NS",
        "PCJEWELLER":   "PCJEWELLER.NS",
        "GOLDIAM":      "GOLDIAM.NS",
        "THANGAMAYL":   "THANGAMAYL.NS",
        "TITAN":        "TITAN.NS",
        "VAIBHAVGBL":   "VAIBHAVGBL.NS",
        "KDDL":         "KDDL.NS",
        "RENAISSANCE":  "RENAISSANCEJEWELRY.NS",
    },
    "SUGAR": {
        "BALRAMCHIN":   "BALRAMCHIN.NS",
        "DHAMPUR":      "DHAMPURSUG.NS",
        "TRIVENI":      "TRIVENI.NS",
        "RENUKA":       "RENUKA.NS",
        "DWARIKESH":    "DWARIKESH.NS",
        "UTTAMSUGAR":   "UTTAMSUGAR.NS",
        "EIDPARRY":     "EIDPARRY.NS",
        "DCHL":         "DCHL.NS",
        "BAJAJHIND":    "BAJAJHIND.NS",
        "SHREERENUKA":  "SHREERENUKA.NS",
    },
    "PAPER": {
        "JKPAPER":      "JKPAPER.NS",
        "TNPL":         "TNPL.NS",
        "WESTCOAST":    "WESTCOAST.NS",
        "ANDPAPER":     "ANDPAPER.NS",
        "NRCL":         "NRCL.NS",
        "SAPPHIRE":     "SAPPHIRE.NS",
        "TAMILNADUPAPER": "TNPL.NS",
        "SESHASAYEE":   "SESHASAYEE.NS",
        "STARPAPER":    "STARPAPER.NS",
        "EMAMIPAPER":   "EMAMIPAPER.NS",
    },
    "SHIPPING": {
        "GESHIP":       "GESHIP.NS",
        "SCI":          "SCI.NS",
        "SEAMECLTD":    "SEAMECLTD.NS",
        "SHREYAS":      "SHREYAS.NS",
        "ESCOSHIP":     "ESCOSHIP.NS",
        "MPSLTD":       "MPSLTD.NS",
        "TOLANI":       "TOLANI.NS",
        "GREATSHIP":    "GREATSHIP.NS",
        "FIVESTAR":     "FIVESTAR.NS",
        "TRANSSHIP":    "TRANSSHIP.NS",
    },
}

# ─────────────────────────────────────────────────────────────
# US STOCKS
# ─────────────────────────────────────────────────────────────
US_STOCKS = {
    "AsterLabs":  "ALAB",
}


# ─────────────────────────────────────────────────────────────
# CRYPTO TICKERS
# ─────────────────────────────────────────────────────────────
CRYPTO = {
    "Bitcoin":    "BTC-USD",
    "Ethereum":   "ETH-USD",
    "ShibaInu":   "SHIB-USD",
    "BNB":        "BNB-USD",
    "Solana":     "SOL-USD",
    "XRP":        "XRP-USD",
    "USDC":       "USDC-USD",
    "Cardano":    "ADA-USD",
    "Avalanche":  "AVAX-USD",
    "Dogecoin":   "DOGE-USD",
}

# ─────────────────────────────────────────────────────────────
# METALS TICKERS
# ─────────────────────────────────────────────────────────────
METALS = {
    "Gold (USD)":    "GC=F",
    "Silver (USD)":  "SI=F",
    "Gold (INR)":    "GOLD.NS",
    "Silver (INR)":  "SILVERMIC.NS",
    "Platinum":      "PL=F",
    "Copper":        "HG=F",
}

# ─────────────────────────────────────────────────────────────
# FOREX TICKERS  (vs USD)
# ─────────────────────────────────────────────────────────────
FOREX = {
    "USD/INR":  "USDINR=X",
    "EUR/USD":  "EURUSD=X",
    "GBP/USD":  "GBPUSD=X",
    "USD/JPY":  "USDJPY=X",
    "USD/CNY":  "USDCNY=X",
    "AUD/USD":  "AUDUSD=X",
    "USD/CAD":  "USDCAD=X",
    "USD/CHF":  "USDCHF=X",
    "USD/SGD":  "USDSGD=X",
    "USD/AED":  "USDAED=X",
}

# ─────────────────────────────────────────────────────────────
# THRESHOLDS
# ─────────────────────────────────────────────────────────────
T = {
    "roe_good": 15.0, "roe_ok": 10.0,
    "de_safe":   1.0, "de_ok":   2.0,
    "pe_cheap": 20.0, "pe_fair": 35.0,
    "nm_good":  15.0, "nm_ok":    8.0,
    "rg_good":  15.0, "rg_ok":    5.0,
    "score_buy": 70,  "score_watch": 50,
    "atr_sl":    1.5,
    "atr_rr":    2.0,
}


# ─────────────────────────────────────────────────────────────
# 1. FUNDAMENTAL DATA FETCH
# ─────────────────────────────────────────────────────────────
def fetch_fundamentals(symbol: str, name: str) -> dict:
    try:
        tk   = yf.Ticker(symbol)
        info = tk.info
        price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        mktcap = info.get("marketCap", 0)
        w52h = info.get("fiftyTwoWeekHigh", 0)
        w52l = info.get("fiftyTwoWeekLow",  0)
        de = info.get("debtToEquity")
        if de: de /= 100
        hist = tk.history(period="1y")
        p_old = float(hist["Close"].iloc[0])  if len(hist) > 1 else None
        p_now = float(hist["Close"].iloc[-1]) if len(hist) > 1 else price
        ann_ret = round((p_now - p_old) / p_old * 100, 2) if p_old else None
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
            rev_gr=round((info.get("revenueGrowth")  or 0)*100, 2),
            earn_gr=round((info.get("earningsGrowth")or 0)*100, 2),
            div_yld=round((info.get("dividendYield") or 0)*100, 2),
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
# 2. PRICE LEVELS  (ATR + Support/Resistance)
# ─────────────────────────────────────────────────────────────
def fetch_price_levels(symbol: str) -> dict:
    try:
        tk = yf.Ticker(symbol)
        h6 = tk.history(period="6mo")
        h5 = tk.history(period="5y")
        h1 = tk.history(period="1y")
        if len(h6) < 20:
            return {"error": "Insufficient history"}
        cl = h6["Close"]; hi = h6["High"]; lo = h6["Low"]
        cp   = float(cl.iloc[-1])
        w52h = float(hi.max()); w52l = float(lo.min())
        ath  = float(h5["High"].max()) if len(h5)>5 else w52h
        atl  = float(h5["Low"].min())  if len(h5)>5 else w52l
        pc   = cl.shift(1)
        tr   = pd.concat([hi-lo,(hi-pc).abs(),(lo-pc).abs()],axis=1).max(axis=1)
        atr  = float(tr.rolling(14).mean().iloc[-1])
        rec  = h6.tail(63)
        rlo  = rec["Low"].values; rhi = rec["High"].values
        sups, ress = [], []
        for i in range(2, len(rlo)-2):
            if rlo[i]<rlo[i-1] and rlo[i]<rlo[i+1] and rlo[i]<rlo[i-2] and rlo[i]<rlo[i+2]:
                sups.append(float(rlo[i]))
        for i in range(2, len(rhi)-2):
            if rhi[i]>rhi[i-1] and rhi[i]>rhi[i+1] and rhi[i]>rhi[i-2] and rhi[i]>rhi[i+2]:
                ress.append(float(rhi[i]))
        sups_below = sorted([s for s in sups if s < cp], reverse=True)
        ress_above = sorted([r for r in ress if r > cp])
        support    = sups_below[0] if sups_below else float(rlo.min())
        resistance = ress_above[0] if ress_above else float(rhi.max())
        buy   = round(cp if cp <= support+1.5*atr else support+0.5*atr, 2)
        buy_h = round(buy + atr, 2)
        sl    = round(support - T["atr_sl"]*atr, 2)
        risk  = round(buy - sl, 2)
        t1    = round(buy + T["atr_rr"]*risk, 2)
        t2    = round(resistance, 2)
        t3    = round(w52h, 2)
        reward = max(t1,t2) - buy
        rr    = round(reward/risk, 2) if risk > 0 else 0
        sma200 = float(h1["Close"].rolling(200).mean().iloc[-1]) if len(h1)>=200 else None
        rng_pct = round((cp-w52l)/(w52h-w52l)*100,1) if (w52h-w52l)>0 else 50
        return dict(
            error=None, cp=round(cp,2), atr=round(atr,2),
            w52h=w52h, w52l=w52l, ath=round(ath,2), atl=round(atl,2),
            rng_pct=rng_pct, support=round(support,2), resistance=round(resistance,2),
            all_supports=[round(s,2) for s in sups_below[:3]],
            all_resistances=[round(r,2) for r in ress_above[:3]],
            buy=buy, buy_h=buy_h, sl=sl, risk=risk,
            t1=t1, t1_pct=round((t1-cp)/cp*100,1),
            t2=t2, t2_pct=round((t2-cp)/cp*100,1),
            t3=t3, t3_pct=round((t3-cp)/cp*100,1),
            rr=rr, sl_pct=round((cp-sl)/cp*100,1),
            sma200=round(sma200,2) if sma200 else None,
            above_200=(cp>sma200) if sma200 else None,
            shares_10k=int(10000/buy) if buy>0 else 0,
            max_loss=round(int(10000/buy)*risk,2) if buy>0 else 0,
        )
    except Exception as e:
        return {"error": str(e)[:100]}


# ─────────────────────────────────────────────────────────────
# 3. CRYPTO DATA FETCH
# ─────────────────────────────────────────────────────────────
def fetch_crypto(symbol: str, name: str) -> dict:
    try:
        tk   = yf.Ticker(symbol)
        info = tk.info
        hist = tk.history(period="1y")
        if len(hist) < 2:
            return dict(name=name, ticker=symbol, error="No data")

        cp     = float(hist["Close"].iloc[-1])
        p_7d   = float(hist["Close"].iloc[-8])  if len(hist)>=8  else cp
        p_30d  = float(hist["Close"].iloc[-31]) if len(hist)>=31 else cp
        p_1y   = float(hist["Close"].iloc[0])

        ret_7d  = round((cp - p_7d)  / p_7d  * 100, 2)
        ret_30d = round((cp - p_30d) / p_30d * 100, 2)
        ret_1y  = round((cp - p_1y)  / p_1y  * 100, 2)

        w52h = float(hist["High"].max())
        w52l = float(hist["Low"].min())
        rng_pct = round((cp-w52l)/(w52h-w52l)*100,1) if (w52h-w52l)>0 else 50

        mktcap = info.get("marketCap", 0)
        vol24h = info.get("volume24Hr") or info.get("regularMarketVolume", 0)

        # ATR for volatility
        pc  = hist["Close"].shift(1)
        tr  = pd.concat([hist["High"]-hist["Low"],
                         (hist["High"]-pc).abs(),
                         (hist["Low"]-pc).abs()], axis=1).max(axis=1)
        atr = float(tr.rolling(14).mean().iloc[-1])
        volatility = round(atr/cp*100, 2)

        # Simple momentum score
        score = 50
        if ret_7d  > 5:  score += 10
        elif ret_7d < -5: score -= 10
        if ret_30d > 10: score += 15
        elif ret_30d < -10: score -= 15
        if ret_1y  > 50: score += 15
        elif ret_1y < -30: score -= 15
        if rng_pct < 30: score += 10  # near 52W low = opportunity
        elif rng_pct > 80: score -= 10
        score = max(0, min(100, score))

        return dict(
            name=name, ticker=symbol, error=None,
            price=round(cp, 6) if cp < 1 else round(cp, 2),
            mktcap_b=round(mktcap/1e9, 2) if mktcap else None,
            vol24h_b=round(vol24h/1e9, 2) if vol24h else None,
            ret_7d=ret_7d, ret_30d=ret_30d, ret_1y=ret_1y,
            w52h=round(w52h,6) if cp<1 else round(w52h,2),
            w52l=round(w52l,6) if cp<1 else round(w52l,2),
            rng_pct=rng_pct,
            volatility=volatility,
            atr=round(atr,6) if cp<1 else round(atr,2),
            score=score,
        )
    except Exception as e:
        return dict(name=name, ticker=symbol, error=str(e)[:100])


# ─────────────────────────────────────────────────────────────
# 4. METALS DATA FETCH
# ─────────────────────────────────────────────────────────────
def fetch_metal(symbol: str, name: str) -> dict:
    try:
        tk   = yf.Ticker(symbol)
        hist = tk.history(period="1y")
        if len(hist) < 2:
            return dict(name=name, ticker=symbol, error="No data")

        cp    = float(hist["Close"].iloc[-1])
        p_1d  = float(hist["Close"].iloc[-2])
        p_7d  = float(hist["Close"].iloc[-8])  if len(hist)>=8  else cp
        p_30d = float(hist["Close"].iloc[-31]) if len(hist)>=31 else cp
        p_1y  = float(hist["Close"].iloc[0])

        ret_1d  = round((cp-p_1d) /p_1d *100, 2)
        ret_7d  = round((cp-p_7d) /p_7d *100, 2)
        ret_30d = round((cp-p_30d)/p_30d*100, 2)
        ret_1y  = round((cp-p_1y) /p_1y *100, 2)

        w52h = float(hist["High"].max())
        w52l = float(hist["Low"].min())
        rng_pct = round((cp-w52l)/(w52h-w52l)*100,1) if (w52h-w52l)>0 else 50

        # SMA trend
        sma50  = float(hist["Close"].rolling(50).mean().iloc[-1])  if len(hist)>=50  else None
        sma200 = float(hist["Close"].rolling(200).mean().iloc[-1]) if len(hist)>=200 else None
        trend  = "↑ Uptrend" if sma200 and cp>sma200 else "↓ Downtrend" if sma200 else "N/A"

        return dict(
            name=name, ticker=symbol, error=None,
            price=round(cp,2),
            ret_1d=ret_1d, ret_7d=ret_7d, ret_30d=ret_30d, ret_1y=ret_1y,
            w52h=round(w52h,2), w52l=round(w52l,2), rng_pct=rng_pct,
            sma50=round(sma50,2) if sma50 else None,
            sma200=round(sma200,2) if sma200 else None,
            trend=trend,
        )
    except Exception as e:
        return dict(name=name, ticker=symbol, error=str(e)[:100])


# ─────────────────────────────────────────────────────────────
# 5. FOREX DATA FETCH
# ─────────────────────────────────────────────────────────────
def fetch_forex(symbol: str, name: str) -> dict:
    try:
        tk   = yf.Ticker(symbol)
        hist = tk.history(period="1y")
        if len(hist) < 2:
            return dict(name=name, ticker=symbol, error="No data")

        cp    = float(hist["Close"].iloc[-1])
        p_1d  = float(hist["Close"].iloc[-2])
        p_7d  = float(hist["Close"].iloc[-8])  if len(hist)>=8  else cp
        p_30d = float(hist["Close"].iloc[-31]) if len(hist)>=31 else cp
        p_1y  = float(hist["Close"].iloc[0])

        ret_1d  = round((cp-p_1d) /p_1d *100, 2)
        ret_7d  = round((cp-p_7d) /p_7d *100, 2)
        ret_30d = round((cp-p_30d)/p_30d*100, 2)
        ret_1y  = round((cp-p_1y) /p_1y *100, 2)

        w52h = float(hist["High"].max())
        w52l = float(hist["Low"].min())
        rng_pct = round((cp-w52l)/(w52h-w52l)*100,1) if (w52h-w52l)>0 else 50

        sma200 = float(hist["Close"].rolling(200).mean().iloc[-1]) if len(hist)>=200 else None
        trend  = "↑ Strong" if sma200 and cp>sma200 else "↓ Weak" if sma200 else "N/A"

        return dict(
            name=name, ticker=symbol, error=None,
            rate=round(cp,4),
            ret_1d=ret_1d, ret_7d=ret_7d, ret_30d=ret_30d, ret_1y=ret_1y,
            w52h=round(w52h,4), w52l=round(w52l,4), rng_pct=rng_pct,
            sma200=round(sma200,4) if sma200 else None,
            trend=trend,
        )
    except Exception as e:
        return dict(name=name, ticker=symbol, error=str(e)[:100])


# ─────────────────────────────────────────────────────────────
# 6. SCORING ENGINE  (stocks)
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
    elif pe <= 0:                        red.append(f"P/E {pe} (negative ✗)")
    elif pe <= T["pe_cheap"]: sc+=15; green.append(f"P/E {pe:.1f} (cheap ✓)")
    elif pe <= T["pe_fair"]:  sc+=8;  green.append(f"P/E {pe:.1f} (fair)")
    else:                                red.append(f"P/E {pe:.1f} (expensive ✗)")
    nm = d.get("net_margin", 0) or 0
    if   nm >= T["nm_good"]: sc+=15; green.append(f"Net margin {nm:.1f}% ✓")
    elif nm >= T["nm_ok"]:   sc+=8;  green.append(f"Net margin {nm:.1f}% (ok)")
    elif nm > 0:             sc+=3;   red.append(f"Net margin {nm:.1f}% (thin)")
    else:                              red.append(f"Net margin {nm:.1f}% (loss ✗)")
    rg = d.get("rev_gr", 0) or 0
    if   rg >= T["rg_good"]: sc+=15; green.append(f"Rev growth {rg:.1f}% ✓")
    elif rg >= T["rg_ok"]:   sc+=8;  green.append(f"Rev growth {rg:.1f}% (ok)")
    elif rg > 0:             sc+=3;   red.append(f"Rev growth {rg:.1f}% (slow)")
    else:                              red.append(f"Rev growth {rg:.1f}% (shrinking ✗)")
    fcf = d.get("fcf_cr")
    if   fcf and fcf > 0: sc+=10; green.append(f"FCF ₹{fcf:.0f}Cr ✓")
    elif fcf and fcf < 0:           red.append(f"FCF ₹{fcf:.0f}Cr (burning ✗)")
    ins = d.get("insider", 0) or 0
    if   ins >= 50: sc+=5; green.append(f"Promoter {ins:.1f}% ✓")
    elif ins >= 30: sc+=3; green.append(f"Promoter {ins:.1f}% (ok)")
    else:                   red.append(f"Promoter {ins:.1f}% (low)")
    dy = d.get("div_yld", 0) or 0
    if dy >= 2: sc+=5; green.append(f"Div yield {dy:.1f}% ✓")
    elif dy>0:  sc+=2
    return min(sc, 100), green, red


def sig(score):
    if score >= T["score_buy"]:   return "🟢 BUY",   "green"
    if score >= T["score_watch"]: return "🟡 WATCH",  "yellow"
    return                               "🔴 AVOID",  "red"


# ─────────────────────────────────────────────────────────────
# 7. DISPLAY: FUNDAMENTAL TABLE
# ─────────────────────────────────────────────────────────────
def show_fundamentals(results, title="NIFTY 50"):
    tbl = Table(
        title=f"📊 {title} — Fundamental Scan  {datetime.now():%d %b %Y %H:%M}",
        box=box.ROUNDED, show_lines=True,
        header_style="bold cyan", title_style="bold white on dark_blue",
    )
    for c,s,w,j in [
        ("Company","bold white",14,"left"), ("Price ₹","",9,"right"),
        ("Score","",7,"center"),            ("Signal","",10,"center"),
        ("P/E","",6,"right"),               ("ROE%","",7,"right"),
        ("D/E","",6,"right"),               ("Net M%","",8,"right"),
        ("RevGr%","",8,"right"),            ("FCF ₹Cr","",9,"right"),
        ("52W Pos","",10,"center"),         ("1Y Ret%","",8,"right"),
    ]:
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
# 8. DISPLAY: CRYPTO TABLE
# ─────────────────────────────────────────────────────────────
def show_crypto(results):
    tbl = Table(
        title=f"🪙 Crypto Monitor  {datetime.now():%d %b %Y %H:%M}",
        box=box.ROUNDED, show_lines=True,
        header_style="bold magenta", title_style="bold white on dark_blue",
    )
    for c,w,j in [
        ("Coin",12,"left"),       ("Price USD",12,"right"),
        ("7D %",8,"right"),       ("30D %",8,"right"),
        ("1Y %",8,"right"),       ("Mkt Cap $B",11,"right"),
        ("Volatility",11,"right"),("52W Pos",10,"center"),
        ("Momentum",10,"center"),
    ]:
        tbl.add_column(c, width=w, justify=j)

    def pct(v):
        if v is None: return "[dim]N/A[/dim]"
        return f"[green]+{v}%[/green]" if v>0 else f"[red]{v}%[/red]"

    for d in sorted([r for r in results if not r.get("error")],
                    key=lambda x: x.get("score",0), reverse=True):
        rp = d["rng_pct"]
        rng_s = f"[green]{rp}%↙[/green]" if rp<30 else f"[yellow]{rp}%[/yellow]" if rp<70 else f"[red]{rp}%↗[/red]"
        sc = d["score"]
        mom = f"[green]Strong[/green]" if sc>=65 else f"[yellow]Neutral[/yellow]" if sc>=40 else f"[red]Weak[/red]"
        tbl.add_row(
            d["name"], str(d["price"]),
            pct(d.get("ret_7d")), pct(d.get("ret_30d")), pct(d.get("ret_1y")),
            str(d.get("mktcap_b","N/A")),
            f"{d.get('volatility','?')}%",
            rng_s, mom,
        )
    for d in [r for r in results if r.get("error")]:
        tbl.add_row(d["name"], "—","—","—","—","—","—","—","[red]ERR[/red]")
    console.print(tbl)


# ─────────────────────────────────────────────────────────────
# 9. DISPLAY: METALS TABLE
# ─────────────────────────────────────────────────────────────
def show_metals(results):
    tbl = Table(
        title=f"🥇 Metals Monitor  {datetime.now():%d %b %Y %H:%M}",
        box=box.ROUNDED, show_lines=True,
        header_style="bold yellow", title_style="bold white on dark_blue",
    )
    for c,w,j in [
        ("Metal",14,"left"),  ("Price",12,"right"),
        ("1D %",7,"right"),   ("7D %",7,"right"),
        ("30D %",8,"right"),  ("1Y %",8,"right"),
        ("52W Low",10,"right"),("52W High",10,"right"),
        ("52W Pos",10,"center"),("Trend",12,"center"),
    ]:
        tbl.add_column(c, width=w, justify=j)

    def pct(v):
        if v is None: return "[dim]N/A[/dim]"
        return f"[green]+{v}%[/green]" if v>0 else f"[red]{v}%[/red]"

    for d in [r for r in results if not r.get("error")]:
        rp = d["rng_pct"]
        rng_s = f"[green]{rp}%[/green]" if rp<30 else f"[yellow]{rp}%[/yellow]" if rp<70 else f"[red]{rp}%[/red]"
        trend = d.get("trend","N/A")
        tc = "green" if "Up" in trend else "red" if "Down" in trend else "dim"
        tbl.add_row(
            d["name"], str(d["price"]),
            pct(d.get("ret_1d")), pct(d.get("ret_7d")),
            pct(d.get("ret_30d")), pct(d.get("ret_1y")),
            str(d["w52l"]), str(d["w52h"]), rng_s,
            f"[{tc}]{trend}[/{tc}]",
        )
    for d in [r for r in results if r.get("error")]:
        tbl.add_row(d["name"],"—","—","—","—","—","—","—","—","[red]ERR[/red]")
    console.print(tbl)


# ─────────────────────────────────────────────────────────────
# 10. DISPLAY: FOREX TABLE
# ─────────────────────────────────────────────────────────────
def show_forex(results):
    tbl = Table(
        title=f"💱 Forex Monitor — vs USD  {datetime.now():%d %b %Y %H:%M}",
        box=box.ROUNDED, show_lines=True,
        header_style="bold cyan", title_style="bold white on dark_blue",
    )
    for c,w,j in [
        ("Pair",10,"left"),    ("Rate",10,"right"),
        ("1D %",7,"right"),    ("7D %",7,"right"),
        ("30D %",8,"right"),   ("1Y %",8,"right"),
        ("52W Low",10,"right"),("52W High",10,"right"),
        ("52W Pos",10,"center"),("Trend",12,"center"),
    ]:
        tbl.add_column(c, width=w, justify=j)

    def pct(v):
        if v is None: return "[dim]N/A[/dim]"
        return f"[green]+{v}%[/green]" if v>0 else f"[red]{v}%[/red]"

    for d in [r for r in results if not r.get("error")]:
        rp = d["rng_pct"]
        rng_s = f"[green]{rp}%[/green]" if rp<30 else f"[yellow]{rp}%[/yellow]" if rp<70 else f"[red]{rp}%[/red]"
        trend = d.get("trend","N/A")
        tc = "green" if "Strong" in trend else "red" if "Weak" in trend else "dim"
        tbl.add_row(
            d["name"], str(d["rate"]),
            pct(d.get("ret_1d")), pct(d.get("ret_7d")),
            pct(d.get("ret_30d")), pct(d.get("ret_1y")),
            str(d["w52l"]), str(d["w52h"]), rng_s,
            f"[{tc}]{trend}[/{tc}]",
        )
    for d in [r for r in results if r.get("error")]:
        tbl.add_row(d["name"],"—","—","—","—","—","—","—","—","[red]ERR[/red]")
    console.print(tbl)


# ─────────────────────────────────────────────────────────────
# 11. DISPLAY: PRICE LEVELS TABLE
# ─────────────────────────────────────────────────────────────
def show_levels_table(results):
    tbl = Table(
        title=f"📈 Price Levels — Buy / Stoploss / Targets  {datetime.now():%d %b %Y %H:%M}",
        box=box.ROUNDED, show_lines=True,
        header_style="bold magenta", title_style="bold white on dark_blue",
    )
    for c,w,j in [
        ("Company",13,"left"),  ("Now ₹",8,"right"),
        ("52W Low",9,"right"),  ("52W High",9,"right"),
        ("52W Pos",10,"center"),("BUY ZONE ₹",15,"center"),
        ("STOPLOSS",11,"right"),("SL%",6,"right"),
        ("T1 ₹",12,"right"),    ("T2 ₹",12,"right"),
        ("T3 ₹",12,"right"),    ("R:R",6,"center"),
        ("Trend",9,"center"),   ("Signal",10,"center"),
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
            time.sleep(0.25); prog.advance(task)
            sc = d.get("score",0); label, col = sig(sc)
            if lv.get("error"):
                tbl.add_row(d["name"][:12],f"₹{d.get('price','?')}",
                            *["—"]*11, f"[{col}]{label}[/{col}]"); continue
            rp = lv["rng_pct"]
            rng_s = f"[green]{rp}%↙[/green]" if rp<30 else f"[yellow]{rp}%[/yellow]" if rp<65 else f"[red]{rp}%↗[/red]"
            rr    = lv["rr"]
            rr_s  = f"[green]1:{rr}[/green]" if rr>=2 else f"[yellow]1:{rr}[/yellow]"
            trend = "[green]↑200[/green]" if lv.get("above_200") else "[red]↓200[/red]" if lv.get("above_200") is False else "[dim]N/A[/dim]"
            tbl.add_row(
                d["name"][:12], f"₹{lv['cp']}",
                f"₹{lv['w52l']}", f"₹{lv['w52h']}", rng_s,
                f"[green]₹{lv['buy']}–{lv['buy_h']}[/green]",
                f"[red]₹{lv['sl']}[/red]", f"[red]-{lv['sl_pct']}%[/red]",
                f"[cyan]₹{lv['t1']}(+{lv['t1_pct']}%)[/cyan]",
                f"[cyan]₹{lv['t2']}(+{lv['t2_pct']}%)[/cyan]",
                f"[cyan]₹{lv['t3']}(+{lv['t3_pct']}%)[/cyan]",
                rr_s, trend, f"[{col}]{label}[/{col}]",
            )
    console.print(tbl)


# ─────────────────────────────────────────────────────────────
# 12. DISPLAY: SINGLE STOCK DEEP DIVE
# ─────────────────────────────────────────────────────────────
def show_deep_dive(name: str, symbol: str):
    console.print(Rule(f"[bold cyan]{name} ({symbol}) — Full Deep Dive[/bold cyan]"))
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as prog:
        t1 = prog.add_task("Fundamentals…", total=None)
        d  = fetch_fundamentals(symbol, name)
        prog.remove_task(t1)
        t2 = prog.add_task("Price levels…", total=None)
        lv = fetch_price_levels(symbol)
        prog.remove_task(t2)
    if d.get("error"):
        console.print(f"[red]Error: {d['error']}[/red]"); return
    sc, green, red = score_stock(d)
    label, col = sig(sc)
    console.print(Panel(
        f"[bold]Sector:[/bold] {d['sector']}   [bold]Industry:[/bold] {d['industry']}\n"
        f"[bold]Market Cap:[/bold] ₹{d.get('market_cap_cr','?')} Cr   "
        f"[bold]Price:[/bold] ₹{d.get('price','?')}   "
        f"[bold]1Y Return:[/bold] {d.get('ann_ret','?')}%",
        title="Overview", border_style="cyan"))
    bar = "█"*int(sc/5) + "░"*(20-int(sc/5))
    console.print(Panel(f"[{col}]{bar}  {sc}/100[/{col}]\n[{col}]{label}[/{col}]",
                        title="Fundamental Score", border_style=col))
    g = Text(); [g.append(f"  ✅ {x}\n","green") for x in green]
    r = Text(); [r.append(f"  ❌ {x}\n","red")   for x in red]
    if not green: g.append("  (none)","dim")
    if not red:   r.append("  (none)","dim")
    console.print(Panel(g, title="[green]Green Flags[/green]", border_style="green"))
    console.print(Panel(r, title="[red]Red Flags[/red]",       border_style="red"))
    mt = Table(box=box.SIMPLE, header_style="bold magenta")
    mt.add_column("Metric", width=24); mt.add_column("Value", justify="right", width=14)
    mt.add_column("Verdict", width=24)
    def mrow(m,v,vd,good):
        c="green" if good else "red"
        mt.add_row(m, str(v) if v is not None else "[dim]N/A[/dim]", f"[{c}]{vd}[/{c}]")
    pe=d.get("pe"); de=d.get("de"); roe=d.get("roe",0) or 0
    nm=d.get("net_margin",0) or 0; rg=d.get("rev_gr",0) or 0
    mrow("P/E Ratio",pe,"Cheap✓" if pe and pe<20 else "Fair" if pe and pe<35 else "Expensive",pe and 0<pe<35)
    mrow("P/B Ratio",d.get("pb"),"Undervalued" if d.get("pb") and d["pb"]<1 else "Fair+",d.get("pb") and d["pb"]<3)
    mrow("ROE %",f"{roe:.1f}%","Strong✓" if roe>=15 else "OK" if roe>=10 else "Weak",roe>=10)
    mrow("Net Margin %",f"{nm:.1f}%","Healthy✓" if nm>=15 else "OK" if nm>=8 else "Thin",nm>=8)
    mrow("Gross Margin %",f"{d.get('gross_margin',0):.1f}%","Good✓" if d.get("gross_margin",0)>=30 else "Moderate",d.get("gross_margin",0)>=30)
    mrow("Debt/Equity",de,"Safe✓" if de and de<1 else "Moderate" if de and de<2 else "High",de and de<1)
    mrow("Current Ratio",d.get("cur_ratio"),"Liquid✓" if d.get("cur_ratio") and d["cur_ratio"]>=1.5 else "Tight",d.get("cur_ratio") and d["cur_ratio"]>=1.5)
    mrow("Revenue Growth %",f"{rg:.1f}%","Strong✓" if rg>=15 else "OK" if rg>=5 else "Slow",rg>=5)
    mrow("Earnings Growth %",f"{d.get('earn_gr',0):.1f}%","Strong✓" if d.get("earn_gr",0)>=15 else "OK",d.get("earn_gr",0)>=5)
    mrow("Free Cash Flow ₹Cr",d.get("fcf_cr"),"Positive✓" if d.get("fcf_cr") and d["fcf_cr"]>0 else "Negative✗",d.get("fcf_cr") and d["fcf_cr"]>0)
    mrow("Promoter %",f"{d.get('insider',0):.1f}%","High✓" if d.get("insider",0)>=50 else "OK",d.get("insider",0)>=30)
    mrow("Div Yield %",f"{d.get('div_yld',0):.1f}%","Good✓" if d.get("div_yld",0)>=2 else "Nominal",d.get("div_yld",0)>=1)
    console.print(mt)
    if lv.get("error"):
        console.print(f"[red]Price levels: {lv['error']}[/red]"); return
    cp=lv["cp"]; w52h=lv["w52h"]; w52l=lv["w52l"]
    def lrow(label,price,color,marker="◀"):
        span=w52h-w52l; pct=max(0,min(1,(price-w52l)/span)) if span>0 else 0.5
        pos=int(pct*30); bar="─"*pos+marker+"─"*(30-pos)
        return f"[{color}]{label:12s} ₹{price:<10.2f}|{bar}|[/{color}]"
    ladder="\n".join([
        lrow("ATH",lv["ath"],"dim","▲"), lrow("52W HIGH",w52h,"dim","▲"),
        lrow("TARGET 3",lv["t3"],"green","🏁"), lrow("TARGET 2",lv["t2"],"green","🎯"),
        lrow("TARGET 1",lv["t1"],"green","🎯"), lrow("RESIST",lv["resistance"],"yellow","┤"),
        lrow("CURRENT",cp,"cyan","●"), lrow("BUY ZONE",lv["buy"],"green","▶"),
        lrow("SUPPORT",lv["support"],"yellow","├"), lrow("STOPLOSS",lv["sl"],"red","✂"),
        lrow("52W LOW",w52l,"dim","▼"), lrow("ATL",lv["atl"],"dim","▼"),
    ])
    rng=lv["rng_pct"]
    entry=("[green]Near 52W low — good entry zone[/green]" if rng<30 else
           "[yellow]Mid-range — wait for pullback[/yellow]" if rng<65 else
           "[red]Near 52W high — risky to enter[/red]")
    trend_txt=(f"[green]Above 200-SMA ₹{lv.get('sma200','?')} → uptrend ✓[/green]" if lv.get("above_200")
               else f"[red]Below 200-SMA ₹{lv.get('sma200','?')} → downtrend ✗[/red]" if lv.get("above_200") is False
               else "[dim]N/A[/dim]")
    detail=(f"\n  [bold white]ATR-14:[/bold white] ₹{lv['atr']}  ← daily volatility\n\n"
            f"  [bold green]BUY ZONE  :[/bold green] ₹{lv['buy']} → ₹{lv['buy_h']}\n"
            f"  [bold red]STOPLOSS  :[/bold red] ₹{lv['sl']}  ([red]-{lv['sl_pct']}% from buy, risk ₹{lv['risk']}/share[/red])\n\n"
            f"  [bold cyan]TARGET 1  :[/bold cyan] ₹{lv['t1']}  ([cyan]+{lv['t1_pct']}%[/cyan])  ← 1:2 R:R minimum\n"
            f"  [bold cyan]TARGET 2  :[/bold cyan] ₹{lv['t2']}  ([cyan]+{lv['t2_pct']}%[/cyan])  ← Next resistance\n"
            f"  [bold cyan]TARGET 3  :[/bold cyan] ₹{lv['t3']}  ([cyan]+{lv['t3_pct']}%[/cyan])  ← 52W high breakout\n\n"
            f"  [bold white]Risk:Reward:[/bold white] 1:{lv['rr']}  {'[green]✓ Good[/green]' if lv['rr']>=2 else '[yellow]⚠ Marginal[/yellow]'}\n"
            f"  [bold white]52W Range:[/bold white]  {rng}% from bottom → {entry}\n"
            f"  [bold white]Trend:[/bold white]      {trend_txt}\n\n"
            f"  [dim]Supports: {lv['all_supports']}  Resistances: {lv['all_resistances']}[/dim]\n"
            f"  [dim]₹10,000 → {lv['shares_10k']} shares, max loss = ₹{lv['max_loss']}[/dim]")
    console.print(Panel(ladder+detail, title=f"[bold magenta]📈 {name} — Price Levels[/bold magenta]",
                        border_style="magenta"))


# ─────────────────────────────────────────────────────────────
# 13. ALERTS
# ─────────────────────────────────────────────────────────────
def show_alerts(results):
    console.print(Rule("[bold]🔔 Signal Alerts[/bold]"))
    valid = [r for r in results if not r.get("error")]
    buys  = sorted([r for r in valid if r["score"]>=T["score_buy"]],  key=lambda x: x["score"], reverse=True)
    watch = sorted([r for r in valid if T["score_watch"]<=r["score"]<T["score_buy"]], key=lambda x: x["score"], reverse=True)
    avoid = sorted([r for r in valid if r["score"]<T["score_watch"]], key=lambda x: x["score"])
    if buys:
        console.print("\n[bold green]🟢 BUY CANDIDATES[/bold green]")
        for r in buys:
            console.print(f"  [green]▶ {r['name']:14s}[/green]  Score:[bold]{r['score']}[/bold]  "
                          f"P/E:{r.get('pe','?')}  ROE:{r.get('roe','?')}%  RevGr:{r.get('rev_gr','?')}%")
    if watch:
        console.print("\n[bold yellow]🟡 WATCHLIST[/bold yellow]")
        for r in watch:
            console.print(f"  [yellow]▶ {r['name']:14s}[/yellow]  Score:[bold]{r['score']}[/bold]  "
                          f"P/E:{r.get('pe','?')}  ROE:{r.get('roe','?')}%")
    if avoid:
        console.print("\n[bold red]🔴 AVOID[/bold red]")
        for r in avoid:
            console.print(f"  [red]▶ {r['name']:14s}[/red]  Score:[bold]{r['score']}[/bold]")
    console.print()


# ─────────────────────────────────────────────────────────────
# 14. CSV EXPORT
# ─────────────────────────────────────────────────────────────
def export_csv(results, prefix="nifty"):
    fn = f"{prefix}_scan_{datetime.now():%Y%m%d_%H%M}.csv"
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


def export_generic_csv(results, fields, prefix):
    fn = f"{prefix}_{datetime.now():%Y%m%d_%H%M}.csv"
    with open(fn,"w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in results: w.writerow(r)
    console.print(f"\n[green]✓ Exported →[/green] [bold]{fn}[/bold]")


# ─────────────────────────────────────────────────────────────
# 15. SCAN RUNNERS
# ─────────────────────────────────────────────────────────────
def run_scan(tickers=None):
    if tickers is None: tickers = NIFTY50
    results = []
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as prog:
        task = prog.add_task("Scanning...", total=len(tickers))
        for name, sym in tickers.items():
            prog.update(task, description=f"[cyan]Fetching[/cyan] {name}")
            d = fetch_fundamentals(sym, name)
            if not d.get("error"):
                sc, g, r = score_stock(d)
                d["score"]=sc; d["green_flags"]=g; d["red_flags"]=r
            else:
                d["score"]=0
            results.append(d)
            prog.advance(task)
            time.sleep(0.3)
    return results


def run_crypto_scan():
    results = []
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as prog:
        task = prog.add_task("Fetching crypto...", total=len(CRYPTO))
        for name, sym in CRYPTO.items():
            prog.update(task, description=f"[magenta]Crypto[/magenta] {name}")
            results.append(fetch_crypto(sym, name))
            prog.advance(task); time.sleep(0.3)
    return results


def run_metals_scan():
    results = []
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as prog:
        task = prog.add_task("Fetching metals...", total=len(METALS))
        for name, sym in METALS.items():
            prog.update(task, description=f"[yellow]Metal[/yellow] {name}")
            results.append(fetch_metal(sym, name))
            prog.advance(task); time.sleep(0.3)
    return results


def run_forex_scan():
    results = []
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as prog:
        task = prog.add_task("Fetching forex...", total=len(FOREX))
        for name, sym in FOREX.items():
            prog.update(task, description=f"[cyan]Forex[/cyan] {name}")
            results.append(fetch_forex(sym, name))
            prog.advance(task); time.sleep(0.3)
    return results


# ─────────────────────────────────────────────────────────────
# 16. WATCH MODE
# ─────────────────────────────────────────────────────────────
def watch_mode(interval, do_all=False):
    console.print(Panel(f"[cyan]Watch mode — every {interval} min. Ctrl+C to stop.[/cyan]",
                        border_style="cyan"))
    while True:
        os.system("clear")
        results = run_scan()
        show_fundamentals(results)
        show_alerts(results)
        if do_all:
            show_crypto(run_crypto_scan())
            show_metals(run_metals_scan())
            show_forex(run_forex_scan())
        nxt = datetime.now() + timedelta(minutes=interval)
        console.print(f"\n[dim]Next refresh at {nxt:%H:%M:%S}[/dim]")
        time.sleep(interval * 60)


# ─────────────────────────────────────────────────────────────
# 17. MAIN
# ─────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(
        description="Market Research Monitor v3 — Stocks · Crypto · Metals · Forex",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--watch",       action="store_true",  help="Auto-refresh mode")
    ap.add_argument("--interval",    type=int, default=30, help="Refresh interval minutes")
    ap.add_argument("--stock",       type=str,             help="Deep dive: e.g. RELIANCE")
    ap.add_argument("--alerts",      action="store_true",  help="Buy/Watch/Avoid signals only")
    ap.add_argument("--levels",      action="store_true",  help="Price levels for all stocks")
    ap.add_argument("--export",      action="store_true",  help="Export to CSV")
    ap.add_argument("--top",         type=int,             help="Top N stocks by score")
    ap.add_argument("--sectorscan",  action="store_true",  help="10 stocks × 15 sectors")
    ap.add_argument("--sector",      type=str,             help="Single sector e.g. IT BANKING")
    ap.add_argument("--listsectors", action="store_true",  help="List all available sectors and their stocks")
    ap.add_argument("--crypto",      action="store_true",  help="Crypto monitor")
    ap.add_argument("--metals",      action="store_true",  help="Gold & Silver monitor")
    ap.add_argument("--forex",       action="store_true",  help="Top 10 forex vs USD")
    ap.add_argument("--usstocks",    action="store_true",  help="US stocks — Aster Labs (ALAB) deep dive")
    ap.add_argument("--all",         action="store_true",  help="Everything in one go")
    args = ap.parse_args()

    console.print(Panel(
        "[bold cyan]MARKET RESEARCH MONITOR  v3.0[/bold cyan]\n"
        "[dim]Stocks · Crypto · Metals · Forex | Yahoo Finance[/dim]",
        border_style="bright_blue", expand=False))

    # ── Single stock deep dive ───────────────────────────────
    # ── List all sectors ─────────────────────────────────────
    if args.listsectors:
        tbl = Table(
            title="📋 Available Sectors & Stocks",
            box=box.ROUNDED, show_lines=True,
            header_style="bold cyan", title_style="bold white on dark_blue",
        )
        tbl.add_column("Sector",  style="bold green", width=14)
        tbl.add_column("Stocks",  width=80)
        for sec, stocks in SECTORS.items():
            tbl.add_row(sec, "  ".join(stocks.keys()))
        console.print(tbl)
        console.print(f"\n[dim]Total: {len(SECTORS)} sectors, "
                      f"{sum(len(v) for v in SECTORS.values())} stocks[/dim]\n"
                      f"[dim]Usage: nifty --sector DEFENCE[/dim]")
        return

    if args.stock:
        name = args.stock.upper()
        sym  = NIFTY50.get(name)
        if not sym:
            for s in SECTORS.values():
                if name in s: sym = s[name]; break
        if not sym:
            sym = name if name.endswith((".NS",".BO")) else name+".NS"
        show_deep_dive(name, sym)
        return

    # ── Watch mode ───────────────────────────────────────────
    if args.watch:
        watch_mode(args.interval, do_all=args.all); return

    # ── Sector scan ──────────────────────────────────────────
    if args.sectorscan or args.sector:
        sectors_to_scan = {}
        if args.sector:
            sec = args.sector.upper()
            if sec in SECTORS:
                sectors_to_scan = {sec: SECTORS[sec]}
            else:
                console.print(f"[red]Unknown sector '{sec}'. Available: {', '.join(SECTORS.keys())}[/red]")
                return
        else:
            sectors_to_scan = SECTORS

        for sec_name, tickers in sectors_to_scan.items():
            console.print(f"\n[bold cyan]━━━ {sec_name} SECTOR ━━━[/bold cyan]")
            results = run_scan(tickers)
            show_fundamentals(results, title=f"{sec_name} Sector")
            show_alerts(results)
            if args.export:
                export_csv(results, prefix=f"sector_{sec_name.lower()}")
        return

    # ── Crypto ───────────────────────────────────────────────
    if args.crypto or args.all:
        console.print("\n[bold magenta]━━━ CRYPTO MONITOR ━━━[/bold magenta]")
        cr = run_crypto_scan()
        show_crypto(cr)
        if args.export:
            export_generic_csv(cr,
                ["name","ticker","price","ret_7d","ret_30d","ret_1y",
                 "mktcap_b","volatility","rng_pct","score"],
                "crypto")

    # ── Metals ───────────────────────────────────────────────
    if args.metals or args.all:
        console.print("\n[bold yellow]━━━ METALS MONITOR ━━━[/bold yellow]")
        mt = run_metals_scan()
        show_metals(mt)
        if args.export:
            export_generic_csv(mt,
                ["name","ticker","price","ret_1d","ret_7d","ret_30d","ret_1y",
                 "w52l","w52h","rng_pct","trend"],
                "metals")

    # ── Forex ────────────────────────────────────────────────
    if args.forex or args.all:
        console.print("\n[bold cyan]━━━ FOREX MONITOR ━━━[/bold cyan]")
        fx = run_forex_scan()
        show_forex(fx)
        if args.export:
            export_generic_csv(fx,
                ["name","ticker","rate","ret_1d","ret_7d","ret_30d","ret_1y",
                 "w52l","w52h","rng_pct","trend"],
                "forex")

    # ── US Stocks ────────────────────────────────────────────
    if args.usstocks or args.all:
        console.print("\n[bold green]━━━ US STOCKS ━━━[/bold green]")
        for name, sym in US_STOCKS.items():
            show_deep_dive(name, sym)

    # ── NIFTY 50 (default or --all) ──────────────────────────
    if not any([args.crypto, args.metals, args.forex, args.sectorscan,
                args.sector, args.usstocks]) or args.all:
        console.print("\n[bold cyan]━━━ NIFTY 50 ━━━[/bold cyan]")
        results = run_scan()

        if not args.alerts:
            pool = sorted([r for r in results if not r.get("error")],
                          key=lambda x: x.get("score",0), reverse=True)
            show_fundamentals(pool[:args.top] if args.top else results)

        show_alerts(results)

        if args.levels:
            console.print("\n[bold magenta]Fetching price levels...[/bold magenta]\n")
            show_levels_table(results)

        if args.export:
            export_csv(results)

        valid = [r for r in results if not r.get("error")]
        console.print(Panel(
            f"[green]🟢 Buy: {sum(1 for r in valid if r['score']>=T['score_buy'])}[/green]   "
            f"[yellow]🟡 Watch: {sum(1 for r in valid if T['score_watch']<=r['score']<T['score_buy'])}[/yellow]   "
            f"[red]🔴 Avoid: {sum(1 for r in valid if r['score']<T['score_watch'])}[/red]   "
            f"[dim]Errors: {len(results)-len(valid)}[/dim]",
            title="Scan Summary", border_style="bright_blue"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")
