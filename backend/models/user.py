from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class UserRole(str, Enum):
    admin = "admin"
    content_team = "content_team"
    video_editor = "video_editor"
    uploader = "uploader"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, values_callable=lambda enum: [member.value for member in enum]),
        nullable=False,
    )
