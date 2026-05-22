from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..db import DATA_DIR, get_upload_path, load_mappings_by_column, project_db, require_project
from ..services.applier import apply_mappings, export_dataframe

router = APIRouter(prefix="/api/projects/{project_id}", tags=["export"])


@router.get("/files/{file_id}/export")
async def export_file_get(project_id: str, file_id: str, format: str = "csv"):
    return await _do_export(project_id, file_id, format)


@router.post("/export")
async def export_anonymized(project_id: str, body: dict):
    file_id = body.get("file_id")
    fmt = body.get("format", "csv")
    return await _do_export(project_id, file_id, fmt)


async def _do_export(project_id: str, file_id: str, fmt: str = "csv"):
    require_project(project_id)

    if fmt not in ("csv", "xlsx", "json", "parquet"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    with project_db(project_id) as pdb:
        file_path = get_upload_path(pdb, file_id)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Original file not found on disk")

        col_rows = pdb.execute(
            "SELECT name, strategy FROM columns WHERE file_id = ?", (file_id,)
        ).fetchall()
        column_strategies = {row["name"]: row["strategy"] for row in col_rows}

        column_mappings = load_mappings_by_column(pdb)

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
