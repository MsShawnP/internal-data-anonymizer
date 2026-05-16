import shutil
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..db import DATA_DIR, get_conn, get_project_db
from ..schemas import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, created_at FROM projects ORDER BY created_at DESC"
    ).fetchall()

    projects = []
    for row in rows:
        file_count = _get_file_count(row["id"])
        projects.append(
            ProjectResponse(
                id=row["id"],
                name=row["name"],
                created_at=row["created_at"],
                file_count=file_count,
            )
        )
    return projects


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(body: ProjectCreate):
    conn = get_conn()
    project_id = uuid.uuid4().hex[:12]
    created_at = datetime.now(timezone.utc).isoformat()

    conn.execute(
        "INSERT INTO projects (id, name, created_at) VALUES (?, ?, ?)",
        (project_id, body.name, created_at),
    )
    conn.commit()

    project_db = get_project_db(project_id)
    project_db.execute("""
        CREATE TABLE IF NOT EXISTS columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            name TEXT NOT NULL,
            dtype TEXT,
            strategy TEXT,
            profile_json TEXT
        )
    """)
    project_db.execute("""
        CREATE TABLE IF NOT EXISTS mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_name TEXT NOT NULL,
            original TEXT NOT NULL,
            anonymized TEXT NOT NULL,
            file_name TEXT,
            UNIQUE(column_name, original)
        )
    """)
    project_db.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            row_count INTEGER,
            column_count INTEGER
        )
    """)
    project_db.commit()
    project_db.close()

    return ProjectResponse(
        id=project_id, name=body.name, created_at=created_at, file_count=0
    )


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()

    project_dir = DATA_DIR / "projects" / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir)

    return None


def _get_file_count(project_id: str) -> int:
    project_dir = DATA_DIR / "projects" / project_id
    db_path = project_dir / "mappings.db"
    if not db_path.exists():
        return 0
    try:
        project_db = get_project_db(project_id)
        row = project_db.execute("SELECT COUNT(*) FROM files").fetchone()
        count = row[0] if row else 0
        project_db.close()
        return count
    except Exception:
        return 0
