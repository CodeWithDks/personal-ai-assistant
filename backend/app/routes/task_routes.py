# backend/app/api/routes/task_routes.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database.database import get_db
from backend.app.database.models import User
from backend.app.api.deps import get_current_user
from backend.app.schemas.task_schema import TaskCreate, TaskResponse, TaskUpdate, TaskStatus
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


@router.post("/", response_model=TaskResponse)
def add_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_task(db, task, user_id=current_user.id)


@router.get("/", response_model=list[TaskResponse])
def show_tasks(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_tasks(db, user_id=current_user.id, limit=limit, offset=offset)


@router.get("/search", response_model=list[TaskResponse])
def search_tasks_route(
    keyword: str | None = Query(None, description="Matches against title and description"),
    status: TaskStatus | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_tasks(
        db, user_id=current_user.id, keyword=keyword, status=status, limit=limit, offset=offset
    )


@router.get("/{task_id}", response_model=TaskResponse)
def show_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = get_task_by_id(db, task_id, user_id=current_user.id)

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found.")

    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task_route(
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_task(db, task_id, task, user_id=current_user.id)


@router.delete("/{task_id}")
def delete_task_route(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return delete_task(db, task_id, user_id=current_user.id)