from pathlib import Path

import pandas as pd


def read_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    readers = {
        ".csv": lambda p: pd.read_csv(p, dtype=str, keep_default_na=False),
        ".xlsx": lambda p: pd.read_excel(p, engine="openpyxl", dtype=str, keep_default_na=False),
        ".json": lambda p: pd.read_json(p, dtype=str),
        ".parquet": pd.read_parquet,
    }
    reader = readers.get(suffix)
    if reader is None:
        raise ValueError(f"Unsupported file format: {suffix}")
    return reader(path)


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".json", ".parquet"}
