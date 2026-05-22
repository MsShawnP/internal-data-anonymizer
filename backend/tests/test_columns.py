import json
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
def mock_project(tmp_path):
    """Create a mock project with a file and columns in a temp database."""
    project_id = uuid.uuid4().hex[:12]
    file_id = uuid.uuid4().hex[:12]

    app_db = sqlite3.connect(":memory:", check_same_thread=False)
    app_db.row_factory = sqlite3.Row
    app_db.execute(
        "CREATE TABLE projects (id TEXT PRIMARY KEY, name TEXT, created_at TEXT)"
    )
    app_db.execute(
        "INSERT INTO projects VALUES (?, ?, ?)",
        (project_id, "Test Project", datetime.now(timezone.utc).isoformat()),
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
    pdb.execute(
        "INSERT INTO files VALUES (?, ?, ?, ?, ?)",
        (file_id, "test.csv", datetime.now(timezone.utc).isoformat(), 100, 3),
    )

    columns_data = [
        (file_id, "email", "object", "fake", json.dumps({
            "detected_type": "email",
            "unique_count": 95,
            "null_rate": 0.02,
            "sample_values": ["a@b.com", "c@d.org", "e@f.net"],
            "stats": {},
        })),
        (file_id, "amount", "float64", "jitter", json.dumps({
            "detected_type": "numeric",
            "unique_count": 80,
            "null_rate": 0.0,
            "sample_values": ["100.5", "200.3", "300.7"],
            "stats": {"mean": 200.5, "std": 100.1, "min": 100.5, "max": 300.7},
        })),
        (file_id, "name", "object", "fake", json.dumps({
            "detected_type": "name",
            "unique_count": 90,
            "null_rate": 0.01,
            "sample_values": ["Alice Smith", "Bob Jones", "Carol White"],
            "stats": {},
        })),
    ]
    pdb.executemany(
        "INSERT INTO columns (file_id, name, dtype, strategy, profile_json) VALUES (?, ?, ?, ?, ?)",
        columns_data,
    )
    pdb.commit()
    pdb.close()

    return {
        "project_id": project_id,
        "file_id": file_id,
        "app_db": app_db,
        "project_db_path": project_db_path,
    }


def _mock_project_db_factory(project_db_path):
    @contextmanager
    def mock_project_db(project_id):
        conn = sqlite3.connect(str(project_db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    return mock_project_db


def _patch_columns_router(mock_project):
    """Patch at the point of use in the columns router."""
    mock_get_conn = lambda: mock_project["app_db"]
    mock_pdb = _mock_project_db_factory(mock_project["project_db_path"])
    return (
        patch("app.routers.columns.require_project"),
        patch("app.routers.columns.project_db", mock_pdb),
        patch("app.db.get_conn", mock_get_conn),
    )


def _patch_columns_router_no_project():
    """Patch for nonexistent project (require_project raises 404)."""
    from fastapi import HTTPException
    def raise_404(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return (patch("app.routers.columns.require_project", raise_404),)


class TestUpdateColumnStrategy:
    def test_valid_strategy_update(self, client, mock_project):
        pid = mock_project["project_id"]
        fid = mock_project["file_id"]

        p1, p2, p3 = _patch_columns_router(mock_project)
        with p1, p2, p3:
            resp = client.put(
                f"/api/projects/{pid}/files/{fid}/columns/email/strategy",
                json={"strategy": "hash"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "updated"
        assert data["column"] == "email"
        assert data["strategy"] == "hash"

    def test_invalid_strategy_returns_400(self, client, mock_project):
        pid = mock_project["project_id"]
        fid = mock_project["file_id"]

        p1, p2, p3 = _patch_columns_router(mock_project)
        with p1, p2, p3:
            resp = client.put(
                f"/api/projects/{pid}/files/{fid}/columns/email/strategy",
                json={"strategy": "invalid_strategy"},
            )

        assert resp.status_code == 400
        assert "Invalid strategy" in resp.json()["detail"]

    def test_nonexistent_project_returns_404(self, client):
        (p1,) = _patch_columns_router_no_project()
        with p1:
            resp = client.put(
                "/api/projects/nonexistent123/files/abc/columns/col/strategy",
                json={"strategy": "fake"},
            )

        assert resp.status_code == 404
        assert "Project not found" in resp.json()["detail"]

    def test_nonexistent_column_returns_404(self, client, mock_project):
        pid = mock_project["project_id"]
        fid = mock_project["file_id"]

        p1, p2, p3 = _patch_columns_router(mock_project)
        with p1, p2, p3:
            resp = client.put(
                f"/api/projects/{pid}/files/{fid}/columns/nonexistent_col/strategy",
                json={"strategy": "fake"},
            )

        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]

    def test_all_valid_strategies_accepted(self, client, mock_project):
        pid = mock_project["project_id"]
        fid = mock_project["file_id"]
        valid_strategies = ["fake", "jitter", "format-preserve", "hash", "drop", "passthrough"]

        for strategy in valid_strategies:
            p1, p2, p3 = _patch_columns_router(mock_project)
            with p1, p2, p3:
                resp = client.put(
                    f"/api/projects/{pid}/files/{fid}/columns/email/strategy",
                    json={"strategy": strategy},
                )
            assert resp.status_code == 200, f"Strategy '{strategy}' should be valid"


class TestListColumns:
    def test_list_columns_success(self, client, mock_project):
        pid = mock_project["project_id"]
        fid = mock_project["file_id"]

        p1, p2, p3 = _patch_columns_router(mock_project)
        with p1, p2, p3:
            resp = client.get(f"/api/projects/{pid}/files/{fid}/columns")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        names = [col["name"] for col in data]
        assert "email" in names
        assert "amount" in names
        assert "name" in names

        email_col = next(c for c in data if c["name"] == "email")
        assert email_col["detected_type"] == "email"
        assert email_col["strategy"] == "fake"
        assert len(email_col["sample_values"]) == 3

    def test_list_columns_nonexistent_project(self, client):
        (p1,) = _patch_columns_router_no_project()
        with p1:
            resp = client.get("/api/projects/nonexistent123/files/abc/columns")

        assert resp.status_code == 404
