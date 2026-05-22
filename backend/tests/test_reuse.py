"""Tests for U10: Multi-file mapping reuse."""

import io
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def project_with_mappings(tmp_path):
    """Create a project that already has mappings from a previous file."""
    project_id = uuid.uuid4().hex[:12]

    app_db = sqlite3.connect(":memory:", check_same_thread=False)
    app_db.row_factory = sqlite3.Row
    app_db.execute(
        "CREATE TABLE projects (id TEXT PRIMARY KEY, name TEXT, created_at TEXT)"
    )
    app_db.execute(
        "INSERT INTO projects VALUES (?, ?, ?)",
        (project_id, "Reuse Test", datetime.now(timezone.utc).isoformat()),
    )
    app_db.commit()

    project_db_path = tmp_path / "mappings.db"
    pdb = sqlite3.connect(str(project_db_path), check_same_thread=False)
    pdb.row_factory = sqlite3.Row
    pdb.execute("""
        CREATE TABLE columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            name TEXT NOT NULL,
            dtype TEXT,
            strategy TEXT,
            profile_json TEXT
        )
    """)
    pdb.execute("""
        CREATE TABLE files (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            row_count INTEGER,
            column_count INTEGER
        )
    """)
    pdb.execute("""
        CREATE TABLE mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_name TEXT NOT NULL,
            original TEXT NOT NULL,
            anonymized TEXT NOT NULL,
            file_name TEXT,
            UNIQUE(column_name, original)
        )
    """)
    pdb.execute(
        "INSERT INTO mappings (column_name, original, anonymized, file_name) VALUES (?, ?, ?, ?)",
        ("store_name", "Costco", "FakeStore Alpha", "file_a.csv"),
    )
    pdb.execute(
        "INSERT INTO mappings (column_name, original, anonymized, file_name) VALUES (?, ?, ?, ?)",
        ("store_name", "Walmart", "FakeStore Beta", "file_a.csv"),
    )
    pdb.execute(
        "INSERT INTO mappings (column_name, original, anonymized, file_name) VALUES (?, ?, ?, ?)",
        ("store_name", "Target", "FakeStore Gamma", "file_a.csv"),
    )
    pdb.commit()
    pdb.close()

    return {
        "project_id": project_id,
        "app_db": app_db,
        "project_db_path": project_db_path,
        "tmp_path": tmp_path,
    }


def _patch_upload_router(ctx):
    """Patch at the point of use in the upload router."""
    @contextmanager
    def mock_project_db(project_id):
        conn = sqlite3.connect(str(ctx["project_db_path"]), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    return (
        patch("app.routers.upload.require_project"),
        patch("app.routers.upload.project_db", mock_project_db),
    )


class TestMultiFileReuse:
    def test_upload_with_all_known_values_sets_all_values_mapped(
        self, client, project_with_mappings
    ):
        """File B has same stores as File A — all values already mapped."""
        ctx = project_with_mappings
        csv_content = "store_name,amount\nCostco,100\nWalmart,200\nTarget,300\n"

        p1, p2 = _patch_upload_router(ctx)
        with p1, p2:
            from app.db import UPLOAD_DIR
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

            res = client.post(
                f"/api/projects/{ctx['project_id']}/upload",
                files={"file": ("file_b.csv", io.BytesIO(csv_content.encode()), "text/csv")},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["reuse_summary"]["store_name"]["auto_applied"] == 3
        assert data["reuse_summary"]["store_name"]["new_values"] == 0

    def test_upload_with_some_new_values(self, client, project_with_mappings):
        """File B has 2 known stores + 1 new store."""
        ctx = project_with_mappings
        csv_content = "store_name,amount\nCostco,100\nWalmart,200\nNewStore,300\n"

        p1, p2 = _patch_upload_router(ctx)
        with p1, p2:
            from app.db import UPLOAD_DIR
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

            res = client.post(
                f"/api/projects/{ctx['project_id']}/upload",
                files={"file": ("file_b.csv", io.BytesIO(csv_content.encode()), "text/csv")},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["reuse_summary"]["store_name"]["auto_applied"] == 2
        assert data["reuse_summary"]["store_name"]["new_values"] == 1
        assert data["all_values_mapped"] is False

    def test_upload_with_new_column(self, client, project_with_mappings):
        """File B has a column not in File A — no reuse for that column."""
        ctx = project_with_mappings
        csv_content = "city,amount\nNew York,100\nChicago,200\n"

        p1, p2 = _patch_upload_router(ctx)
        with p1, p2:
            from app.db import UPLOAD_DIR
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

            res = client.post(
                f"/api/projects/{ctx['project_id']}/upload",
                files={"file": ("file_c.csv", io.BytesIO(csv_content.encode()), "text/csv")},
            )

        assert res.status_code == 200
        data = res.json()
        assert "city" not in data["reuse_summary"]
        assert data["all_values_mapped"] is False
