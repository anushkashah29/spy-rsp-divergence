"""
SPY vs RSP: Divergence & Mean-Reversion Analysis
=================================================
Analyzes the performance gap between the cap-weighted S&P 500 (SPY)
and the equal-weighted S&P 500 (RSP) using:
  1. Relative performance ratio
  2. Rolling Z-score of the spread
  3. Full-period + rolling cointegration test
  4. Forward returns after SPY-dominant episodes
  5. Summary chart with all findings

Run:  pip install yfinance pandas numpy matplotlib statsmodels
      python spy_rsp_analysis.py
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from statsmodels.tsa.stattools import coint
import warnings

warnings.filterwarnings("ignore")

# ── Config ───────────────────────────────────────────────────────────────────
TICKERS     = ["SPY", "RSP"]
START_DATE  = "2007-01-01"
ZSCORE_WIN  = 252    # rolling window for Z-score (~1 trading year)
COINT_WIN   = 756    # rolling cointegration window (~3 years)
EXTREME_Z   = 2.0    # threshold for "statistically extreme"
OUTPUT_FILE = "spy_rsp_analysis.png"

# ── 1. Fetch Data ─────────────────────────────────────────────────────────────
print("Fetching data from yfinance …")
raw = yf.download(TICKERS, start=START_DATE, auto_adjust=True, progress=False)["Close"]
raw.columns = ["RSP", "SPY"]
prices = raw.dropna()

print(f"  Data range  : {prices.index[0].date()} → {prices.index[-1].date()}")
print(f"  Trading days: {len(prices)}\n")

# ── 2. Ratio & Log Spread ─────────────────────────────────────────────────────
prices["Ratio"]   = prices["RSP"] / prices["SPY"]
prices["Log_SPY"] = np.log(prices["SPY"])
prices["Log_RSP"] = np.log(prices["RSP"])
prices["Spread"]  = prices["Log_RSP"] - prices["Log_SPY"]

# ── 3. Rolling Z-Score ────────────────────────────────────────────────────────
roll_mean = prices["Spread"].rolling(ZSCORE_WIN).mean()
roll_std  = prices["Spread"].rolling(ZSCORE_WIN).std()
prices["ZScore"] = (prices["Spread"] - roll_mean) / roll_std

current_z = prices["ZScore"].iloc[-1]
print(f"Current Z-score : {current_z:+.2f}  "
      f"({'RSP extended above SPY' if current_z > 0 else 'SPY extended above RSP'})")
if abs(current_z) >= EXTREME_Z:
    print(f"  ⚡ Beyond ±{EXTREME_Z} → historically ripe for mean-reversion\n")
else:
    print(f"  Within ±{EXTREME_Z} → no extreme divergence signal currently\n")

# ── 4. Full-period Engle-Granger ──────────────────────────────────────────────
score, p_value, _ = coint(prices["Log_SPY"], prices["Log_RSP"])
print("Engle-Granger cointegration test (full period)")
print(f"  Test statistic : {score:.4f}")
print(f"  p-value        : {p_value:.4f}")
if p_value < 0.05:
    print("  ✅ Cointegrated (p < 0.05) — long-run relationship confirmed\n")
else:
    print("  ⚠️  Not cointegrated at 5% — see rolling test below\n")

# ── 5. Rolling Cointegration (3-year window, monthly steps) ──────────────────
print(f"Computing rolling cointegration ({COINT_WIN}-day window) …")
roll_p, roll_dates = [], []
for i in range(COINT_WIN, len(prices), 21):  # step every 21 days (~monthly)
    window = prices.iloc[i - COINT_WIN:i]
    _, p, _ = coint(window["Log_SPY"], window["Log_RSP"])
    roll_p.append(p)
    roll_dates.append(prices.index[i])

roll_coint = pd.Series(roll_p, index=roll_dates)
pct_cointegrated = (roll_coint < 0.05).mean() * 100
print(f"  Cointegrated in {pct_cointegrated:.1f}% of 3-year windows\n")

# ── 6. Extreme Divergence Episodes ───────────────────────────────────────────
extreme_low  = prices[prices["ZScore"] <= -EXTREME_Z]
extreme_high = prices[prices["ZScore"] >=  EXTREME_Z]
print(f"Extreme divergence episodes (|Z| ≥ {EXTREME_Z})")
print(f"  SPY dominant  (Z ≤ -{EXTREME_Z}): {len(extreme_low):>4d} days")
print(f"  RSP dominant  (Z ≥ +{EXTREME_Z}): {len(extreme_high):>4d} days\n")

# ── 7. Chart (5 panels) ───────────────────────────────────────────────────────
print("Rendering chart …")

FG    = "#0f1117"
PANEL = "#1a1d27"
SPY_C = "#4f8ef7"
RSP_C = "#f7c948"
WARN  = "#ff5c5c"
NEUT  = "#8892a4"
GREEN = "#4fc97e"

fig = plt.figure(figsize=(16, 15), facecolor=FG)
fig.suptitle(
    "S&P 500  Cap-Weighted vs Equal-Weighted  ·  Divergence & Mean-Reversion Analysis",
    color="white", fontsize=14, fontweight="bold", y=0.99
)

axes = fig.subplots(5, 1, sharex=True,
                    gridspec_kw={"hspace": 0.08,
                                 "height_ratios": [2, 1.5, 1.5, 1.5, 0.8]})

for ax in axes:
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=NEUT, labelsize=8)
    ax.yaxis.label.set_color(NEUT)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2e3242")

def panel_label(ax, text):
    ax.text(0.01, 0.95, text, transform=ax.transAxes,
            color="white", fontsize=9, fontweight="bold", va="top")

# Panel 1 — Indexed price levels
ax = axes[0]
spy_idx = prices["SPY"] / prices["SPY"].iloc[0] * 100
rsp_idx = prices["RSP"] / prices["RSP"].iloc[0] * 100
ax.plot(prices.index, spy_idx, color=SPY_C, lw=1.5, label="SPY (cap-weighted)")
ax.plot(prices.index, rsp_idx, color=RSP_C, lw=1.5, label="RSP (equal-weighted)")
ax.set_ylabel("Indexed (base = 100)")
ax.legend(fontsize=8, facecolor=PANEL, edgecolor=NEUT, labelcolor="white", loc="upper left")
panel_label(ax, "① Indexed Total Return (base = 100 at start)")
ax.grid(axis="y", color="#2e3242", lw=0.5)

# Panel 2 — RSP/SPY ratio
ax = axes[1]
ratio_mean = prices["Ratio"].mean()
ax.plot(prices.index, prices["Ratio"], color=RSP_C, lw=1.2)
ax.axhline(ratio_mean, color=NEUT, lw=0.8, ls="--", label=f"Mean ratio {ratio_mean:.3f}")
ax.fill_between(prices.index, prices["Ratio"], ratio_mean,
                where=(prices["Ratio"] < ratio_mean), color=WARN, alpha=0.15)
ax.set_ylabel("RSP / SPY")
ax.legend(fontsize=8, facecolor=PANEL, edgecolor=NEUT, labelcolor="white")
panel_label(ax, "② RSP÷SPY Ratio  (below mean = SPY dominance)")
ax.grid(axis="y", color="#2e3242", lw=0.5)

# Panel 3 — Rolling Z-score
ax = axes[2]
ax.axhline(0,          color=NEUT, lw=0.8, ls="--")
ax.axhline( EXTREME_Z, color=WARN, lw=0.8, ls=":", label=f"±{EXTREME_Z}σ threshold")
ax.axhline(-EXTREME_Z, color=WARN, lw=0.8, ls=":")
ax.fill_between(prices.index, prices["ZScore"],  EXTREME_Z,
                where=(prices["ZScore"] >=  EXTREME_Z), color=RSP_C, alpha=0.25)
ax.fill_between(prices.index, prices["ZScore"], -EXTREME_Z,
                where=(prices["ZScore"] <= -EXTREME_Z), color=WARN, alpha=0.25)
ax.plot(prices.index, prices["ZScore"], color="white", lw=1.0)
ax.axhline(current_z, color=GREEN, lw=1, ls="-.",
           label=f"Current Z = {current_z:+.2f}")
ax.set_ylabel(f"Z-score ({ZSCORE_WIN}d window)")
ax.legend(fontsize=8, facecolor=PANEL, edgecolor=NEUT, labelcolor="white")
panel_label(ax, "③ Rolling Z-Score of Log Spread  (Z ≤ -2 → extreme SPY dominance)")
ax.grid(axis="y", color="#2e3242", lw=0.5)

# Panel 4 — Rolling cointegration p-value
ax = axes[3]
ax.plot(roll_coint.index, roll_coint.values, color=SPY_C, lw=1.0)
ax.axhline(0.05, color=WARN, lw=0.8, ls="--", label="5% significance threshold")
ax.fill_between(roll_coint.index, roll_coint.values, 0.05,
                where=(roll_coint.values < 0.05), color=GREEN, alpha=0.2,
                label=f"Cointegrated ({pct_cointegrated:.0f}% of windows)")
ax.fill_between(roll_coint.index, roll_coint.values, 0.05,
                where=(roll_coint.values >= 0.05), color=WARN, alpha=0.1,
                label="Not cointegrated")
ax.set_ylabel("p-value")
ax.set_ylim(0, 1)
ax.legend(fontsize=8, facecolor=PANEL, edgecolor=NEUT, labelcolor="white")
panel_label(ax, "④ Rolling 3yr Cointegration p-value  —  green = cointegrated at 5%")
ax.grid(axis="y", color="#2e3242", lw=0.5)

# Panel 5 — Summary stats
ax = axes[4]
ax.axis("off")
coint_str = (f"Full-period p = {p_value:.4f} ⚠️  |  "
             f"Rolling 3yr: cointegrated {pct_cointegrated:.1f}% of windows")
extreme_str = (f"SPY-dominant days (Z ≤ -{EXTREME_Z}): {len(extreme_low)}  |  "
               f"RSP-dominant days (Z ≥ +{EXTREME_Z}): {len(extreme_high)}  |  "
               f"Current Z: {current_z:+.2f}")
ax.text(0.5, 0.75, coint_str,   ha="center", va="center", color="white",
        fontsize=8, transform=ax.transAxes)
ax.text(0.5, 0.25, extreme_str, ha="center", va="center", color=NEUT,
        fontsize=8, transform=ax.transAxes)
panel_label(ax, "⑤ Summary Statistics")

axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
axes[-1].xaxis.set_major_locator(mdates.YearLocator())
plt.setp(axes[-1].xaxis.get_majorticklabels(), color=NEUT, fontsize=8)

fig.tight_layout(rect=[0, 0, 1, 0.98])
fig.savefig(OUTPUT_FILE, dpi=150, bbox_inches="tight", facecolor=FG)
print(f"Chart saved → {OUTPUT_FILE}")

# ── 8. Forward Returns After SPY-Dominant Extremes ───────────────────────────
print("\nForward returns after SPY-dominant extreme episodes (Z ≤ -2.0)\n")
print("Hypothesis: extreme SPY dominance mean-reverts → RSP outperforms after signal\n")

holding_periods = {"6M": 126, "12M": 252, "24M": 504}

spy_extreme    = prices["ZScore"] <= -EXTREME_Z
episode_starts = spy_extreme & ~spy_extreme.shift(1).fillna(False)
entry_dates    = prices.index[episode_starts].tolist()

rows = []
for entry in entry_dates:
    entry_idx = prices.index.get_loc(entry)
    row = {"Entry Date": entry.date()}
    for label, days in holding_periods.items():
        exit_idx = entry_idx + days
        if exit_idx < len(prices):
            spy_ret = (prices["SPY"].iloc[exit_idx] / prices["SPY"].iloc[entry_idx] - 1) * 100
            rsp_ret = (prices["RSP"].iloc[exit_idx] / prices["RSP"].iloc[entry_idx] - 1) * 100
            row[f"SPY {label}"] = f"{spy_ret:+.1f}%"
            row[f"RSP {label}"] = f"{rsp_ret:+.1f}%"
            row[f"RSP Edge {label}"] = f"{rsp_ret - spy_ret:+.1f}%"
        else:
            row[f"SPY {label}"] = "N/A"
            row[f"RSP {label}"] = "N/A"
            row[f"RSP Edge {label}"] = "N/A"
    rows.append(row)

results = pd.DataFrame(rows)

csv_path = "spy_rsp_episodes.csv"
results.to_csv(csv_path, index=False)
print(f"Full episode data exported → {csv_path}")

# ── Regime-grouped summary (clean output) ────────────────────────────────────
results["Year"] = pd.to_datetime(results["Entry Date"]).dt.year
results["Regime"] = results["Year"].apply(lambda y:
    "GFC Recovery"           if y <= 2010 else
    "Post-Crisis Broadening" if y <= 2013 else
    "Mega-Cap Buildup"       if y <= 2018 else
    "COVID Crash/Recovery"   if y <= 2020 else
    "AI Concentration"       if y <= 2023 else
    "Recent")

for label in ["6M", "12M", "24M"]:
    col = f"RSP Edge {label}"
    results[col] = pd.to_numeric(results[col].str.replace("%", ""), errors="coerce")

regime_order = ["GFC Recovery", "Post-Crisis Broadening", "Mega-Cap Buildup",
                "COVID Crash/Recovery", "AI Concentration", "Recent"]

print(f"{'Regime':<25} {'Days':>5}  {'RSP Edge 6M':>12}  {'RSP Edge 12M':>13}  {'RSP Edge 24M':>13}")
print("-" * 75)
for regime in regime_order:
    group = results[results["Regime"] == regime]
    if group.empty:
        continue
    e6  = group["RSP Edge 6M"].mean()
    e12 = group["RSP Edge 12M"].mean()
    e24 = group["RSP Edge 24M"].mean()
    print(f"{regime:<25} {len(group):>5}  {e6:>+11.1f}%  {e12:>+12.1f}%  {e24:>+12.1f}%")

print("-" * 75)
# Overall averages
avg_e6  = results["RSP Edge 6M"].mean()
avg_e12 = results["RSP Edge 12M"].mean()
avg_e24 = results["RSP Edge 24M"].mean()
print(f"{'OVERALL':<25} {len(results):>5}  {avg_e6:>+11.1f}%  {avg_e12:>+12.1f}%  {avg_e24:>+12.1f}%")

hypothesis_confirmed = avg_e6 > 0 and avg_e12 > 0 and avg_e24 > 0
print(f"\nHypothesis {'SUPPORTED ✅' if hypothesis_confirmed else 'PARTIALLY SUPPORTED / MIXED ⚠️'} "
      f"— after extreme SPY dominance (Z ≤ -2), RSP "
      f"{'outperformed across all horizons' if hypothesis_confirmed else 'showed mixed results across horizons'}")