from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    created_at: str
    file_count: int = 0


class StrategyUpdate(BaseModel):
    strategy: str


class MappingUpdate(BaseModel):
    anonymized: str


class JitterRequest(BaseModel):
    alpha: float = 0.05


class ExportRequest(BaseModel):
    file_id: str
    format: str = "csv"
