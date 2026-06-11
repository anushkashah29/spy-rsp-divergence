# SPY vs RSP: Divergence & Mean-Reversion Analysis

A quantitative project analyzing the performance gap between the cap-weighted S&P 500 (SPY) and the equal-weighted S&P 500 (RSP) from 2007 to present, testing whether extreme divergences between the two indexes mean-revert over time.

---

## Background

The S&P 500 can be tracked two ways:

- **Cap-weighted (SPY):** Each stock's weight is proportional to its market cap. The largest companies like Apple, Microsoft and Nvidia dominate returns. 
- **Equal-weighted (RSP):** Every stock gets the same weight (~0.2%), rebalancing quarterly to maintain equal exposure across all stocks. RSP approximates the return of the average stock in the index.

When a handful of mega-caps drive returns, SPY pulls ahead of RSP. The main question of this project is: **when that gap reaches a statistical extreme, does it mean-revert?**

---

## Hypothesis

> When the performance gap between SPY and RSP reaches a statistically extreme level (rolling Z-score ≤ -2.0, meaning SPY is far ahead of RSP), the divergence will mean-revert and RSP will outperform going forward.

---

## Methodology

### Data
- **Tickers:** SPY (cap-weighted benchmark), RSP (equal-weighted benchmark)
- **Source:** Yahoo Finance via `yfinance`
- **Period:** January 2007 – present (~4,900 trading days)

### Steps

**1. Relative Performance Ratio**

Computed the daily ratio `RSP / SPY` to track which index is outperforming over time. Values below the historical mean show SPY dominance.

**2. Log Spread & Rolling Z-Score**

Calculated the log spread `log(RSP) - log(SPY)` and applied a 252-day (1-year) rolling Z-score:

```
Z = (Spread - Rolling Mean) / Rolling Std
```

A Z-score ≤ -2.0 flags a statistically extreme episode of SPY dominance, which is the entry signal for the hypothesis test.

**3. Engle-Granger Cointegration Test**

Tested whether SPY and RSP are cointegrated (bound by a long-run equilibrium that divergences must revert to). Run two ways:
- Full-period test (2007–present)
- Rolling 3-year window test (monthly steps) to detect regime changes

**4. Forward Return Analysis**

For every day the Z-score crossed below -2.0 (515 trading days total), measured the forward returns of SPY and RSP at 6-month, 12-month, and 24-month horizons. The RSP Edge (RSP return minus SPY return) is the main metric. A positive edge confirms mean-reversion.

**5. Regime Analysis**

Grouped all signal days into six historical regimes to test whether mean-reversion is uniform or regime-dependent.

---

## Results

### Cointegration

| Test | Result |
|---|---|
| Full-period Engle-Granger (2007–2026) | p = 0.77 ⚠️ Not cointegrated |
| Rolling 3-year windows | Cointegrated in only 9.6% of windows |

The full-period cointegration test fails, meaning there is no single stable long-run equilibrium between SPY and RSP across the entire 19-year period. The rolling test reveals it's due to the relationship switching on and off across market regimes rather than holding consistently. 

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

The hypothesis is **supported on average.** RSP outperformed SPY by **+2.0% at 12 months** and **+1.7% at 24 months** across all 515 signal days. However, the regime table shows the outcome depended on why the divergence happened, not just how large it was.

**It worked best after market crashes.** After the 2008 financial crisis, RSP beat SPY by **+13.8% over the next year** and **+25.4% over two years.** After the COVID crash, RSP beat SPY by **+4.0% at 12 months.** In both cases, the market had sold off broadly, and when it recovered, smaller and mid-size stocks bounced back harder than the mega-caps.

**It failed when mega-caps were genuinely dominant.** Between 2014 and 2018, when tech stocks were steadily taking over the market, the signal fired 200 times and RSP still underperformed by **-5.6% over two years.** During the AI boom from 2021 to 2023, when Nvidia, Microsoft, and Meta were driving the entire market, RSP underperformed by **-15.8% over two years.** 

**The Z-score alone is not enough.** A Z-score of -2.0 looks identical whether SPY is ahead because of a temporary panic or because a handful of companies are earning extraordinary returns. Those two situations have opposite outcomes for RSP. To use this signal in practice, you need a second indicator such as market breadth, sector rotation trends, or Fed policy stance.

> *Extreme divergences between SPY and RSP do mean-revert on average, but the signal is regime-dependent, not unconditional. The Z-score only captures the magnitude of divergence.*

---

### Caveats

- **The statistical test for mean-reversion did not pass.** The Engle-Granger cointegration test failed (p = 0.77), and the rolling version found a stable relationship in only 9.6% of three-year windows. Mean-reversion is not a certianty.
- **The 515 signal days are not 515 independent events.** Many of the signal days are within the same episode (ex: 60 consecutive days during the GFC all count separately). The regime table helps groups these days, but the true sample size is smaller than it appears.
- **Trading costs are not included.** RSP rebalances every quarter to maintain equal weights, generating more transaction costs than SPY. A real strategy would earn somewhat less than the RSP Edge numbers suggest.
- **Recent results are incomplete.** Signal days from 2024 onward do not yet have full 12 and 24 month forward returns, so the Recent regime numbers will change as more data comes in.

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
