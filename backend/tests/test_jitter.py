import numpy as np
import pandas as pd
import pytest

from app.services.jitter import apply_jitter


class TestJitterBasic:
    def test_preserves_rank_order(self):
        series = pd.Series([10, 20, 30, 40, 50])
        result, _ = apply_jitter(series, alpha=0.05, seed=42)
        # Rank order must be preserved
        for i in range(len(result) - 1):
            assert result.iloc[i] <= result.iloc[i + 1]

    def test_deterministic_with_seed(self):
        series = pd.Series([100, 200, 300, 400, 500])
        r1, _ = apply_jitter(series, seed=123)
        r2, _ = apply_jitter(series, seed=123)
        pd.testing.assert_series_equal(r1, r2)

    def test_different_seeds_produce_different_output(self):
        series = pd.Series([100, 200, 300, 400, 500])
        r1, _ = apply_jitter(series, seed=1)
        r2, _ = apply_jitter(series, seed=2)
        assert not r1.equals(r2)

    def test_preserves_null_positions(self):
        series = pd.Series([10, None, 30, None, 50])
        result, _ = apply_jitter(series, seed=42)
        assert pd.isna(result.iloc[1])
        assert pd.isna(result.iloc[3])
        assert not pd.isna(result.iloc[0])
        assert not pd.isna(result.iloc[2])
        assert not pd.isna(result.iloc[4])

    def test_all_nulls_returns_unchanged(self):
        series = pd.Series([None, None, None], dtype="float64")
        result, hist = apply_jitter(series, seed=42)
        assert result.isna().all()

    def test_single_unique_value_unchanged(self):
        series = pd.Series([42, 42, 42, 42])
        result, _ = apply_jitter(series, seed=42)
        assert (result == 42).all()


class TestJitterStatistical:
    def test_preserves_approximate_mean(self):
        rng = np.random.default_rng(99)
        values = rng.normal(450, 120, size=200)
        series = pd.Series(values)
        result, hist = apply_jitter(series, alpha=0.05, seed=42)

        original_mean = series.mean()
        jittered_mean = result.mean()
        # Mean should be within 5% of original
        assert abs(jittered_mean - original_mean) / original_mean < 0.05

    def test_preserves_null_rate(self):
        rng = np.random.default_rng(99)
        values = list(rng.normal(450, 120, size=170)) + [None] * 30  # 15% null
        series = pd.Series(values)
        result, _ = apply_jitter(series, seed=42)

        original_null_rate = series.isna().mean()
        result_null_rate = result.isna().mean()
        assert abs(result_null_rate - original_null_rate) < 0.001  # Exact preservation

    def test_integer_column_stays_integer(self):
        series = pd.Series([100, 200, 300, 400, 500])
        result, _ = apply_jitter(series, seed=42)
        for val in result:
            assert float(val) == int(float(val))

    def test_clamp_to_original_range(self):
        series = pd.Series([10, 20, 30, 40, 50])
        result, _ = apply_jitter(series, alpha=0.2, clamp_range=True, seed=42)
        assert result.min() >= 10
        assert result.max() <= 50

    def test_negative_values_handled(self):
        series = pd.Series([-50, -20, 0, 20, 50])
        result, _ = apply_jitter(series, seed=42)
        # Should not error and should preserve rank
        for i in range(len(result) - 1):
            assert result.iloc[i] <= result.iloc[i + 1]


class TestHistogramOutput:
    def test_histogram_structure(self):
        series = pd.Series([10, 20, 30, 40, 50, 60, 70, 80])
        _, hist = apply_jitter(series, seed=42)
        assert "bin_edges" in hist
        assert "original_counts" in hist
        assert "jittered_counts" in hist
        assert "stats" in hist
        assert len(hist["bin_edges"]) == len(hist["original_counts"]) + 1

    def test_histogram_stats(self):
        series = pd.Series([10, 20, 30, 40, 50])
        _, hist = apply_jitter(series, seed=42)
        assert "original_mean" in hist["stats"]
        assert "jittered_mean" in hist["stats"]
