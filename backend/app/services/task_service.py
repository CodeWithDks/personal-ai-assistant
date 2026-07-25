# backend/app/services/task_service.py

from sqlalchemy import or_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.database.models import Task
from backend.app.schemas.task_schema import TaskCreate, TaskUpdate, TaskStatus, TaskPriority


def find_duplicate_task(db: Session, user_id: int, title: str) -> Task | None:
    """
    Look for an existing PENDING task with the same title (case-insensitive,
    whitespace-trimmed) for this user. Completed tasks are ignored — a
    finished task with the same title shouldn't block creating a new one
    (e.g. a recurring "pay rent" task).
    """

    normalized_title = title.strip()

    return (
        db.query(Task)
        .filter(
            Task.user_id == user_id,
            func.lower(Task.status) == "pending",
            func.lower(Task.title) == normalized_title.lower(),
        )
        .first()
    )


def create_task(db: Session, task: TaskCreate, user_id: int) -> Task:
    """Create and persist a new task owned by user_id."""

    new_task = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        due_date=task.due_date,
        user_id=user_id,
    )

    try:
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create task.")

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


def _get_task_or_404(db: Session, task_id: int, user_id: int) -> Task:
    """Shared helper for update/delete: fetch a task scoped to user_id,
    or raise 404 if it doesn't exist / doesn't belong to this user.
    Deliberately the same error either way, so we don't leak which
    task IDs exist for other users."""

    db_task = get_task_by_id(db, task_id, user_id)

    if db_task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found.")

    return db_task


def search_tasks(
    db: Session,
    user_id: int,
    keyword: str | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Task]:
    """Search this user's tasks by keyword, status, and/or priority."""

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

    if priority:
        query = query.filter(func.lower(Task.priority) == priority.value)

    return (
        query.order_by(Task.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_task(db: Session, task_id: int, task: TaskUpdate, user_id: int) -> Task:
    """Update a task, but only if it belongs to user_id."""

    db_task = _get_task_or_404(db, task_id, user_id)

    update_data = task.model_dump(exclude_unset=True)

    if update_data.get("status") is not None:
        update_data["status"] = update_data["status"].value

    if update_data.get("priority") is not None:
        update_data["priority"] = update_data["priority"].value

    for key, value in update_data.items():
        setattr(db_task, key, value)

    try:
        db.commit()
        db.refresh(db_task)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update task.")

    return db_task


def delete_task(db: Session, task_id: int, user_id: int) -> dict:
    """Delete a task, but only if it belongs to user_id."""

    db_task = _get_task_or_404(db, task_id, user_id)
    deleted_title = db_task.title

    try:
        db.delete(db_task)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete task.")

    return {"message": f"'{deleted_title}' has been deleted successfully."}