from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    created_at: str
    file_count: int = 0
