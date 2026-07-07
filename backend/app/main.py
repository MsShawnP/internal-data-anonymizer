from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import close_db, init_db
from .routers import columns, export, mappings, projects, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    close_db()


app = FastAPI(title="Data Anonymizer", lifespan=lifespan)
app.include_router(projects.router)
app.include_router(upload.router)
app.include_router(columns.router)
app.include_router(mappings.router)
app.include_router(export.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
