"""
Phase 2 — Quantitative Analysis
Computes the RSP/SPY ratio, rolling Z-score, and tests for cointegration.

Usage:
    python src/analysis.py
"""

import os
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import coint

RAW_DIR       = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
ZSCORE_WINDOW = 252    # 1 trading year rolling window for Z-score
RATIO_FLOOR   = 0.32   # MAPsignals trigger level


# ── Load ──────────────────────────────────────────────────────────────────────

def load_prices() -> pd.DataFrame:
    """Load combined price CSV from data/raw/."""
    path = os.path.join(RAW_DIR, "combined.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            "data/raw/combined.csv not found. Run `python src/download.py` first."
        )
    df = pd.read_csv(path, index_col="Date", parse_dates=True)
    # Flatten MultiIndex columns if yfinance wrote them that way
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    return df


# ── Ratio & Z-score ───────────────────────────────────────────────────────────

def compute_ratio(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate RSP/SPY ratio normalized to 100 on the first date,
    plus rolling Z-score of the ratio.
    """
    df = prices[["SPY", "RSP"]].copy()

    # Normalize both series to 100 at start (shows relative performance)
    df["SPY_idx"] = df["SPY"] / df["SPY"].iloc[0] * 100
    df["RSP_idx"] = df["RSP"] / df["RSP"].iloc[0] * 100

    # Raw ratio (used by MAPsignals — RSP price / SPY price)
    df["ratio_raw"] = df["RSP"] / df["SPY"]

    # Normalized ratio (100 at start) — easier to visualize trend
    df["ratio"] = df["RSP_idx"] / df["SPY_idx"]

    # Rolling Z-score of the normalized ratio
    roll = df["ratio"].rolling(ZSCORE_WINDOW)
    df["ratio_mean"] = roll.mean()
    df["ratio_std"]  = roll.std()
    df["zscore"]     = (df["ratio"] - df["ratio_mean"]) / df["ratio_std"]

    # Boolean flag: ratio_raw below MAPsignals trigger
    df["maps_trigger"] = df["ratio_raw"] <= RATIO_FLOOR

    return df


# ── Cointegration test ────────────────────────────────────────────────────────

def test_cointegration(prices: pd.DataFrame) -> dict:
    """
    Engle-Granger cointegration test on log prices of SPY and RSP.
    Returns dict with test statistic, p-value, and interpretation.
    """
    log_spy = np.log(prices["SPY"].dropna())
    log_rsp = np.log(prices["RSP"].dropna())

    # Align on common dates
    aligned = pd.concat([log_spy, log_rsp], axis=1).dropna()
    log_spy_a = aligned.iloc[:, 0]
    log_rsp_a = aligned.iloc[:, 1]

    score, pvalue, crit_values = coint(log_spy_a, log_rsp_a)

    result = {
        "test":         "Engle-Granger",
        "statistic":    round(float(score), 4),
        "p_value":      round(float(pvalue), 4),
        "crit_1pct":    round(float(crit_values[0]), 4),
        "crit_5pct":    round(float(crit_values[1]), 4),
        "crit_10pct":   round(float(crit_values[2]), 4),
        "cointegrated": pvalue < 0.05,
    }

    print("\nCointegration Test (Engle-Granger)")
    print("=" * 40)
    print(f"  Test statistic : {result['statistic']}")
    print(f"  p-value        : {result['p_value']}")
    print(f"  Critical (5%)  : {result['crit_5pct']}")
    print(f"  Cointegrated   : {'YES ✓' if result['cointegrated'] else 'NO ✗'}")
    if result["cointegrated"]:
        print("  → SPY and RSP share a long-run equilibrium.")
        print("    Divergences are temporary — mean reversion is expected.")
    else:
        print("  → No statistical evidence of cointegration.")
    return result


# ── Spread summary ────────────────────────────────────────────────────────────

def spread_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify all dates where Z-score crossed key thresholds.
    Returns a summary DataFrame of extreme divergence episodes.
    """
    extremes = df[df["zscore"].abs() >= 2.0][["zscore", "ratio", "ratio_raw", "maps_trigger"]].copy()
    extremes["signal"] = extremes["zscore"].apply(
        lambda z: "RSP cheap (buy RSP)" if z <= -2 else "RSP expensive (buy SPY)"
    )
    return extremes


# ── Save & run ────────────────────────────────────────────────────────────────

def run_analysis() -> pd.DataFrame:
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    prices = load_prices()

    print(f"\nLoaded {len(prices)} trading days  "
          f"({prices.index[0].date()} → {prices.index[-1].date()})")

    # Ratio & Z-score
    df = compute_ratio(prices)
    out_path = os.path.join(PROCESSED_DIR, "ratio_zscore.csv")
    df.to_csv(out_path)
    print(f"\nRatio + Z-score saved → {out_path}")

    # Quick stats
    current_z = df["zscore"].iloc[-1]
    current_ratio = df["ratio_raw"].iloc[-1]
    print(f"\nCurrent snapshot ({df.index[-1].date()}):")
    print(f"  RSP/SPY ratio (raw) : {current_ratio:.4f}")
    print(f"  Z-score             : {current_z:.2f}")
    trigger_days = df["maps_trigger"].sum()
    print(f"  Days below {RATIO_FLOOR} trigger : {trigger_days}")

    # Cointegration
    coint_result = test_cointegration(prices)

    # Extremes
    extremes = spread_summary(df)
    ext_path = os.path.join(PROCESSED_DIR, "extreme_dates.csv")
    extremes.to_csv(ext_path)
    print(f"\nExtreme divergence dates ({len(extremes)} rows) → {ext_path}")

    return df


if __name__ == "__main__":
    df = run_analysis()
    print("\nLast 5 rows of ratio_zscore:")
    print(df[["SPY", "RSP", "ratio", "zscore"]].tail())
