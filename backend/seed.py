import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from database import AsyncSessionLocal
from models.task import Task

SEED_TASKS_PATH = Path(__file__).resolve().parents[1] / "specs" / "seed-data.json"


async def seed_tasks() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Task.id).limit(1))
        if existing.first() is not None:
            print("tasks table already has data, skipping seed")
            return

        tasks = json.loads(SEED_TASKS_PATH.read_text())
        for entry in tasks:
            session.add(
                Task(
                    id=entry["id"],
                    title=entry["title"],
                    description=entry["description"],
                    assigned_role=entry["assignedRole"],
                    state=entry["state"],
                    created_at=entry["createdAt"],
                )
            )
        await session.commit()
        print(f"seeded {len(tasks)} tasks")


if __name__ == "__main__":
    asyncio.run(seed_tasks())
