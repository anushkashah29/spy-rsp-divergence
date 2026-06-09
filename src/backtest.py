"""
Phase 4 — Backtest
Simulates a long RSP / short SPY trade triggered by Z-score signals
and tracks the equity curve vs buy-and-hold SPY.

Usage:
    python src/backtest.py
"""

import os
import pandas as pd
import numpy as np

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
ENTRY_ZSCORE  = -2.0
EXIT_ZSCORE   =  0.0


def load_data():
    df  = pd.read_csv(os.path.join(PROCESSED_DIR, "ratio_zscore.csv"),
                      index_col="Date", parse_dates=True)
    return df


def run_backtest(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simple long-only RSP strategy:
      - Hold RSP when Z-score <= ENTRY_ZSCORE (extreme divergence)
      - Hold SPY otherwise (benchmark)
    Returns a DataFrame with daily strategy and benchmark equity curves.
    """
    df = df.copy().dropna(subset=["zscore"])

    # Daily returns
    df["spy_ret"] = df["SPY"].pct_change()
    df["rsp_ret"] = df["RSP"].pct_change()

    # Position: 1 = long RSP, 0 = hold SPY
    in_trade = False
    positions = []

    for z in df["zscore"]:
        if not in_trade and z <= ENTRY_ZSCORE:
            in_trade = True
        elif in_trade and z >= EXIT_ZSCORE:
            in_trade = False
        positions.append(1 if in_trade else 0)

    df["position"] = positions

    # Strategy return: RSP when in trade, SPY when not
    df["strat_ret"] = np.where(df["position"] == 1, df["rsp_ret"], df["spy_ret"])

    # Equity curves (start at 100)
    df["equity_strategy"]  = (1 + df["strat_ret"]).cumprod() * 100
    df["equity_spy"]       = (1 + df["spy_ret"]).cumprod() * 100
    df["equity_rsp"]       = (1 + df["rsp_ret"]).cumprod() * 100

    return df


def performance_stats(df: pd.DataFrame) -> dict:
    """Compute annualized return, volatility, Sharpe, and max drawdown."""

    def stats(col_ret):
        r = df[col_ret].dropna()
        ann_ret  = (1 + r.mean()) ** 252 - 1
        ann_vol  = r.std() * np.sqrt(252)
        sharpe   = ann_ret / ann_vol if ann_vol > 0 else np.nan
        cum      = (1 + r).cumprod()
        roll_max = cum.cummax()
        drawdown = (cum - roll_max) / roll_max
        max_dd   = drawdown.min()
        return {
            "ann_return": round(ann_ret * 100, 2),
            "ann_vol":    round(ann_vol * 100, 2),
            "sharpe":     round(sharpe, 3),
            "max_dd":     round(max_dd * 100, 2),
        }

    results = {
        "Strategy (RSP on signal / SPY otherwise)": stats("strat_ret"),
        "Buy & Hold SPY":                            stats("spy_ret"),
        "Buy & Hold RSP":                            stats("rsp_ret"),
    }
    return results


def print_stats(stats: dict) -> None:
    print("\nBacktest Performance Summary")
    print("=" * 62)
    print(f"{'Strategy':<42} {'Ann Ret':>8} {'Vol':>6} {'Sharpe':>8} {'Max DD':>8}")
    print("-" * 62)
    for name, s in stats.items():
        print(f"{name:<42} {s['ann_return']:>7}% {s['ann_vol']:>5}% "
              f"{s['sharpe']:>8} {s['max_dd']:>7}%")


def run():
    df = load_data()
    bt = run_backtest(df)

    # Save
    out = os.path.join(PROCESSED_DIR, "backtest.csv")
    bt[["SPY", "RSP", "zscore", "position",
        "strat_ret", "equity_strategy", "equity_spy", "equity_rsp"]].to_csv(out)
    print(f"Backtest results → {out}")

    stats = performance_stats(bt)
    print_stats(stats)

    # Days in trade
    in_trade_days = bt["position"].sum()
    total_days    = len(bt)
    print(f"\n  Days in RSP trade : {in_trade_days} / {total_days} "
          f"({in_trade_days/total_days*100:.1f}% of time)")

    return bt


if __name__ == "__main__":
    run()
