"""
Phase 1 — Data Collection
Downloads daily adjusted closing prices for SPY, RSP, and XLG
from Yahoo Finance via yfinance and saves them to data/raw/.

Usage:
    python src/download.py
"""

import os
import yfinance as yf
import pandas as pd
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────

TICKERS   = ["SPY", "RSP", "XLG"]
START     = "2007-01-01"          # RSP launched 2003; 2007 gives GFC baseline
END       = datetime.today().strftime("%Y-%m-%d")
RAW_DIR   = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


# ── Helpers ───────────────────────────────────────────────────────────────────

def download_ticker(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Download adjusted close for a single ticker."""
    print(f"  Downloading {ticker}...")
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for {ticker}. Check ticker or date range.")
    # Keep only Close; rename to ticker symbol
    close = df[["Close"]].rename(columns={"Close": ticker})
    return close


def save_raw(df: pd.DataFrame, ticker: str) -> str:
    """Save a single ticker's prices to data/raw/<TICKER>.csv."""
    os.makedirs(RAW_DIR, exist_ok=True)
    path = os.path.join(RAW_DIR, f"{ticker}.csv")
    df.to_csv(path)
    print(f"  Saved → {path}  ({len(df)} rows)")
    return path


def download_all() -> pd.DataFrame:
    """
    Download all tickers, save individual CSVs, and return a
    combined DataFrame with one column per ticker.
    """
    print(f"\nDownloading data from {START} to {END}")
    print("=" * 50)

    frames = []
    for ticker in TICKERS:
        df = download_ticker(ticker, START, END)
        save_raw(df, ticker)
        frames.append(df)

    # Combine into one aligned DataFrame (inner join on trading days)
    combined = pd.concat(frames, axis=1).dropna()
    combined.index.name = "Date"

    combined_path = os.path.join(RAW_DIR, "combined.csv")
    combined.to_csv(combined_path)
    print(f"\nCombined file → {combined_path}  ({len(combined)} trading days)")
    print(f"Date range:  {combined.index[0].date()}  →  {combined.index[-1].date()}")
    print(f"Columns:     {list(combined.columns)}")
    return combined


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    data = download_all()
    print("\nSample (last 5 rows):")
    print(data.tail())
    print("\nDownload complete.")
