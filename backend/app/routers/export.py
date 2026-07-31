import asyncio
import hashlib
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..db import DATA_DIR, get_upload_path, load_mappings_by_column, project_db, require_project
from ..schemas import ExportRequest
from ..services.applier import apply_mappings, export_dataframe
from ..services.engine import generate_mappings
from ..services.ingest import read_file
from ..services.jitter import apply_jitter

router = APIRouter(prefix="/api/projects/{project_id}", tags=["export"])

GENERATIVE_STRATEGIES = ("fake", "format-preserve", "hash")

MEDIA_TYPES = {
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "json": "application/json",
    "parquet": "application/octet-stream",
}


@router.get("/files/{file_id}/export")
async def export_file_get(project_id: str, file_id: str, format: str = "csv"):
    return await _do_export(project_id, file_id, format)


@router.post("/export")
async def export_anonymized(project_id: str, body: ExportRequest):
    return await _do_export(project_id, body.file_id, body.format)


def _ensure_mappings_cover(
    pdb, project_id, df, column_strategies, detected_types, column_mappings
):
    """Generate + persist mappings for any non-blank value not yet mapped.

    Mutates column_mappings in place so the subsequent apply covers every value.
    """
    for col, strategy in column_strategies.items():
        if strategy not in GENERATIVE_STRATEGIES or col not in df.columns:
            continue
        existing = column_mappings.setdefault(col, {})
        uniques = [
            v for v in df[col].dropna().astype(str).unique() if v.strip() != ""
        ]
        missing = [v for v in uniques if v not in existing]
        if not missing:
            continue
        new_maps = generate_mappings(
            unique_values=missing,
            strategy=strategy,
            column_name=col,
            project_salt=project_id,
            detected_type=detected_types.get(col, "generic_string"),
        )
        for original, anonymized in new_maps.items():
            pdb.execute(
                "INSERT OR REPLACE INTO mappings (column_name, original, anonymized, file_name) VALUES (?, ?, ?, ?)",
                (col, original, anonymized, None),
            )
        pdb.commit()
        existing.update(new_maps)


async def _do_export(project_id: str, file_id: str, fmt: str = "csv"):
    require_project(project_id)

    if fmt not in MEDIA_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    with project_db(project_id) as pdb:
        file_path = get_upload_path(pdb, file_id)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Original file not found on disk")

        col_rows = pdb.execute(
            "SELECT name, strategy, profile_json FROM columns WHERE file_id = ?", (file_id,)
        ).fetchall()
        column_strategies = {row["name"]: row["strategy"] for row in col_rows}
        detected_types = {
            row["name"]: (json.loads(row["profile_json"]) if row["profile_json"] else {})
            .get("detected_type", "generic_string")
            for row in col_rows
        }

        file_columns = [row["name"] for row in col_rows]
        column_mappings = load_mappings_by_column(pdb, file_columns)

        df_orig = await asyncio.to_thread(read_file, file_path)

        # Fill any coverage gaps before applying. Mappings are deterministic
        # (seed = salt+column+value), so generating a missing value here yields
        # the same result as if it had been generated during review — this both
        # closes the fail-open leak and makes cross-file reuse actually work for
        # values a later file introduces.
        _ensure_mappings_cover(
            pdb, project_id, df_orig, column_strategies, detected_types, column_mappings
        )

    jitter_results = {}
    jitter_cols = [c for c, s in column_strategies.items() if s == "jitter"]
    if jitter_cols:
        seed_int = int(hashlib.sha256(project_id.encode()).hexdigest(), 16) % (2**31)
        for col in jitter_cols:
            if col in df_orig.columns:
                jittered, _ = apply_jitter(df_orig[col], seed=seed_int)
                jitter_results[col] = jittered

    df = apply_mappings(file_path, column_mappings, column_strategies, jitter_results)

    output_dir = DATA_DIR / "projects" / project_id / "exports"
    output_path = export_dataframe(df, output_dir, fmt)

    return FileResponse(
        path=str(output_path),
        media_type=MEDIA_TYPES[fmt],
        filename=f"anonymized.{fmt}",
    )
