import json

from fastapi import APIRouter, HTTPException

from ..db import get_upload_path, project_db, require_project
from ..services.ingest import read_file
from ..services.jitter import apply_jitter

router = APIRouter(prefix="/api/projects/{project_id}", tags=["columns"])

VALID_STRATEGIES = {"fake", "jitter", "format-preserve", "hash", "drop", "passthrough"}


@router.get("/files/{file_id}/columns")
async def list_columns(project_id: str, file_id: str):
    require_project(project_id)

    with project_db(project_id) as pdb:
        rows = pdb.execute(
            "SELECT name, dtype, strategy, profile_json FROM columns WHERE file_id = ?",
            (file_id,),
        ).fetchall()

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
    require_project(project_id)

    strategy = body.get("strategy")
    if strategy not in VALID_STRATEGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy. Must be one of: {sorted(VALID_STRATEGIES)}",
        )

    with project_db(project_id) as pdb:
        cursor = pdb.execute(
            "UPDATE columns SET strategy = ? WHERE file_id = ? AND name = ?",
            (strategy, file_id, col_name),
        )
        pdb.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Column '{col_name}' not found")

    return {"status": "updated", "column": col_name, "strategy": strategy}


@router.post("/files/{file_id}/columns/{col_name}/jitter")
async def jitter_column(project_id: str, file_id: str, col_name: str, body: dict | None = None):
    require_project(project_id)

    alpha = (body or {}).get("alpha", 0.05)

    with project_db(project_id) as pdb:
        file_path = get_upload_path(pdb, file_id)

    df = read_file(file_path)
    if col_name not in df.columns:
        raise HTTPException(status_code=404, detail=f"Column '{col_name}' not in file")

    series = df[col_name].dropna()
    try:
        jittered, histogram_data = apply_jitter(series, alpha=alpha)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Jitter failed: {e}")

    return histogram_data
