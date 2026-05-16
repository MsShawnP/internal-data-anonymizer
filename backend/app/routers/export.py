from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..db import DATA_DIR, get_conn, get_project_db
from ..services.applier import apply_mappings, export_dataframe

router = APIRouter(prefix="/api/projects/{project_id}", tags=["export"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


@router.get("/files/{file_id}/export")
async def export_file_get(project_id: str, file_id: str, format: str = "csv"):
    return await _do_export(project_id, file_id, format)


@router.post("/export")
async def export_anonymized(project_id: str, body: dict):
    file_id = body.get("file_id")
    fmt = body.get("format", "csv")
    return await _do_export(project_id, file_id, fmt)


async def _do_export(project_id: str, file_id: str, fmt: str = "csv"):
    conn = get_conn()
    if not conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

    if fmt not in ("csv", "xlsx", "json", "parquet"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    project_db = get_project_db(project_id)

    file_row = project_db.execute(
        "SELECT id, filename FROM files WHERE id = ?", (file_id,)
    ).fetchone()
    if not file_row:
        project_db.close()
        raise HTTPException(status_code=404, detail="File not found")

    original_ext = Path(file_row["filename"]).suffix.lower()
    file_path = UPLOAD_DIR / f"{file_id}{original_ext}"
    if not file_path.exists():
        project_db.close()
        raise HTTPException(status_code=404, detail="Original file not found on disk")

    col_rows = project_db.execute(
        "SELECT name, strategy FROM columns WHERE file_id = ?", (file_id,)
    ).fetchall()
    column_strategies = {row["name"]: row["strategy"] for row in col_rows}

    mapping_rows = project_db.execute(
        "SELECT column_name, original, anonymized FROM mappings"
    ).fetchall()
    column_mappings: dict[str, dict[str, str]] = {}
    for row in mapping_rows:
        col = row["column_name"]
        if col not in column_mappings:
            column_mappings[col] = {}
        column_mappings[col][row["original"]] = row["anonymized"]

    project_db.close()

    df = apply_mappings(file_path, column_mappings, column_strategies)

    output_dir = DATA_DIR / "projects" / project_id / "exports"
    output_path = export_dataframe(df, output_dir, fmt)

    media_types = {
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json",
        "parquet": "application/octet-stream",
    }

    return FileResponse(
        path=str(output_path),
        media_type=media_types[fmt],
        filename=f"anonymized.{fmt}",
    )
