import json
from pathlib import Path

import pandas as pd


def _read_json(path: Path, columns: list[str] | None) -> pd.DataFrame:
    """Match the CSV/XLSX readers: string-typed, blank-preserving, column-scoped.

    pd.read_json can't do this directly — it infers "1" as numeric, and
    dtype=str corrupts JSON null into the literal "None" (which would wrongly
    blank a real "None" string). Parsing the records ourselves preserves each
    value's representation while turning only true nulls into "".
    """
    records = json.loads(path.read_text(encoding="utf-8"))
    df = pd.DataFrame(records)
    if columns is not None:
        df = df[columns]
    return df.map(lambda v: "" if pd.isna(v) else str(v))


def read_file(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    readers = {
        ".csv": lambda p, c: pd.read_csv(p, dtype=str, keep_default_na=False, usecols=c),
        ".xlsx": lambda p, c: pd.read_excel(p, engine="openpyxl", dtype=str, keep_default_na=False, usecols=c),
        ".json": _read_json,
        ".parquet": lambda p, c: pd.read_parquet(p, columns=c),
    }
    reader = readers.get(suffix)
    if reader is None:
        raise ValueError(f"Unsupported file format: {suffix}")
    return reader(path, columns)


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".json", ".parquet"}
