from pydantic import BaseModel, ConfigDict, Field

from models.task import AssignedRole, TaskState


class TaskCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(min_length=1)
    description: str = ""
    assigned_role: AssignedRole = Field(alias="assignedRole")
    state: TaskState = TaskState.code_ready


class TaskUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = None
    description: str | None = None
    assigned_role: AssignedRole | None = Field(default=None, alias="assignedRole")
    state: TaskState | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: int
    title: str
    description: str
    assigned_role: AssignedRole = Field(alias="assignedRole")
    state: TaskState
    created_at: str = Field(alias="createdAt")
