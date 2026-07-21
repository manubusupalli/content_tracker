from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password, verify_password
from models.user import User, UserRole
from schemas.auth import UserCreate


class UsernameTakenError(Exception):
    def __init__(self, username: str) -> None:
        self.username = username
        super().__init__(f"Username '{username}' is already taken")


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(db, username)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    if await get_user_by_username(db, data.username) is not None:
        raise UsernameTakenError(data.username)
    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        role=UserRole(data.role),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
