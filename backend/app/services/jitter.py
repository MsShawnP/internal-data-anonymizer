import numpy as np
import pandas as pd


def apply_jitter(
    series: pd.Series,
    alpha: float = 0.05,
    clamp_range: bool = True,
    seed: int | None = None,
) -> tuple[pd.Series, dict]:
    """Apply rank-preserving jitter to a numeric series.

    Returns the jittered series and histogram data for before/after comparison.
    """
    numeric = pd.to_numeric(series, errors="coerce")
    null_mask = numeric.isna()
    non_null = numeric[~null_mask]

    if len(non_null) == 0:
        return series.copy(), _empty_histogram()

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

    # Match original precision (integer columns stay integer)
    if pd.api.types.is_integer_dtype(series.dropna()):
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

    result = series.copy()
    result[~null_mask] = rank_preserved

    histograms = _compute_histograms(
        pd.Series(values), pd.Series(rank_preserved)
    )
    return result, histograms


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
