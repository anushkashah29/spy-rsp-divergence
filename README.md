# SPY vs RSP: Divergence & Mean-Reversion Analysis

A quantitative project analyzing the performance gap between the cap-weighted S&P 500 (SPY) and the equal-weighted S&P 500 (RSP) from 2007 to present, testing whether extreme divergences between the two indexes mean-revert over time.

---

## Background

The S&P 500 can be tracked two ways:

- **Cap-weighted (SPY):** Each stock's weight is proportional to its market cap. The largest companies — Apple, Microsoft, Nvidia — dominate returns. This acts as a momentum strategy, letting winners ride.
- **Equal-weighted (RSP):** Every stock gets the same weight (~0.2%), regardless of size. RSP rebalances quarterly, trimming winners and buying laggards, approximating the return of the "average" stock.

When a handful of mega-caps drive returns, SPY pulls ahead of RSP. The central question of this project: **when that gap reaches a statistical extreme, does it revert?**

---

## Hypothesis

> When the performance gap between SPY and RSP reaches a statistically extreme level (Z-score ≤ -2.0, indicating SPY is far ahead of RSP), the divergence will mean-revert and RSP will outperform going forward.

---

## Methodology

### Data
- **Tickers:** SPY (cap-weighted benchmark), RSP (equal-weighted benchmark)
- **Source:** Yahoo Finance via `yfinance`
- **Period:** January 2007 – present (~4,900 trading days)

### Steps

**1. Relative Performance Ratio**

Computed the daily ratio `RSP / SPY` to track which index is outperforming over time. Values below the historical mean indicate SPY dominance.

**2. Log Spread & Rolling Z-Score**

Calculated the log spread `log(RSP) - log(SPY)` and applied a 252-day (1-year) rolling Z-score:

```
Z = (Spread - Rolling Mean) / Rolling Std
```

A Z-score ≤ -2.0 flags a statistically extreme episode of SPY dominance — the entry signal for the hypothesis test.

**3. Engle-Granger Cointegration Test**

Tested whether SPY and RSP are cointegrated (i.e., bound by a long-run equilibrium that divergences must revert to). Run two ways:
- Full-period test (2007–present)
- Rolling 3-year window test (monthly steps) to detect regime changes

**4. Forward Return Analysis**

For every day the Z-score crossed below -2.0 (515 trading days total), measured the forward returns of SPY and RSP at 6-month, 12-month, and 24-month horizons. The RSP Edge (RSP return minus SPY return) is the primary metric — a positive edge confirms mean-reversion.

**5. Regime Analysis**

Grouped all signal days into six historical regimes to test whether mean-reversion is uniform or regime-dependent.

---

## Results

### Cointegration

| Test | Result |
|---|---|
| Full-period Engle-Granger (2007–2026) | p = 0.77 ⚠️ Not cointegrated |
| Rolling 3-year windows | Cointegrated in only 9.6% of windows |

The full-period cointegration test fails, meaning there is no single stable long-run equilibrium between SPY and RSP across the entire 19-year period. The rolling test reveals why — the relationship switches on and off across market regimes rather than holding consistently. This is an important caveat: mean-reversion cannot be characterized as a statistical law, only as a tendency.

### Z-Score Signal Summary

- **SPY-dominant days (Z ≤ -2.0):** 515
- **RSP-dominant days (Z ≥ +2.0):** 152
- **Current Z-score:** -0.28 (SPY modestly ahead, no extreme signal)

The asymmetry — 515 SPY-dominant days vs 152 RSP-dominant days — reflects the structural mega-cap concentration of the post-2017 market.

### Forward Returns by Regime

| Regime | Days | RSP Edge 6M | RSP Edge 12M | RSP Edge 24M |
|---|---|---|---|---|
| GFC Recovery (≤2010) | 60 | +8.7% | +13.8% | +25.4% |
| Post-Crisis Broadening (2011–2013) | 32 | +3.2% | +4.1% | +9.0% |
| Mega-Cap Buildup (2014–2018) | 200 | +0.4% | -0.3% | -5.6% |
| COVID Crash/Recovery (2019–2020) | 98 | -2.9% | +4.0% | +5.6% |
| AI Concentration (2021–2023) | 31 | -3.7% | -9.7% | -15.8% |
| Recent (2024–present) | 94 | +0.9% | -2.5% | -12.1% |
| **OVERALL** | **515** | **+0.7%** | **+2.0%** | **+1.7%** |

---

## Conclusion

The hypothesis is supported on average — RSP outperformed SPY by +2.0% at 12 months and +1.7% at 24 months across all 515 signal days. However, the regime table reveals that this average masks fundamentally different outcomes across market environments.

**Mean-reversion was strong after dislocations.** Following the GFC, RSP outperformed SPY by +13.8% at 12 months and +25.4% at 24 months. Following the COVID crash, the edge was +4.0% at 12 months and +5.6% at 24 months. In both cases, an acute market shock created temporary distortions that quickly unwound.

**Mean-reversion failed during structural concentration.** During the Mega-Cap Buildup regime (2014–2018), 200 signal days produced a -5.6% RSP edge at 24 months — SPY dominance persisted despite the Z-score signal. The AI Concentration regime (2021–2023) was worse, producing a -15.8% RSP edge at 24 months, the worst outcome in the dataset.

**The Z-score alone is insufficient as a trading signal.** The critical distinction is between *dislocation-driven* divergences, where mega-cap outperformance reflects temporary risk-off behavior, and *structural-driven* divergences, where mega-cap outperformance reflects genuine and sustained earnings superiority (e.g., AI-driven revenue growth at Nvidia, Microsoft, Meta). A Z-score of -2.0 looks identical in both cases, but the forward outcomes are opposite.

A more robust framework would pair the Z-score signal with a regime-detection indicator — such as market breadth (the percentage of stocks outperforming the index), sector rotation trends, or Fed policy stance — to distinguish dislocations from structural shifts before acting on the divergence.

> *Extreme divergences between SPY and RSP do mean-revert on average, but the signal is regime-dependent rather than unconditional. The Z-score captures the magnitude of divergence but not its cause — and cause is everything.*

---

## Caveats

- **Cointegration is weak over the full period.** The statistical foundation for guaranteed mean-reversion does not hold across the entire 2007–2026 dataset. Results should be interpreted as empirical tendencies, not laws.
- **Overlapping observations.** The 515 signal days are not independent — many belong to the same sustained episode (e.g., 60 consecutive days during the GFC). The regime table partially addresses this by grouping by period, but averages are still influenced by the duration of each episode.
- **Survivorship and look-ahead bias.** Regime labels were assigned with the benefit of hindsight. In real time, identifying whether a divergence is dislocation-driven or structural is non-trivial.
- **Transaction costs excluded.** RSP rebalances quarterly, incurring higher turnover and transaction costs than SPY. A live strategy would need to account for this drag on the RSP edge.
- **Recent data is incomplete.** Signal days from 2024–2025 do not yet have full 12M and 24M forward return data, making the "Recent" regime preliminary.

---

## Files

| File | Description |
|---|---|
| `spy_rsp_analysis.py` | Main analysis script |
| `spy_rsp_analysis.png` | 5-panel chart output |
| `spy_rsp_episodes.csv` | Full episode-level forward return data |
| `README.md` | This file |

---

## Requirements

```
yfinance
pandas
numpy
matplotlib
statsmodels
```

Install with:

```bash
pip install yfinance pandas numpy matplotlib statsmodels
```

Run with:

```bash
python spy_rsp_analysis.py
```
