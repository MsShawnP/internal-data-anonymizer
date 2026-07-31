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


class TestJitterDirtyData:
    """A jitter column must never leak a non-numeric original value."""

    def test_non_numeric_cell_blanked_not_leaked(self):
        series = pd.Series(["10", "20", "30", "40", "SSN-123-45-6789"])
        result, _ = apply_jitter(series, seed=7)
        assert result.iloc[4] == ""  # dirty string blanked, not passed through
        assert "SSN-123-45-6789" not in list(result)
        # numeric cells still jittered to numbers
        assert all(isinstance(float(result.iloc[i]), float) for i in range(4))

    def test_str_dtype_series_does_not_crash(self):
        # read_file yields object/str columns; write-back must be dtype-safe.
        # Digit-string columns now come back as integer strings (never
        # "100.0"-style floats); a clamped boundary value may legitimately
        # round back to its original numeral.
        series = pd.Series(["100", "200", "300"], dtype="object")
        result, _ = apply_jitter(series, seed=7)
        assert len(result) == 3
        assert all(isinstance(result.iloc[i], str) and result.iloc[i].isdigit()
                   for i in range(3))

    def test_blank_cells_preserved_among_dirty(self):
        series = pd.Series(["10", "", "30", "junk", "50"])
        result, _ = apply_jitter(series, seed=7)
        assert result.iloc[1] == ""   # originally blank stays blank
        assert result.iloc[3] == ""   # dirty string blanked


class TestJitterDates:
    """Date columns routed to jitter must be shifted, never passed through."""

    def test_date_values_shifted_never_equal_input(self):
        series = pd.Series(
            ["2024-03-15", "2024-03-16", "03/20/2024", "2024-04-01", None, ""]
        )
        result, _ = apply_jitter(series, seed=42)
        import re
        for i in (0, 1, 2, 3):
            assert result.iloc[i] != series.iloc[i]
            assert re.match(r"^\d{4}-\d{2}-\d{2}$", result.iloc[i])
        assert pd.isna(result.iloc[4])  # null preserved
        assert result.iloc[5] == ""     # blank preserved

    def test_date_shift_bounded_1_to_30_days(self):
        series = pd.Series(
            ["2024-01-10", "2024-02-15", "2024-03-20", "2024-04-25", "2024-05-30"]
        )
        result, _ = apply_jitter(series, seed=7)
        for orig, jit in zip(series, result):
            delta = abs(
                (pd.Timestamp(jit) - pd.Timestamp(orig)).days
            )
            assert 1 <= delta <= 30

    def test_date_jitter_deterministic_with_seed(self):
        series = pd.Series(["2024-03-15", "2024-06-01", "2025-01-20"])
        r1, _ = apply_jitter(series, seed=123)
        r2, _ = apply_jitter(series, seed=123)
        pd.testing.assert_series_equal(r1, r2)

    def test_date_output_normalized_to_iso(self):
        # Non-ISO input format comes back as YYYY-MM-DD (documented behavior).
        series = pd.Series(["03/15/2024", "04/20/2024", "05/25/2024"])
        result, _ = apply_jitter(series, seed=9)
        import re
        for v in result:
            assert re.match(r"^\d{4}-\d{2}-\d{2}$", v)

    def test_unparseable_minority_blanked_not_leaked(self):
        # 5 of 6 non-blank values parse (83% >= 80%); the junk cell is blanked.
        series = pd.Series(
            ["2024-01-10", "2024-02-15", "2024-03-20", "2024-04-25",
             "2024-05-30", "not-a-date"]
        )
        result, _ = apply_jitter(series, seed=7)
        assert result.iloc[5] == ""
        assert "not-a-date" not in list(result)

    def test_text_column_raises_instead_of_leaking(self):
        series = pd.Series(["apple", "banana", "cherry", "dragonfruit"])
        with pytest.raises(ValueError, match="jitter unsupported"):
            apply_jitter(series, seed=42)

    def test_all_blank_column_passes_through(self):
        series = pd.Series(["", "", None])
        result, _ = apply_jitter(series, seed=42)
        assert result.iloc[0] == ""
        assert result.iloc[1] == ""
        assert pd.isna(result.iloc[2])


class TestJitterDigitStrings:
    """Digit-string columns (zips, quantities) round-trip as integer strings."""

    def test_zip_codes_keep_width_no_float_suffix(self):
        series = pd.Series(["90210", "10001", "02134", "60601", "30301"])
        result, _ = apply_jitter(series, seed=42)
        for v in result:
            assert isinstance(v, str)
            assert v.isdigit(), f"non-digit output: {v!r}"
            assert len(v) == 5, f"width changed: {v!r}"

    def test_leading_zero_width_preserved_when_value_shrinks(self):
        # min is 02134 so clamped values may drop below 10000; the output
        # must be zero-padded back to the original 5-character width.
        series = pd.Series(["02134", "10001", "20002", "30003", "40004"])
        result, _ = apply_jitter(series, alpha=0.2, seed=3)
        for v in result:
            assert isinstance(v, str) and v.isdigit() and len(v) == 5

    def test_quantity_strings_stay_integer_strings(self):
        series = pd.Series(["2", "1", "3", "5", "4", "9", "7", "6"])
        result, _ = apply_jitter(series, seed=42)
        for v in result:
            assert isinstance(v, str)
            assert v.isdigit()
            assert "." not in v


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
