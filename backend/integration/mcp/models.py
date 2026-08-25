from pydantic import BaseModel

class TaskCreateInput(BaseModel):
    title: str
    description: str
    parent_id: int | None = None

class CreateArea(BaseModel):
    name: str

class CreateProject(BaseModel):
    area_id: int
    name: str
    description: str = ""