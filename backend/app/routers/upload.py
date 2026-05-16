import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile

from ..db import DATA_DIR, get_project_db, get_conn
from ..services.detector import profile_columns
from ..services.ingest import SUPPORTED_EXTENSIONS, read_file

router = APIRouter(prefix="/api/projects/{project_id}", tags=["upload"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


@router.post("/upload")
async def upload_file(project_id: str, file: UploadFile):
    conn = get_conn()
    row = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex[:12]
    save_path = UPLOAD_DIR / f"{file_id}{ext}"

    size = 0
    async with aiofiles.open(save_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                await out.close()
                save_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File too large")
            await out.write(chunk)

    try:
        df = read_file(save_path)
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    profiles = profile_columns(df)

    project_db = get_project_db(project_id)
    project_db.execute(
        "INSERT OR REPLACE INTO files (id, filename, uploaded_at, row_count, column_count) VALUES (?, ?, ?, ?, ?)",
        (file_id, file.filename, datetime.now(timezone.utc).isoformat(), len(df), len(df.columns)),
    )
    for p in profiles:
        import json
        project_db.execute(
            "INSERT INTO columns (file_id, name, dtype, strategy, profile_json) VALUES (?, ?, ?, ?, ?)",
            (file_id, p.name, p.dtype, p.suggested_strategy, json.dumps({
                "detected_type": p.detected_type,
                "unique_count": p.unique_count,
                "null_rate": p.null_rate,
                "sample_values": p.sample_values,
                "stats": p.stats,
            })),
        )
    project_db.commit()
    project_db.close()

    return {
        "file_id": file_id,
        "filename": file.filename,
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": [
            {
                "name": p.name,
                "dtype": p.dtype,
                "detected_type": p.detected_type,
                "suggested_strategy": p.suggested_strategy,
                "unique_count": p.unique_count,
                "null_rate": p.null_rate,
                "sample_values": p.sample_values,
                "stats": p.stats,
            }
            for p in profiles
        ],
    }
