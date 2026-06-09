"""
Unit tests for src/analysis.py and src/signals.py
Run with: python -m pytest tests/ -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import pandas as pd
import pytest

from analysis import compute_ratio
from signals import generate_signals, compute_forward_returns


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_prices(n=600, spy_drift=0.0003, rsp_drift=0.0001, seed=42):
    """Generate synthetic SPY and RSP price series."""
    rng  = np.random.default_rng(seed)
    dates = pd.bdate_range("2020-01-01", periods=n)
    spy  = 100 * np.cumprod(1 + rng.normal(spy_drift, 0.01, n))
    rsp  = 100 * np.cumprod(1 + rng.normal(rsp_drift, 0.01, n))
    return pd.DataFrame({"SPY": spy, "RSP": rsp}, index=dates)


# ── compute_ratio ─────────────────────────────────────────────────────────────

class TestComputeRatio:
    def test_output_columns(self):
        prices = make_prices()
        result = compute_ratio(prices)
        for col in ["ratio", "zscore", "SPY_idx", "RSP_idx", "ratio_raw", "maps_trigger"]:
            assert col in result.columns, f"Missing column: {col}"

    def test_spy_idx_starts_at_100(self):
        prices = make_prices()
        result = compute_ratio(prices)
        assert abs(result["SPY_idx"].iloc[0] - 100) < 1e-6

    def test_rsp_idx_starts_at_100(self):
        prices = make_prices()
        result = compute_ratio(prices)
        assert abs(result["RSP_idx"].iloc[0] - 100) < 1e-6

    def test_ratio_raw_is_rsp_over_spy(self):
        prices = make_prices()
        result = compute_ratio(prices)
        expected = prices["RSP"] / prices["SPY"]
        pd.testing.assert_series_equal(
            result["ratio_raw"].dropna(), expected.dropna(),
            check_names=False, rtol=1e-5
        )

    def test_zscore_has_nan_in_warmup(self):
        """Z-score should be NaN for the first ZSCORE_WINDOW rows."""
        prices = make_prices(n=600)
        result = compute_ratio(prices)
        # First 252 rows should all be NaN (rolling window warmup)
        assert result["zscore"].iloc[:252].isna().all()

    def test_zscore_roughly_standard_normal(self):
        """After warmup, Z-score should have mean ~0 and std ~1."""
        prices = make_prices(n=1000)
        result = compute_ratio(prices)
        z = result["zscore"].dropna()
        assert abs(z.mean()) < 0.5, f"Z-score mean too far from 0: {z.mean():.3f}"
        assert 0.5 < z.std() < 2.0, f"Z-score std unexpected: {z.std():.3f}"

    def test_maps_trigger_boolean(self):
        prices = make_prices()
        result = compute_ratio(prices)
        assert result["maps_trigger"].dtype == bool


# ── generate_signals ─────────────────────────────────────────────────────────

class TestGenerateSignals:
    def _df_with_forced_zscore(self):
        """Create a processed DataFrame with a known Z-score dip."""
        prices = make_prices(n=800)
        df = compute_ratio(prices)
        # Force a Z-score below -2 at row 400
        df.iloc[400, df.columns.get_loc("zscore")] = -2.5
        return df

    def test_signal_detected_at_dip(self):
        df = self._df_with_forced_zscore()
        signals = generate_signals(df)
        assert len(signals) >= 1

    def test_signals_have_required_columns(self):
        df = self._df_with_forced_zscore()
        signals = generate_signals(df)
        if not signals.empty:
            assert "entry_zscore" in signals.columns
            assert "entry_ratio"  in signals.columns

    def test_no_signals_above_threshold(self):
        prices = make_prices(n=600)
        df = compute_ratio(prices)
        # Override all Z-scores to 0 (no signal)
        df["zscore"] = 0.0
        signals = generate_signals(df)
        assert signals.empty


# ── compute_forward_returns ───────────────────────────────────────────────────

class TestForwardReturns:
    def test_forward_return_columns_present(self):
        prices = make_prices(n=800)
        df = compute_ratio(prices)
        df.iloc[300, df.columns.get_loc("zscore")] = -2.5
        signals = generate_signals(df)
        fwd = compute_forward_returns(df, signals)
        for col in ["SPY_6m", "RSP_6m", "alpha_6m"]:
            assert col in fwd.columns

    def test_alpha_equals_rsp_minus_spy(self):
        prices = make_prices(n=800)
        df = compute_ratio(prices)
        df.iloc[300, df.columns.get_loc("zscore")] = -2.5
        signals = generate_signals(df)
        fwd = compute_forward_returns(df, signals)
        valid = fwd.dropna(subset=["SPY_6m", "RSP_6m", "alpha_6m"])
        if not valid.empty:
            diff = (valid["RSP_6m"] - valid["SPY_6m"] - valid["alpha_6m"]).abs()
            assert (diff < 0.01).all(), "alpha != RSP - SPY"
