# SPY vs RSP: Divergence & Mean Reversion Analysis

A quantitative finance project analyzing the performance gap between the
**S&P 500 market-cap weighted index (SPY)** and the **equal-weighted index (RSP)**,
testing the hypothesis that extreme divergences mean-revert over time.

---

## Hypothesis

When the RSP/SPY performance ratio falls to historical extremes (Z-score < −2),
the equal-weighted index subsequently outperforms the cap-weighted index over
6-, 12-, and 24-month horizons — a mean reversion trade.

---

## Setup

```bash
# 1. Clone / enter the project
cd spy_rsp_divergence

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download data (saves to data/raw/)
python src/download.py

# 5. Run full analysis
python src/analysis.py
python src/signals.py
python src/backtest.py

# 6. Open notebook
jupyter notebook notebooks/analysis.ipynb
```

---

## Key Results

| Trigger (RSP/SPY Z-score < −2) | SPY forward return | RSP forward return |
|---|---|---|
| 6 months later  | ~13%  | ~24%  |
| 12 months later | ~29%  | ~47%  |
| 24 months later | ~49%  | ~78%  |

*Historical figures from MAPsignals research (2007–2024).*

---

## Methodology

1. **Ratio**: `R_t = RSP_t / SPY_t` (normalized to 100 at start)
2. **Z-score**: `Z = (R_t - rolling_mean) / rolling_std` over 252-day window
3. **Cointegration**: Engle-Granger test confirms long-run relationship
4. **Signal**: Enter long RSP / short SPY when Z < −2; exit at Z > 0
5. **Breadth**: % of S&P 500 stocks above 200-day MA as confirming indicator

---

## Data Sources

- `SPY` — SPDR S&P 500 ETF (cap-weighted proxy)
- `RSP` — Invesco S&P 500 Equal Weight ETF
- `XLG` — Invesco S&P 500 Top 50 ETF (mega-cap proxy)
- All via `yfinance` (Yahoo Finance)
