import sqlite3
from contextlib import contextmanager
from pathlib import Path

from fastapi import HTTPException

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"

_conn: sqlite3.Connection | None = None


def _configure_conn(conn: sqlite3.Connection) -> None:
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")


def get_conn() -> sqlite3.Connection:
    if _conn is None:
        raise RuntimeError("Database not initialized")
    return _conn


def require_project(project_id: str) -> None:
    conn = get_conn()
    if not conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Project not found")


def init_db():
    global _conn
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_path = DATA_DIR / "app.db"
    _conn = sqlite3.connect(str(db_path), check_same_thread=False)
    _configure_conn(_conn)
    _conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    _conn.commit()


def close_db():
    global _conn
    if _conn:
        _conn.close()
        _conn = None


@contextmanager
def project_db(project_id: str):
    project_dir = DATA_DIR / "projects" / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(project_dir / "mappings.db"), check_same_thread=False)
    _configure_conn(conn)
    try:
        yield conn
    finally:
        conn.close()


def load_mappings_by_column(
    conn: sqlite3.Connection, columns: list[str] | None = None
) -> dict[str, dict[str, str]]:
    if columns:
        placeholders = ",".join("?" for _ in columns)
        rows = conn.execute(
            f"SELECT column_name, original, anonymized FROM mappings WHERE column_name IN ({placeholders}) ORDER BY column_name, original",
            columns,
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT column_name, original, anonymized FROM mappings ORDER BY column_name, original"
        ).fetchall()
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        col = row["column_name"]
        if col not in result:
            result[col] = {}
        result[col][row["original"]] = row["anonymized"]
    return result


def get_upload_path(conn: sqlite3.Connection, file_id: str) -> Path:
    file_row = conn.execute("SELECT filename FROM files WHERE id = ?", (file_id,)).fetchone()
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")
    ext = Path(file_row["filename"]).suffix.lower()
    return UPLOAD_DIR / f"{file_id}{ext}"
