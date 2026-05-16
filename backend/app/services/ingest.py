from pathlib import Path

import pandas as pd


def read_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    readers = {
        ".csv": pd.read_csv,
        ".xlsx": lambda p: pd.read_excel(p, engine="openpyxl"),
        ".json": pd.read_json,
        ".parquet": pd.read_parquet,
    }
    reader = readers.get(suffix)
    if reader is None:
        raise ValueError(f"Unsupported file format: {suffix}")
    return reader(path)


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".json", ".parquet"}
