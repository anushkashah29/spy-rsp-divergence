"""
Phase 5 — Visualization
Generates all project charts and saves them to outputs/.

Usage:
    python src/visualize.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
OUTPUT_DIR    = os.path.join(os.path.dirname(__file__), "..", "outputs")
STYLE = {
    "spy_color":      "#2563EB",   # blue
    "rsp_color":      "#16A34A",   # green
    "signal_color":   "#DC2626",   # red
    "neutral_color":  "#9CA3AF",   # gray
    "shade_color":    "#FEF9C3",   # light yellow for signal shading
    "fig_bg":         "#FAFAFA",
    "ax_bg":          "#FFFFFF",
    "grid_color":     "#E5E7EB",
    "text_color":     "#111827",
    "font":           "DejaVu Sans",
}
plt.rcParams.update({
    "font.family":       STYLE["font"],
    "text.color":        STYLE["text_color"],
    "axes.labelcolor":   STYLE["text_color"],
    "xtick.color":       STYLE["text_color"],
    "ytick.color":       STYLE["text_color"],
    "axes.facecolor":    STYLE["ax_bg"],
    "figure.facecolor":  STYLE["fig_bg"],
})


def _save(fig, name: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved → {path}")
    return path


def load_all():
    def read(fname):
        return pd.read_csv(
            os.path.join(PROCESSED_DIR, fname),
            index_col="Date", parse_dates=True
        )
    rz  = read("ratio_zscore.csv")
    bt  = read("backtest.csv")
    fwd_path = os.path.join(PROCESSED_DIR, "forward_returns.csv")
    fwd = pd.read_csv(fwd_path, index_col="entry_date", parse_dates=True) \
          if os.path.exists(fwd_path) else pd.DataFrame()
    return rz, bt, fwd


# ── Chart 1: Normalized performance ──────────────────────────────────────────

def chart_performance(rz: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(rz.index, rz["SPY_idx"], color=STYLE["spy_color"],
            linewidth=1.8, label="SPY (cap-weighted)")
    ax.plot(rz.index, rz["RSP_idx"], color=STYLE["rsp_color"],
            linewidth=1.8, label="RSP (equal-weighted)")

    ax.set_title("SPY vs RSP — Normalized Performance (Base 100)", fontsize=14, pad=12)
    ax.set_ylabel("Index level (base = 100)")
    ax.legend(loc="upper left")
    ax.grid(True, color=STYLE["grid_color"], linewidth=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.tight_layout()
    _save(fig, "01_normalized_performance.png")


# ── Chart 2: RSP/SPY ratio with Z-score thresholds ───────────────────────────

def chart_ratio_zscore(rz: pd.DataFrame) -> None:
    fig = plt.figure(figsize=(12, 8))
    gs  = gridspec.GridSpec(2, 1, height_ratios=[1.6, 1], hspace=0.08)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)

    # Top: ratio
    ax1.plot(rz.index, rz["ratio"], color="#7C3AED", linewidth=1.5,
             label="RSP/SPY ratio (normalized)")
    ax1.axhline(1.0, color=STYLE["neutral_color"], linewidth=0.8, linestyle="--")
    ax1.fill_between(rz.index, rz["ratio"], 1.0,
                     where=rz["ratio"] < 1.0,
                     color=STYLE["signal_color"], alpha=0.08,
                     label="RSP underperforming")
    ax1.set_ylabel("Ratio (RSP / SPY normalized)")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, color=STYLE["grid_color"], linewidth=0.5)
    ax1.set_title("RSP/SPY Ratio & Z-Score — Divergence Analysis", fontsize=14, pad=12)
    plt.setp(ax1.get_xticklabels(), visible=False)

    # Bottom: Z-score with thresholds
    ax2.plot(rz.index, rz["zscore"], color="#7C3AED", linewidth=1.2, label="Z-score")
    ax2.axhline(0,    color=STYLE["neutral_color"], linewidth=0.8, linestyle="--")
    ax2.axhline(-2.0, color=STYLE["signal_color"],  linewidth=1.2, linestyle="--",
                label="Z = −2 (buy RSP signal)")
    ax2.axhline( 2.0, color=STYLE["spy_color"],     linewidth=1.2, linestyle="--",
                label="Z = +2 (sell RSP signal)")
    ax2.fill_between(rz.index, rz["zscore"], -2,
                     where=rz["zscore"] <= -2,
                     color=STYLE["signal_color"], alpha=0.25)
    ax2.set_ylabel("Z-score (252-day rolling)")
    ax2.set_ylim(-4.5, 4.5)
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(True, color=STYLE["grid_color"], linewidth=0.5)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    fig.tight_layout()
    _save(fig, "02_ratio_zscore.png")


# ── Chart 3: Backtest equity curves ──────────────────────────────────────────

def chart_backtest(bt: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(bt.index, bt["equity_strategy"], color="#7C3AED",
            linewidth=2, label="Strategy (RSP on signal / SPY otherwise)")
    ax.plot(bt.index, bt["equity_spy"], color=STYLE["spy_color"],
            linewidth=1.5, linestyle="--", label="Buy & hold SPY", alpha=0.8)
    ax.plot(bt.index, bt["equity_rsp"], color=STYLE["rsp_color"],
            linewidth=1.5, linestyle=":", label="Buy & hold RSP", alpha=0.8)

    # Shade periods in RSP trade
    in_trade = bt["position"] == 1
    ax.fill_between(bt.index, bt["equity_strategy"].min(),
                    bt["equity_strategy"].max(),
                    where=in_trade, alpha=0.07,
                    color=STYLE["rsp_color"], label="In RSP trade")

    ax.set_title("Backtest Equity Curves — Z-Score Mean Reversion Strategy", fontsize=14, pad=12)
    ax.set_ylabel("Portfolio value (start = 100)")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, color=STYLE["grid_color"], linewidth=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.tight_layout()
    _save(fig, "03_backtest_equity.png")


# ── Chart 4: Forward returns bar chart ───────────────────────────────────────

def chart_forward_returns(fwd: pd.DataFrame) -> None:
    if fwd.empty:
        print("  Skipping forward returns chart — no signal data.")
        return

    horizons = ["6m", "12m", "24m"]
    spy_means, rsp_means = [], []

    for h in horizons:
        sc, rc = f"SPY_{h}", f"RSP_{h}"
        if sc in fwd.columns and rc in fwd.columns:
            spy_means.append(fwd[sc].dropna().mean())
            rsp_means.append(fwd[rc].dropna().mean())
        else:
            spy_means.append(np.nan)
            rsp_means.append(np.nan)

    x    = np.arange(len(horizons))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    bars_spy = ax.bar(x - width/2, spy_means, width,
                      color=STYLE["spy_color"], alpha=0.85, label="SPY avg return")
    bars_rsp = ax.bar(x + width/2, rsp_means, width,
                      color=STYLE["rsp_color"], alpha=0.85, label="RSP avg return")

    for bar in list(bars_spy) + list(bars_rsp):
        h = bar.get_height()
        if not np.isnan(h):
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.5,
                    f"{h:.1f}%", ha="center", va="bottom", fontsize=9)

    ax.set_title("Avg Forward Returns After Z-Score ≤ −2 Signal", fontsize=14, pad=12)
    ax.set_ylabel("Average return (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(["6 months", "12 months", "24 months"])
    ax.legend()
    ax.grid(True, axis="y", color=STYLE["grid_color"], linewidth=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    _save(fig, "04_forward_returns.png")


# ── Run all ───────────────────────────────────────────────────────────────────

def run_all():
    print("\nGenerating charts...")
    rz, bt, fwd = load_all()
    chart_performance(rz)
    chart_ratio_zscore(rz)
    chart_backtest(bt)
    chart_forward_returns(fwd)
    print(f"\nAll charts saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    run_all()
