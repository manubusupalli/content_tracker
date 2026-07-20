from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user, require_role
from models.task import AssignedRole, TaskState
from models.user import User, UserRole
from schemas.task import TaskCreate, TaskResponse, TaskUpdate
from services import task_service
from services.task_service import TaskNotFoundError

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Which roles may move a task off of a given current state (spec: security-specs.md).
_ADVANCE_RULES: dict[UserRole, set[TaskState]] = {
    UserRole.admin: set(TaskState),
    UserRole.content_team: {TaskState.code_ready},
    UserRole.video_editor: {TaskState.recorded, TaskState.editing},
    UserRole.uploader: {TaskState.uploaded},
}


def _check_can_advance(role: UserRole, current_state: TaskState) -> None:
    if current_state not in _ADVANCE_RULES[role]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"role {role.value} cannot advance from state {current_state.value}",
        )


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    state: str | None = None,
    assigned_role: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    parsed_state: TaskState | None = None
    if state is not None:
        try:
            parsed_state = TaskState(state)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"invalid state: {state}",
            ) from None

    parsed_role: AssignedRole | None = None
    if assigned_role is not None:
        try:
            parsed_role = AssignedRole(assigned_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"invalid role: {assigned_role}",
            ) from None

    return await task_service.list_tasks(db, state=parsed_state, assigned_role=parsed_role)


@router.get("/by-role/{role}", response_model=list[TaskResponse])
async def list_tasks_by_role(
    role: AssignedRole,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    return await task_service.list_tasks_by_role(db, role)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.admin, UserRole.content_team)
    ),
) -> TaskResponse:
    return await task_service.create_task(db, payload)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    try:
        if payload.state is not None:
            task = await task_service.get_task(db, task_id)
            _check_can_advance(current_user.role, task.state)
        return await task_service.update_task(db, task_id, payload)
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
) -> Response:
    try:
        await task_service.delete_task(db, task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
