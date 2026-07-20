from langchain_community.tools import tool
from fastapi import HTTPException

from backend.app.schemas.task_schema import TaskCreate, TaskUpdate
from backend.app.services.task_service import (
    create_task,
    get_tasks,
    update_task,
    delete_task,
)
from app.database.database import SessionLocal


@tool
def create_task_tool(title: str, description: str = ""):
    """
    Create a new task.

    Use the user's task title and description.
    """

    db = SessionLocal()

    try:
        task = TaskCreate(
            title=title,
            description=description,
        )

        created_task = create_task(db, task)

        return {
            "success": True,
            "message": "Task created successfully.",
            "data": {
                "id": created_task.id,
                "title": created_task.title,
                "description": created_task.description,
            },
        }

    finally:
        db.close()


@tool
def get_tasks_tool():
    """
    Retrieve all tasks.

    Use this tool when the user wants to:
    - Show their tasks
    - List all tasks
    - View their to-do list
    - Check pending tasks
    - Check completed tasks

    Do not modify any tasks.
    """

    db = SessionLocal()

    try:
        tasks = get_tasks(db)

        if not tasks:
            return {
                "success": True,
                "message": "No tasks found.",
                "data": [],
            }

        return {
            "success": True,
            "message": f"Retrieved {len(tasks)} task(s).",
            "data": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "created_at": str(task.created_at),
                }
                for task in tasks
            ],
        }

    finally:
        db.close()


@tool
def update_task_tool(
    task_id: int,
    title: str | None = None,
    description: str | None = None,
):
    """
    Update an existing task.

    Update the title, description, or both. Only the provided fields will be updated.
    """

    db = SessionLocal()

    try:
        task_data = TaskUpdate(
            title=title,
            description=description,
        )

        updated_task = update_task(db, task_id, task_data)

        return {
            "success": True,
            "message": "Task updated successfully.",
            "data": {
                "id": updated_task.id,
                "title": updated_task.title,
                "description": updated_task.description,
                "status": updated_task.status,
                "created_at": str(updated_task.created_at),
            },
        }

    except HTTPException as e:
        return {
            "success": False,
            "message": e.detail,
            "data": None,
        }

    finally:
        db.close()


@tool
def delete_task_tool(task_id: int):
    """
    Delete a task by its ID.

    Use this tool only when the user explicitly wants to delete or remove a task.
    """

    db = SessionLocal()

    try:
        result = delete_task(db, task_id)

        return {
            "success": True,
            "message": result["message"],
            "data": None,
        }

    except HTTPException as e:
        return {
            "success": False,
            "message": e.detail,
            "data": None,
        }

    finally:
        db.close()