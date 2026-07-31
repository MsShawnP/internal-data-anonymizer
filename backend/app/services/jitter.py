import numpy as np
import pandas as pd


def _is_blank(value) -> bool:
    """Null or empty/whitespace-only (read_file yields "" for blank cells)."""
    return pd.isna(value) or str(value).strip() == ""


# Date-fallback tuning: minimum share of non-blank values that must parse as
# dates for the column to be jittered as dates, and the per-value shift range.
_DATE_PARSE_MIN_RATE = 0.80
_DATE_SHIFT_MIN_DAYS = 1
_DATE_SHIFT_MAX_DAYS = 30


def apply_jitter(
    series: pd.Series,
    alpha: float = 0.05,
    clamp_range: bool = True,
    seed: int | None = None,
) -> tuple[pd.Series, dict]:
    """Apply rank-preserving jitter to a numeric series.

    Numeric columns get rank-preserving Gaussian noise (see below). Columns
    whose non-blank cells are all digit-strings (zip codes, quantities read
    from file as text) come back as zero-padded integer strings of each
    cell's original width -- never floats like "8079.0", and leading zeros
    survive.

    Date fallback: when the column has no numeric cells but at least 80% of
    its non-blank values parse as dates, each date is shifted by a seeded
    random +/- 1..30 days instead. Output values are normalized to ISO
    YYYY-MM-DD regardless of the input format (e.g. "03/15/2024" comes back
    as "2024-04-02"); any unparseable minority cells are blanked, never
    passed through.

    A column that is neither numeric nor date-parseable raises ValueError
    ("jitter unsupported for this column type; choose another strategy")
    instead of returning the original values -- jitter must never leak real
    data. All-blank/all-null columns pass through unchanged.

    Returns the jittered series and histogram data for before/after comparison.
    """
    coerced = pd.to_numeric(series, errors="coerce")
    numeric_mask = coerced.notna()
    non_null = coerced[numeric_mask]

    if len(non_null) == 0:
        return _jitter_non_numeric(series, seed)

    if non_null.nunique() <= 1:
        return series.copy(), _compute_histograms(non_null, non_null)

    rng = np.random.default_rng(seed)
    values = non_null.values.astype(float)
    original_ranks = np.argsort(np.argsort(values))

    std = np.std(values, ddof=1) if len(values) > 1 else 0.0
    noise = rng.normal(0, alpha * std, size=len(values)) if std > 0 else np.zeros(len(values))
    perturbed = values + noise

    # Rank-preserving: re-sort perturbed to match original rank order
    sorted_perturbed = np.sort(perturbed)
    rank_preserved = sorted_perturbed[original_ranks]

    # Post-hoc variance correction
    var_original = np.var(values, ddof=1)
    var_perturbed = np.var(rank_preserved, ddof=1)
    if var_perturbed > 0 and var_original > 0:
        correction = np.sqrt(var_original / var_perturbed)
        mean_val = np.mean(rank_preserved)
        rank_preserved = mean_val + (rank_preserved - mean_val) * correction

    # Clamp to original range
    if clamp_range:
        rank_preserved = np.clip(rank_preserved, values.min(), values.max())

    # Digit-string columns (zips, quantities — read_file yields str cells, so
    # is_integer_dtype never fires for them) must round-trip as integer
    # strings, not floats.
    non_blank_orig = series[~series.map(_is_blank)]
    all_digit_strings = len(non_blank_orig) > 0 and all(
        isinstance(v, str) and v.strip().isdigit() for v in non_blank_orig
    )

    # Match original precision (integer columns stay integer)
    if pd.api.types.is_integer_dtype(series.dropna()) or all_digit_strings:
        rank_preserved = np.round(rank_preserved).astype(int)
        # Resolve ties that rounding introduced — nudge duplicates to preserve rank
        rank_order = np.argsort(original_ranks)
        for j in range(1, len(rank_order)):
            curr, prev = rank_order[j], rank_order[j - 1]
            if rank_preserved[curr] <= rank_preserved[prev]:
                rank_preserved[curr] = rank_preserved[prev] + 1
    else:
        max_decimals = _detect_precision(non_null)
        rank_preserved = np.round(rank_preserved, max_decimals)

    # Object dtype makes the numeric write-back safe regardless of the input
    # series dtype (read_file yields str-typed columns).
    result = series.astype(object).copy()
    if all_digit_strings:
        # Write back zero-padded integer strings of each cell's original
        # width: "10001" jittered to 8079 exports as "08079", never "8079.0".
        widths = series[numeric_mask].astype(str).str.strip().str.len()
        result[numeric_mask] = [
            str(int(v)).zfill(int(w)) for v, w in zip(rank_preserved, widths)
        ]
    else:
        result[numeric_mask] = rank_preserved

    # A non-numeric, non-blank cell in a jitter column is dirty data that
    # to_numeric could not parse. Blank it rather than pass the original
    # through — jitter must never leak a real value. Genuine null/blank cells
    # are left as-is so the null structure is preserved.
    dirty_mask = (~numeric_mask) & series.map(lambda v: not _is_blank(v))
    if dirty_mask.any():
        result[dirty_mask] = ""

    histograms = _compute_histograms(
        pd.Series(values), pd.Series(rank_preserved)
    )
    return result, histograms


