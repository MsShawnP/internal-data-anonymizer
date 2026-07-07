from pathlib import Path

import pandas as pd

from .ingest import read_file


def apply_mappings(
    file_path: Path,
    column_mappings: dict[str, dict[str, str]],
    column_strategies: dict[str, str],
    jitter_results: dict[str, pd.Series] | None = None,
) -> pd.DataFrame:
    """Apply anonymization mappings to a dataframe.

    Args:
        file_path: Path to the original uploaded file.
        column_mappings: {column_name: {original: anonymized}} for generative columns.
        column_strategies: {column_name: strategy} for all columns.
        jitter_results: {column_name: jittered_series} for numeric columns.

    Returns:
        Anonymized DataFrame.
    """
    df = read_file(file_path)
    drop_cols = []

    for col in df.columns:
        strategy = column_strategies.get(col, "passthrough")

        if strategy == "drop":
            drop_cols.append(col)
        elif strategy == "passthrough":
            continue
        elif strategy == "jitter":
            if jitter_results and col in jitter_results:
                df[col] = jitter_results[col]
        elif strategy in ("fake", "format-preserve", "hash"):
            mapping = column_mappings.get(col, {})
            if mapping:
                df[col] = df[col].map(lambda v, m=mapping: m.get(str(v), v) if pd.notna(v) else v)

    if drop_cols:
        df = df.drop(columns=drop_cols)

    return df


def export_dataframe(df: pd.DataFrame, output_path: Path, fmt: str) -> Path:
    """Export a DataFrame to the specified format.

    Args:
        df: The anonymized DataFrame.
        output_path: Directory to save the file.
        fmt: Output format (csv, xlsx, json, parquet).

    Returns:
        Path to the exported file.
    """
    output_path.mkdir(parents=True, exist_ok=True)

    if fmt == "csv":
        path = output_path / "anonymized.csv"
        df.to_csv(path, index=False)
    elif fmt == "xlsx":
        path = output_path / "anonymized.xlsx"
        df.to_excel(path, index=False, engine="openpyxl")
    elif fmt == "json":
        path = output_path / "anonymized.json"
        df.to_json(path, orient="records", indent=2)
    elif fmt == "parquet":
        path = output_path / "anonymized.parquet"
        df.to_parquet(path, index=False)
    else:
        raise ValueError(f"Unsupported export format: {fmt}")

    return path
