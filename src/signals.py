"""
Phase 3 — Signal Generation
Converts Z-score extremes into actionable long/short signals
and computes forward returns for each trigger date.

Usage:
    python src/signals.py
"""

import os
import pandas as pd
import numpy as np

PROCESSED_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
ENTRY_ZSCORE   = -2.0   # Enter long RSP when Z-score drops below this
EXIT_ZSCORE    =  0.0   # Exit when Z-score reverts to mean
HORIZONS       = [126, 252, 504]   # 6m, 12m, 24m in trading days
HORIZON_LABELS = {126: "6m", 252: "12m", 504: "24m"}


# ── Load ──────────────────────────────────────────────────────────────────────

def load_processed() -> pd.DataFrame:
    path = os.path.join(PROCESSED_DIR, "ratio_zscore.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            "data/processed/ratio_zscore.csv not found. "
            "Run `python src/analysis.py` first."
        )
    return pd.read_csv(path, index_col="Date", parse_dates=True)


# ── Signal logic ──────────────────────────────────────────────────────────────

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mark entry dates where Z-score first crosses below ENTRY_ZSCORE
    (after a gap of at least 63 trading days from the prior signal,
    to avoid clustering).
    """
    signals = []
    last_signal_idx = -63   # allow signal on day 0

    for i, (date, row) in enumerate(df.iterrows()):
        if pd.isna(row["zscore"]):
            continue
        if row["zscore"] <= ENTRY_ZSCORE and (i - last_signal_idx) >= 63:
            signals.append({"date": date, "entry_zscore": row["zscore"],
                            "entry_ratio": row["ratio_raw"]})
            last_signal_idx = i

    return pd.DataFrame(signals).set_index("date") if signals else pd.DataFrame()


# ── Forward returns ───────────────────────────────────────────────────────────

def compute_forward_returns(df: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    """
    For each signal date, compute SPY and RSP forward total returns
    at each horizon (6m, 12m, 24m).
    """
    rows = []

    for entry_date in signals.index:
        if entry_date not in df.index:
            continue
        entry_spy = df.loc[entry_date, "SPY"]
        entry_rsp = df.loc[entry_date, "RSP"]
        row = {
            "entry_date":   entry_date,
            "entry_zscore": signals.loc[entry_date, "entry_zscore"],
        }

        future_dates = df.index[df.index > entry_date]

        for h in HORIZONS:
            label = HORIZON_LABELS[h]
            if len(future_dates) >= h:
                target_date = future_dates[h - 1]
                spy_ret = (df.loc[target_date, "SPY"] / entry_spy - 1) * 100
                rsp_ret = (df.loc[target_date, "RSP"] / entry_rsp - 1) * 100
                row[f"SPY_{label}"]   = round(spy_ret, 2)
                row[f"RSP_{label}"]   = round(rsp_ret, 2)
                row[f"alpha_{label}"] = round(rsp_ret - spy_ret, 2)
            else:
                row[f"SPY_{label}"]   = np.nan
                row[f"RSP_{label}"]   = np.nan
                row[f"alpha_{label}"] = np.nan

        rows.append(row)

    return pd.DataFrame(rows).set_index("entry_date")


# ── Summary stats ─────────────────────────────────────────────────────────────

def summarize(fwd: pd.DataFrame) -> None:
    print("\nForward Return Summary (signal dates only)")
    print("=" * 58)
    print(f"{'Horizon':<10} {'SPY avg':>10} {'RSP avg':>10} {'Alpha avg':>12} {'Win%':>8}")
    print("-" * 58)

    for h in HORIZONS:
        label = HORIZON_LABELS[h]
        spy_col   = f"SPY_{label}"
        rsp_col   = f"RSP_{label}"
        alpha_col = f"alpha_{label}"

        valid = fwd[[spy_col, rsp_col, alpha_col]].dropna()
        if valid.empty:
            print(f"{label:<10} {'–':>10} {'–':>10} {'–':>12} {'–':>8}")
            continue

        spy_avg   = valid[spy_col].mean()
        rsp_avg   = valid[rsp_col].mean()
        alpha_avg = valid[alpha_col].mean()
        win_pct   = (valid[alpha_col] > 0).mean() * 100

        print(f"{label:<10} {spy_avg:>9.1f}% {rsp_avg:>9.1f}% {alpha_avg:>11.1f}% {win_pct:>7.0f}%")

    print()
    print(f"  Total signals generated : {len(fwd)}")
    print(f"  Entry threshold         : Z-score ≤ {ENTRY_ZSCORE}")


# ── Run ───────────────────────────────────────────────────────────────────────

def run_signals():
    df = load_processed()

    signals = generate_signals(df)
    if signals.empty:
        print("No signals found with current threshold.")
        return

    print(f"\nSignals found: {len(signals)}")
    print(signals.head(10).to_string())

    fwd = compute_forward_returns(df, signals)

    # Save
    sig_path = os.path.join(PROCESSED_DIR, "signals.csv")
    fwd_path = os.path.join(PROCESSED_DIR, "forward_returns.csv")
    signals.to_csv(sig_path)
    fwd.to_csv(fwd_path)
    print(f"\nSignals      → {sig_path}")
    print(f"Fwd returns  → {fwd_path}")

    summarize(fwd)
    return fwd


if __name__ == "__main__":
    run_signals()
