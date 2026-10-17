from typing import Annotated

from pydantic import BaseModel, Field

# None significa "non modificare": distinto da "" che svuota la descrizione.
OptionalDescription = Annotated[
    str | None,
    Field(description="New description. Omit it to keep the current one; use an empty string to clear it."),
]

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
    description: OptionalDescription = None

class UpdateTask(BaseModel):
    id: int
    title: str
    description: OptionalDescription = None

class SetTaskCompleted(BaseModel):
    id: int
    completed: bool
