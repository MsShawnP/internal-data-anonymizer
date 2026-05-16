import json

from fastapi import APIRouter, HTTPException

from ..db import get_conn, get_project_db

router = APIRouter(prefix="/api/projects/{project_id}", tags=["mappings"])


@router.get("/mappings")
async def get_all_mappings(project_id: str):
    conn = get_conn()
    if not conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    project_db = get_project_db(project_id)
    rows = project_db.execute(
        "SELECT column_name, original, anonymized FROM mappings ORDER BY column_name, original"
    ).fetchall()
    project_db.close()

    result: dict[str, list[dict]] = {}
    for row in rows:
        col = row["column_name"]
        if col not in result:
            result[col] = []
        result[col].append({"original": row["original"], "anonymized": row["anonymized"]})
    return result


@router.get("/files/{file_id}/columns/{col_name}/mappings")
async def get_column_mappings(project_id: str, file_id: str, col_name: str):
    conn = get_conn()
    if not conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    project_db = get_project_db(project_id)
    rows = project_db.execute(
        "SELECT original, anonymized FROM mappings WHERE column_name = ? ORDER BY original",
        (col_name,),
    ).fetchall()
    project_db.close()

    return [{"original": row["original"], "anonymized": row["anonymized"]} for row in rows]


@router.post("/files/{file_id}/columns/{col_name}/generate")
async def generate_column_mappings(project_id: str, file_id: str, col_name: str):
    """Generate mappings for a column using the anonymization engine."""
    conn = get_conn()
    project_row = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project_row:
        raise HTTPException(status_code=404, detail="Project not found")

    project_db = get_project_db(project_id)

    # Get column info
    col_row = project_db.execute(
        "SELECT strategy, profile_json FROM columns WHERE file_id = ? AND name = ?",
        (file_id, col_name),
    ).fetchone()
    if not col_row:
        project_db.close()
        raise HTTPException(status_code=404, detail="Column not found")

    strategy = col_row["strategy"]
    profile = json.loads(col_row["profile_json"]) if col_row["profile_json"] else {}
    detected_type = profile.get("detected_type", "generic_string")
    sample_values = profile.get("sample_values", [])

    # Get unique values from the uploaded file
    from pathlib import Path
    from ..services.ingest import read_file

    upload_dir = Path(__file__).resolve().parent.parent.parent / "uploads"
    file_row = project_db.execute("SELECT filename FROM files WHERE id = ?", (file_id,)).fetchone()
    if not file_row:
        project_db.close()
        raise HTTPException(status_code=404, detail="File not found")

    ext = Path(file_row["filename"]).suffix.lower()
    file_path = upload_dir / f"{file_id}{ext}"

    df = read_file(file_path)
    if col_name not in df.columns:
        project_db.close()
        raise HTTPException(status_code=404, detail=f"Column '{col_name}' not in file")

    unique_values = df[col_name].dropna().astype(str).unique().tolist()

    # Generate mappings using engine
    from ..services.engine import generate_mappings

    mappings = generate_mappings(
        unique_values=unique_values,
        strategy=strategy,
        column_name=col_name,
        project_salt=project_id,
        detected_type=detected_type,
    )

    # Store in DB
    for original, anonymized in mappings.items():
        project_db.execute(
            "INSERT OR REPLACE INTO mappings (column_name, original, anonymized, file_name) VALUES (?, ?, ?, ?)",
            (col_name, original, anonymized, file_row["filename"]),
        )
    project_db.commit()
    project_db.close()

    return {
        "column": col_name,
        "strategy": strategy,
        "mappings": [{"original": k, "anonymized": v} for k, v in mappings.items()],
    }


@router.put("/mappings/{col_name}/{original_value}")
async def update_single_mapping(project_id: str, col_name: str, original_value: str, body: dict):
    """Update a single mapping's anonymized value."""
    conn = get_conn()
    if not conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    new_value = body.get("anonymized")
    if not new_value or not new_value.strip():
        raise HTTPException(status_code=400, detail="Anonymized value cannot be empty")

    project_db = get_project_db(project_id)
    result = project_db.execute(
        "UPDATE mappings SET anonymized = ? WHERE column_name = ? AND original = ?",
        (new_value.strip(), col_name, original_value),
    )
    project_db.commit()

    if result.rowcount == 0:
        project_db.close()
        raise HTTPException(status_code=404, detail="Mapping not found")

    project_db.close()
    return {"status": "updated", "column": col_name, "original": original_value, "anonymized": new_value.strip()}


@router.get("/reverse-lookup")
async def reverse_lookup(project_id: str, q: str = ""):
    """Search for an anonymized value and return its original."""
    conn = get_conn()
    if not conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    if not q.strip():
        return []

    project_db = get_project_db(project_id)
    rows = project_db.execute(
        "SELECT column_name, original, anonymized, file_name FROM mappings WHERE anonymized LIKE ?",
        (f"%{q.strip()}%",),
    ).fetchall()
    project_db.close()

    return [
        {
            "column_name": row["column_name"],
            "original": row["original"],
            "anonymized": row["anonymized"],
            "file_name": row["file_name"],
        }
        for row in rows
    ]
