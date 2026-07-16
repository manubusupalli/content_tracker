import asyncio

from sqlalchemy import select

from core.security import hash_password
from database import AsyncSessionLocal
from models.user import User, UserRole

DEMO_USERS = [
    ("admin", "admin123", UserRole.admin),
    ("content", "content123", UserRole.content_team),
    ("editor", "editor123", UserRole.video_editor),
    ("uploader", "uploader123", UserRole.uploader),
]


async def seed_users() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(User.id).limit(1))
        if existing.first() is not None:
            print("users table already has data, skipping seed")
            return

        for username, password, role in DEMO_USERS:
            session.add(
                User(
                    username=username,
                    hashed_password=hash_password(password),
                    role=role,
                )
            )
        await session.commit()
        print(f"seeded {len(DEMO_USERS)} users")


if __name__ == "__main__":
    asyncio.run(seed_users())
