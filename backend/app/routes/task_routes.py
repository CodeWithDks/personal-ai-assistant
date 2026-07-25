# backend/app/api/routes/task_routes.py

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database.database import get_db
from backend.app.database.models import User
from backend.app.api.deps import get_current_user
from backend.app.schemas.task_schema import TaskCreate, TaskResponse, TaskUpdate, TaskStatus, TaskPriority
from backend.app.services.task_service import (
    create_task,
    get_tasks,
    get_task_by_id,
    search_tasks,
    update_task,
    delete_task,
)

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def add_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new task owned by the currently authenticated user."""
    return create_task(db, task, user_id=current_user.id)


@router.get(
    "/",
    response_model=list[TaskResponse],
    summary="List all tasks",
)
def show_tasks(
    limit: int = Query(100, ge=1, le=200, description="Max number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current user's tasks, newest first."""
    return get_tasks(db, user_id=current_user.id, limit=limit, offset=offset)


# NOTE: This route must stay ABOVE "/{task_id}" — FastAPI matches routes in
# declaration order, so "/search" would otherwise be swallowed by the
# "/{task_id}" path parameter (and fail trying to parse "search" as an int).
@router.get(
    "/search",
    response_model=list[TaskResponse],
    summary="Search tasks by keyword, status, and/or priority",
)
def search_tasks_route(
    keyword: str | None = Query(None, description="Matches against title and description"),
    status_filter: TaskStatus | None = Query(None, alias="status", description="Filter by task status"),
    priority: TaskPriority | None = Query(None, description="Filter by task priority"),
    limit: int = Query(50, ge=1, le=200, description="Max number of tasks to return"),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search the current user's tasks with optional filters."""
    return search_tasks(
        db,
        user_id=current_user.id,
        keyword=keyword,
        status=status_filter,
        priority=priority,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a single task by ID",
)
def show_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a single task, scoped to the current user."""
    task = get_task_by_id(db, task_id, user_id=current_user.id)

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found.")

    return task


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
)
def update_task_route(
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partially update a task owned by the current user. Only fields
    provided in the request body are changed."""
    return update_task(db, task_id, task, user_id=current_user.id)


@router.delete(
    "/{task_id}",
    summary="Delete a task",
)
def delete_task_route(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permanently delete a task owned by the current user."""
    return delete_task(db, task_id, user_id=current_user.id)