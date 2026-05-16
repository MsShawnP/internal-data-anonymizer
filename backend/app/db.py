import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_conn: sqlite3.Connection | None = None


def get_conn() -> sqlite3.Connection:
    if _conn is None:
        raise RuntimeError("Database not initialized")
    return _conn


def init_db():
    global _conn
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_path = DATA_DIR / "app.db"
    _conn = sqlite3.connect(str(db_path), check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.execute("PRAGMA journal_mode=WAL")
    _conn.execute("PRAGMA synchronous=NORMAL")
    _conn.execute("PRAGMA foreign_keys=ON")
    _conn.execute("PRAGMA busy_timeout=5000")
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


def get_project_db(project_id: str) -> sqlite3.Connection:
    project_dir = DATA_DIR / "projects" / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(project_dir / "mappings.db"), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn
