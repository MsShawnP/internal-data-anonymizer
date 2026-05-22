import json

from fastapi import APIRouter, HTTPException

from ..db import get_upload_path, load_mappings_by_column, project_db, require_project
from ..services.engine import generate_mappings
from ..services.ingest import read_file

router = APIRouter(prefix="/api/projects/{project_id}", tags=["mappings"])


@router.get("/mappings")
async def get_all_mappings(project_id: str):
    require_project(project_id)

    with project_db(project_id) as pdb:
        rows = pdb.execute(
            "SELECT column_name, original, anonymized FROM mappings ORDER BY column_name, original"
        ).fetchall()

    result: dict[str, list[dict]] = {}
    for row in rows:
        col = row["column_name"]
        if col not in result:
            result[col] = []
        result[col].append({"original": row["original"], "anonymized": row["anonymized"]})
    return result


@router.get("/files/{file_id}/columns/{col_name}/mappings")
async def get_column_mappings(project_id: str, file_id: str, col_name: str):
    require_project(project_id)

    with project_db(project_id) as pdb:
        rows = pdb.execute(
            "SELECT original, anonymized FROM mappings WHERE column_name = ? ORDER BY original",
            (col_name,),
        ).fetchall()

    return [{"original": row["original"], "anonymized": row["anonymized"]} for row in rows]


@router.post("/files/{file_id}/columns/{col_name}/generate")
async def generate_column_mappings(project_id: str, file_id: str, col_name: str):
    require_project(project_id)

    with project_db(project_id) as pdb:
        col_row = pdb.execute(
            "SELECT strategy, profile_json FROM columns WHERE file_id = ? AND name = ?",
            (file_id, col_name),
        ).fetchone()
        if not col_row:
            raise HTTPException(status_code=404, detail="Column not found")

        strategy = col_row["strategy"]
        profile = json.loads(col_row["profile_json"]) if col_row["profile_json"] else {}
        detected_type = profile.get("detected_type", "generic_string")

        file_path = get_upload_path(pdb, file_id)
        file_row = pdb.execute("SELECT filename FROM files WHERE id = ?", (file_id,)).fetchone()

        df = read_file(file_path)
        if col_name not in df.columns:
            raise HTTPException(status_code=404, detail=f"Column '{col_name}' not in file")

        unique_values = df[col_name].dropna().astype(str).unique().tolist()

        mappings = generate_mappings(
            unique_values=unique_values,
            strategy=strategy,
            column_name=col_name,
            project_salt=project_id,
            detected_type=detected_type,
        )

        for original, anonymized in mappings.items():
            pdb.execute(
                "INSERT OR REPLACE INTO mappings (column_name, original, anonymized, file_name) VALUES (?, ?, ?, ?)",
                (col_name, original, anonymized, file_row["filename"] if file_row else None),
            )
        pdb.commit()

    return {
        "column": col_name,
        "strategy": strategy,
        "mappings": [{"original": k, "anonymized": v} for k, v in mappings.items()],
    }


@router.put("/mappings/{col_name}/{original_value}")
async def update_single_mapping(project_id: str, col_name: str, original_value: str, body: dict):
    require_project(project_id)

    new_value = body.get("anonymized")
    if not new_value or not new_value.strip():
        raise HTTPException(status_code=400, detail="Anonymized value cannot be empty")

    with project_db(project_id) as pdb:
        result = pdb.execute(
            "UPDATE mappings SET anonymized = ? WHERE column_name = ? AND original = ?",
            (new_value.strip(), col_name, original_value),
        )
        pdb.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Mapping not found")

    return {"status": "updated", "column": col_name, "original": original_value, "anonymized": new_value.strip()}


@router.get("/reverse-lookup")
async def reverse_lookup(project_id: str, q: str = ""):
    require_project(project_id)

    if not q.strip():
        return []

    with project_db(project_id) as pdb:
        rows = pdb.execute(
            "SELECT column_name, original, anonymized, file_name FROM mappings WHERE anonymized LIKE ?",
            (f"%{q.strip()}%",),
        ).fetchall()

    return [
        {
            "column_name": row["column_name"],
            "original": row["original"],
            "anonymized": row["anonymized"],
            "file_name": row["file_name"],
        }
        for row in rows
    ]
