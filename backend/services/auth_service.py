from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import verify_password
from models.user import User


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
