import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..db import get_conn, get_project_db
from ..services.ingest import read_file
from ..services.jitter import apply_jitter

router = APIRouter(prefix="/api/projects/{project_id}", tags=["columns"])

VALID_STRATEGIES = {"fake", "jitter", "format-preserve", "hash", "drop", "passthrough"}


@router.get("/files/{file_id}/columns")
async def list_columns(project_id: str, file_id: str):
    conn = get_conn()
    if not conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    project_db = get_project_db(project_id)
    rows = project_db.execute(
        "SELECT name, dtype, strategy, profile_json FROM columns WHERE file_id = ?",
        (file_id,),
    ).fetchall()
    project_db.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No columns found for this file")

    columns = []
    for row in rows:
        profile = json.loads(row["profile_json"]) if row["profile_json"] else {}
        columns.append({
            "name": row["name"],
            "dtype": row["dtype"],
            "strategy": row["strategy"],
            "detected_type": profile.get("detected_type"),
            "unique_count": profile.get("unique_count"),
            "null_rate": profile.get("null_rate"),
            "sample_values": profile.get("sample_values", []),
            "stats": profile.get("stats", {}),
        })

    return columns


@router.put("/files/{file_id}/columns/{col_name}/strategy")
async def update_column_strategy(project_id: str, file_id: str, col_name: str, body: dict):
    conn = get_conn()
    if not conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    strategy = body.get("strategy")
    if strategy not in VALID_STRATEGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy. Must be one of: {sorted(VALID_STRATEGIES)}",
        )

    project_db = get_project_db(project_id)
    cursor = project_db.execute(
        "UPDATE columns SET strategy = ? WHERE file_id = ? AND name = ?",
        (strategy, file_id, col_name),
    )
    project_db.commit()

    if cursor.rowcount == 0:
        project_db.close()
        raise HTTPException(status_code=404, detail=f"Column '{col_name}' not found")

    project_db.close()
    return {"status": "updated", "column": col_name, "strategy": strategy}


UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


@router.post("/files/{file_id}/columns/{col_name}/jitter")
async def jitter_column(project_id: str, file_id: str, col_name: str, body: dict = {}):
    conn = get_conn()
    if not conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    alpha = body.get("alpha", 0.05)
    project_db = get_project_db(project_id)

    file_row = project_db.execute("SELECT filename FROM files WHERE id = ?", (file_id,)).fetchone()
    if not file_row:
        project_db.close()
        raise HTTPException(status_code=404, detail="File not found")

    ext = Path(file_row["filename"]).suffix.lower()
    file_path = UPLOAD_DIR / f"{file_id}{ext}"
    project_db.close()

    df = read_file(file_path)
    if col_name not in df.columns:
        raise HTTPException(status_code=404, detail=f"Column '{col_name}' not in file")

    series = df[col_name].dropna()
    try:
        jittered, histogram_data = apply_jitter(series, alpha=alpha)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Jitter failed: {e}")

    return histogram_data
