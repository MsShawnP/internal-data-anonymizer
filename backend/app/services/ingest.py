from pathlib import Path

import pandas as pd


def read_file(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    readers = {
        ".csv": lambda p, c: pd.read_csv(p, dtype=str, keep_default_na=False, usecols=c),
        ".xlsx": lambda p, c: pd.read_excel(p, engine="openpyxl", dtype=str, keep_default_na=False, usecols=c),
        ".json": lambda p, c: pd.read_json(p, dtype=str),
        ".parquet": lambda p, c: pd.read_parquet(p, columns=c),
    }
    reader = readers.get(suffix)
    if reader is None:
        raise ValueError(f"Unsupported file format: {suffix}")
    return reader(path, columns)


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".json", ".parquet"}
