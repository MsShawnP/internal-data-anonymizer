"""Tests for read_file cross-format consistency (ingest.py)."""

import json

import pandas as pd

from app.services.ingest import read_file


class TestJsonParity:
    """JSON reads must match CSV/XLSX: honor `columns`, blanks as "", str dtype."""

    def _write_json(self, tmp_path, records):
        f = tmp_path / "t.json"
        f.write_text(json.dumps(records))
        return f

    def test_honors_columns_argument(self, tmp_path):
        f = self._write_json(
            tmp_path, [{"a": "1", "b": "x"}, {"a": "2", "b": "y"}]
        )
        df = read_file(f, columns=["a"])
        assert list(df.columns) == ["a"]

    def test_nulls_become_blank_strings(self, tmp_path):
        f = self._write_json(tmp_path, [{"a": "1"}, {"a": None}])
        df = read_file(f)
        assert df["a"].tolist() == ["1", ""]

    def test_values_are_strings(self, tmp_path):
        f = self._write_json(tmp_path, [{"a": 1}, {"a": 2}])
        df = read_file(f)
        assert all(isinstance(v, str) for v in df["a"])
