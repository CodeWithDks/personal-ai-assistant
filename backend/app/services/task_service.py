# backend/app/services/task_service.py

from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.database.models import Task
from backend.app.schemas.task_schema import TaskCreate, TaskUpdate, TaskStatus


def create_task(db: Session, task: TaskCreate, user_id: int) -> Task:
    """Create and persist a new task owned by user_id."""

    new_task = Task(
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        user_id=user_id,
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


def get_tasks(db: Session, user_id: int, limit: int = 100, offset: int = 0) -> list[Task]:
    """Return this user's tasks, newest first."""

    return (
        db.query(Task)
        .filter(Task.user_id == user_id)
        .order_by(Task.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_task_by_id(db: Session, task_id: int, user_id: int) -> Task | None:
    """Return a single task by ID, scoped to user_id so one user can never
    fetch another user's task even if they guess a valid ID."""

    return (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == user_id)
        .first()
    )


def search_tasks(
    db: Session,
    user_id: int,
    keyword: str | None = None,
    status: TaskStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Task]:
    """Search this user's tasks by keyword and/or status."""

    query = db.query(Task).filter(Task.user_id == user_id)

    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Task.title.ilike(pattern),
                Task.description.ilike(pattern),
            )
        )

    if status:
        query = query.filter(func.lower(Task.status) == status.value)

    return (
        query.order_by(Task.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_task(db: Session, task_id: int, task: TaskUpdate, user_id: int) -> Task:
    """Update a task, but only if it belongs to user_id. Raises 404 if the
    task doesn't exist OR belongs to someone else — deliberately the same
    error either way, so we don't leak which task IDs exist for other users."""

    db_task = get_task_by_id(db, task_id, user_id)

    if db_task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found.")

    update_data = task.model_dump(exclude_unset=True)

    if "status" in update_data and update_data["status"] is not None:
        update_data["status"] = update_data["status"].value

    for key, value in update_data.items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)

    return db_task


def delete_task(db: Session, task_id: int, user_id: int) -> dict:
    """Delete a task, but only if it belongs to user_id."""

    db_task = get_task_by_id(db, task_id, user_id)

    if db_task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found.")

    deleted_title = db_task.title

    db.delete(db_task)
    db.commit()

    return {"message": f"'{deleted_title}' has been deleted successfully."}