def _jitter_non_numeric(series: pd.Series, seed: int | None) -> tuple[pd.Series, dict]:
    """Jitter a column with no numeric cells: shift dates, or fail loud.

    Previously this path returned the series unchanged, which exported the
    original values verbatim — a leak for date columns the detector routes
    to the jitter strategy. Now:

    * All-blank/all-null column: returned unchanged (nothing to leak).
    * >= 80% of non-blank values parse as dates: every parseable date is
      shifted by a seeded random +/- 1..30 days (never 0, so no output equals
      its input) and written back as ISO ``YYYY-MM-DD`` — a deliberate format
      normalization: whatever the input spelling ("03/15/2024",
      "2024-03-15"), the output is ISO. Unparseable minority cells are
      blanked, mirroring the numeric dirty-cell rule.
    * Anything else: raise ValueError so the operator picks another strategy
      instead of the export silently leaking originals.
    """
    blank_mask = series.map(_is_blank)
    non_blank = series[~blank_mask]
    if len(non_blank) == 0:
        return series.copy(), _empty_histogram()

    parsed = pd.to_datetime(
        non_blank.astype(str).str.strip(), errors="coerce", format="mixed"
    )
    parse_rate = parsed.notna().sum() / len(non_blank)
    if parse_rate < _DATE_PARSE_MIN_RATE:
        raise ValueError(
            "jitter unsupported for this column type; choose another strategy"
        )

    rng = np.random.default_rng(seed)
    result = series.astype(object).copy()
    for idx, ts in parsed.items():
        if pd.isna(ts):
            # Unparseable non-blank cell in a date column: blank it rather
            # than leak the original.
            result.at[idx] = ""
            continue
        days = int(rng.integers(_DATE_SHIFT_MIN_DAYS, _DATE_SHIFT_MAX_DAYS + 1))
        sign = -1 if int(rng.integers(0, 2)) == 0 else 1
        shifted = ts + pd.Timedelta(days=sign * days)
        result.at[idx] = shifted.strftime("%Y-%m-%d")
    return result, _empty_histogram()


def _detect_precision(series: pd.Series) -> int:
    """Detect maximum decimal places in a numeric series."""
    max_dec = 0
    for val in series.head(50):
        s = f"{float(val):.10f}".rstrip("0")
        if "." in s:
            dec = len(s.split(".")[1])
            max_dec = max(max_dec, dec)
    return min(max_dec, 6)


def _compute_histograms(
    original: pd.Series, jittered: pd.Series, bins: int = 15
) -> dict:
    """Compute histogram bin data for before/after comparison."""
    all_values = pd.concat([original, jittered])
    bin_edges = np.linspace(all_values.min(), all_values.max(), bins + 1)

    orig_counts, _ = np.histogram(original, bins=bin_edges)
    jit_counts, _ = np.histogram(jittered, bins=bin_edges)

    return {
        "bin_edges": bin_edges.tolist(),
        "original_counts": orig_counts.tolist(),
        "jittered_counts": jit_counts.tolist(),
        "stats": {
            "original_mean": float(original.mean()),
            "original_std": float(original.std()),
            "jittered_mean": float(jittered.mean()),
            "jittered_std": float(jittered.std()),
            "null_rate": 0.0,
        },
    }


def _empty_histogram() -> dict:
    return {
        "bin_edges": [],
        "original_counts": [],
        "jittered_counts": [],
        "stats": {},
    }
