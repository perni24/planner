from pydantic import BaseModel

class CreateTask(BaseModel):
    project_id: int
    title: str
    description: str = ""
    parent_id: int | None = None

class CreateArea(BaseModel):
    name: str

class CreateProject(BaseModel):
    area_id: int
    name: str
    description: str = ""

class UpdateProject(BaseModel):
    id: int
    name: str
    description: str = ""

class UpdateTask(BaseModel):
    id: int
    title: str
    description: str = ""

class SetTaskCompleted(BaseModel):
    id: int
    completed: bool
