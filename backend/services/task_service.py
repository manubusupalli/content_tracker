from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.task import Task
from schemas.task import TaskCreate, TaskUpdate


class TaskNotFoundError(Exception):
    def __init__(self, task_id: int) -> None:
        self.task_id = task_id
        super().__init__(f"Task {task_id} not found")


async def list_tasks(db: AsyncSession) -> list[Task]:
    result = await db.execute(select(Task).order_by(Task.id))
    return list(result.scalars().all())


async def create_task(db: AsyncSession, data: TaskCreate) -> Task:
    task = Task(
        title=data.title,
        description=data.description,
        assigned_role=data.assigned_role,
        state=data.state,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def _get_task(db: AsyncSession, task_id: int) -> Task:
    task = await db.get(Task, task_id)
    if task is None:
        raise TaskNotFoundError(task_id)
    return task


async def update_task(db: AsyncSession, task_id: int, data: TaskUpdate) -> Task:
    task = await _get_task(db, task_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: int) -> None:
    task = await _get_task(db, task_id)
    await db.delete(task)
    await db.commit()
