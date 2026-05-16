import re
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    unique_count: int
    null_rate: float
    sample_values: list[str]
    suggested_strategy: str
    detected_type: str
    stats: dict = field(default_factory=dict)


THRESHOLD = 0.80

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_RE = re.compile(
    r"^[\+]?[(]?\d{1,3}[)]?[-\s.]\d{3}[-\s.]\d{4}$"
)
DATE_FORMATS = [
    r"^\d{4}-\d{2}-\d{2}",
    r"^\d{1,2}/\d{1,2}/\d{2,4}",
    r"^\d{1,2}-\d{1,2}-\d{2,4}",
]
SKU_RE = re.compile(r"^[A-Za-z]{1,5}[-_][A-Za-z0-9]{1,8}([-_][A-Za-z0-9]{1,5})?$")


def _is_upc_valid(code: str) -> bool:
    if not code.isdigit() or len(code) not in (12, 13):
        return False
    digits = [int(d) for d in code]
    check = digits[-1]
    if len(code) == 12:
        # UPC-A: positions 0,2,4... weight 3; positions 1,3,5... weight 1
        total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(digits[:-1]))
    else:
        # EAN-13: positions 0,2,4... weight 1; positions 1,3,5... weight 3
        total = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits[:-1]))
    return (10 - total % 10) % 10 == check


def _classify_column(series: pd.Series) -> tuple[str, str]:
    non_null = series.dropna().astype(str)
    non_null = non_null[non_null.str.strip() != ""]
    if len(non_null) == 0:
        return "empty", "passthrough"

    total = len(non_null)

    # Email check
    email_matches = non_null.apply(lambda v: bool(EMAIL_RE.match(v.strip()))).sum()
    if email_matches / total >= THRESHOLD:
        return "email", "fake"

    # Phone check
    phone_matches = non_null.apply(lambda v: bool(PHONE_RE.match(v.strip()))).sum()
    if phone_matches / total >= THRESHOLD:
        return "phone", "fake"

    # UPC/GTIN check (12 or 13 digit numbers with check digit validation)
    digit_only = non_null.apply(lambda v: v.strip().isdigit() and len(v.strip()) in (12, 13))
    if digit_only.sum() / total >= THRESHOLD:
        valid_checks = non_null.apply(lambda v: _is_upc_valid(v.strip())).sum()
        # If >10% pass check digit validation, it's likely UPC data (random 12-digit
        # numbers have only 10% chance of valid check digit)
        if valid_checks / total > 0.10:
            return "upc_gtin", "format-preserve"

    # Date check
    try:
        coerced = pd.to_datetime(non_null, errors="coerce", format="mixed")
        if coerced.notna().sum() / total >= THRESHOLD:
            return "date", "jitter"
    except Exception:
        pass

    # SKU check (mixed alphanumeric with delimiters)
    sku_matches = non_null.apply(lambda v: bool(SKU_RE.match(v.strip()))).sum()
    if sku_matches / total >= THRESHOLD:
        return "sku", "format-preserve"

    # Numeric check
    numeric_series = pd.to_numeric(non_null, errors="coerce")
    if numeric_series.notna().sum() / total >= THRESHOLD:
        return "numeric", "jitter"

    # Name-like check (no digits, mostly titlecase/words)
    name_pattern = re.compile(r"^[A-Za-z\s\.\'\-]+$")
    name_matches = non_null.apply(lambda v: bool(name_pattern.match(v.strip()))).sum()
    if name_matches / total >= THRESHOLD:
        return "name", "fake"

    return "generic_string", "hash"


def _infer_dtype(series: pd.Series, detected_type: str) -> str:
    if detected_type == "numeric":
        numeric = pd.to_numeric(series.dropna(), errors="coerce")
        if numeric.notna().any():
            if (numeric == numeric.astype(int)).all():
                return "int64"
            return "float64"
    if detected_type in ("date",):
        return "str"
    return "str"


def profile_columns(df: pd.DataFrame) -> list[ColumnProfile]:
    profiles = []
    for col in df.columns:
        series = df[col]
        non_null = series[series.astype(str).str.strip() != ""]
        detected_type, strategy = _classify_column(series)

        sample = non_null.head(5).astype(str).tolist() if len(non_null) > 0 else []

        stats = {}
        if detected_type == "numeric":
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()
            if len(numeric) > 0:
                stats = {
                    "mean": round(float(numeric.mean()), 2),
                    "std": round(float(numeric.std()), 2),
                    "min": float(numeric.min()),
                    "max": float(numeric.max()),
                }

        profiles.append(
            ColumnProfile(
                name=col,
                dtype=_infer_dtype(series, detected_type),
                unique_count=int(non_null.nunique()),
                null_rate=round(float(series.isna().mean()), 4),
                sample_values=sample,
                suggested_strategy=strategy,
                detected_type=detected_type,
                stats=stats,
            )
        )
    return profiles
