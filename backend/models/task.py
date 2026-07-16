from datetime import date
from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class TaskState(str, Enum):
    code_ready = "code_ready"
    recorded = "recorded"
    editing = "editing"
    uploaded = "uploaded"
    published = "published"


class AssignedRole(str, Enum):
    admin = "Admin"
    content = "Content"
    editor = "Editor"
    uploader = "Uploader"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False, default="")
    assigned_role: Mapped[AssignedRole] = mapped_column(
        SAEnum(AssignedRole, values_callable=lambda enum: [member.value for member in enum]),
        nullable=False,
    )
    state: Mapped[TaskState] = mapped_column(
        SAEnum(TaskState, values_callable=lambda enum: [member.value for member in enum]),
        nullable=False,
        default=TaskState.code_ready,
    )
    created_at: Mapped[str] = mapped_column(
        String, nullable=False, default=lambda: date.today().isoformat()
    )
