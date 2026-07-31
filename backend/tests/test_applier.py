"""Tests for apply/export safety (applier.py, export coverage).

Covers the cardinal anonymizer rule: real data must never reach the output.
"""

import sqlite3

import pandas as pd
import pytest

from app.routers.export import _ensure_mappings_cover
from app.services.applier import (
    _neutralize_cell,
    apply_mappings,
    export_dataframe,
)


def _write_csv(tmp_path, text):
    f = tmp_path / "t.csv"
    f.write_text(text)
    return f


class TestFailClosed:
    """A column set to a generative strategy must never export originals."""

    def test_missing_mapping_raises_not_leaks(self, tmp_path):
        f = _write_csv(tmp_path, "name,age\nAlice Real,30\nBob Real,40\n")
        with pytest.raises(ValueError):
            apply_mappings(
                f,
                column_mappings={},
                column_strategies={"name": "hash", "age": "passthrough"},
            )

    def test_partial_mapping_raises_on_unmapped_value(self, tmp_path):
        # Cross-file scenario: a new value ("Bob") has no mapping yet.
        f = _write_csv(tmp_path, "name\nAlice\nBob\n")
        with pytest.raises(ValueError):
            apply_mappings(f, {"name": {"Alice": "xxx"}}, {"name": "hash"})

    def test_full_mapping_applies(self, tmp_path):
        f = _write_csv(tmp_path, "name\nAlice\nBob\n")
        out = apply_mappings(
            f, {"name": {"Alice": "aaa", "Bob": "bbb"}}, {"name": "hash"}
        )
        assert list(out["name"]) == ["aaa", "bbb"]


class TestBlankPreservation:
    def test_blank_cells_stay_blank(self, tmp_path):
        # Second column keeps the middle line from being a skipped blank line.
        f = _write_csv(tmp_path, "name,keep\nAlice,x\n,y\nBob,z\n")
        out = apply_mappings(
            f,
            {"name": {"Alice": "aaa", "Bob": "bbb"}},
            {"name": "hash", "keep": "passthrough"},
        )
        assert list(out["name"]) == ["aaa", "", "bbb"]


class TestFormulaNeutralization:
    @pytest.mark.parametrize("bad", ["=cmd()", "+1+1", "@SUM(A1)", "-1+1", "\t=x", "\rfoo"])
    def test_dangerous_prefixed(self, bad):
        assert _neutralize_cell(bad).startswith("'")

    @pytest.mark.parametrize("ok", ["-5", "-5.2", "-1,000", "Alice", "5", "", "a=b"])
    def test_safe_unchanged(self, ok):
        assert _neutralize_cell(ok) == ok

    def test_export_csv_neutralizes(self, tmp_path):
        df = pd.DataFrame({"c": ["=danger", "-5", "safe"]})
        out = export_dataframe(df, tmp_path, "csv")
        text = out.read_text()
        assert "'=danger" in text
        assert "-5" in text


class TestExportCoverage:
    """Export generates + persists mappings for values not yet mapped."""

    def _mappings_conn(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute(
            "CREATE TABLE mappings (column_name TEXT, original TEXT, "
            "anonymized TEXT, file_name TEXT, UNIQUE(column_name, original))"
        )
        return conn

    def test_generates_missing_and_excludes_blanks(self):
        conn = self._mappings_conn()
        df = pd.DataFrame({"name": ["Alice", "Bob", ""]})
        column_mappings = {}
        _ensure_mappings_cover(
            conn, "salt123", df,
            {"name": "hash"}, {"name": "generic_string"}, column_mappings,
        )
        assert set(column_mappings["name"]) == {"Alice", "Bob"}  # blank excluded
        persisted = {r["original"] for r in conn.execute("SELECT original FROM mappings")}
        assert persisted == {"Alice", "Bob"}

    def test_keeps_existing_and_adds_new(self):
        conn = self._mappings_conn()
        conn.execute(
            "INSERT INTO mappings VALUES ('name', 'Alice', 'kept', NULL)"
        )
        df = pd.DataFrame({"name": ["Alice", "Carol"]})
        column_mappings = {"name": {"Alice": "kept"}}
        _ensure_mappings_cover(
            conn, "salt123", df,
            {"name": "hash"}, {"name": "generic_string"}, column_mappings,
        )
        assert column_mappings["name"]["Alice"] == "kept"  # not regenerated
        assert "Carol" in column_mappings["name"]
