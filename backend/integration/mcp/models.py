from typing import Annotated

from pydantic import BaseModel, Field

from validators.request_validator import SQLITE_MAX_INTEGER


EntityId = Annotated[int, Field(strict=True, gt=0, le=SQLITE_MAX_INTEGER)]

# None significa "non modificare": distinto da "" che svuota la descrizione.
OptionalDescription = Annotated[
    str | None,
    Field(description="New description. Omit it to keep the current one; use an empty string to clear it."),
]

class CreateTask(BaseModel):
    project_id: EntityId
    title: str
    description: str = ""
    parent_id: EntityId | None = None

class CreateArea(BaseModel):
    name: str

class CreateProject(BaseModel):
    area_id: EntityId
    name: str
    description: str = ""

class UpdateProject(BaseModel):
    id: EntityId
    name: str
    description: OptionalDescription = None

class UpdateTask(BaseModel):
    id: EntityId
    title: str
    description: OptionalDescription = None

class SetTaskCompleted(BaseModel):
    id: EntityId
    completed: bool
