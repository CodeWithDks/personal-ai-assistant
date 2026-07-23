# backend/app/ai/tools/tasks.py
#
# Tools are built PER USER via build_task_tools(user_id), not as static
# module-level functions. This is what makes the agent user-scoped: each
# closure below captures user_id, so create_task_tool etc. can never touch
# another user's data no matter what the LLM is told to do.

from datetime import datetime

from fastapi import HTTPException
from langchain_core.tools import tool

from backend.app.schemas.task_schema import TaskStatus, TaskCreate, TaskUpdate
from backend.app.services.task_service import (
    create_task,
    get_tasks,
    search_tasks,
    update_task,
    delete_task,
)
from backend.app.database.database import SessionLocal


def build_task_tools(user_id: int) -> list:
    """Build the set of task tools scoped to a single user. Call this once
    per chat session/request with the authenticated user's id, and pass
    the result into create_agent's tools list."""

    @tool
    def create_task_tool(
        title: str,
        description: str = "",
        due_date: str | None = None,
    ):
        """
        Create a new task the user wants to DO or be reminded about.

        Use ONLY when the user expresses intent to complete an action, e.g.
        "remind me to call the plumber", "add buy groceries to my list",
        "I need to finish the report by Friday".

        Do NOT use this for information the user just wants saved for
        reference — use create_note_tool instead.

        title: short actionable phrase (e.g. "Call the plumber") — required,
            cannot be empty
        description: optional extra detail (context, sub-steps) — do NOT
            repeat date/time info here if it's already captured in due_date
        due_date: ISO 8601 timestamp (e.g. "2026-07-21T21:00:00"), resolved
            from whatever the user said relative to the current date/time
            given in your system instructions. Leave unset if no
            date/time was mentioned — never guess one.
        """

        if not title.strip():
            return {
                "success": False,
                "message": "Task title cannot be empty.",
                "data": None,
            }

        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.fromisoformat(due_date)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Could not understand due_date '{due_date}'. Use ISO 8601 format.",
                    "data": None,
                }

        db = SessionLocal()

        try:
            task = TaskCreate(title=title, description=description, due_date=parsed_due_date)
            created_task = create_task(db, task, user_id=user_id)

            return {
                "success": True,
                "message": "Task created successfully.",
                "data": {
                    "id": created_task.id,
                    "title": created_task.title,
                    "description": created_task.description,
                    "due_date": str(created_task.due_date) if created_task.due_date else None,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Could not create task: {str(e)}",
                "data": None,
            }

        finally:
            db.close()

    @tool
    def get_tasks_tool():
        """
        Retrieve ALL of the current user's tasks, unfiltered.

        Use this ONLY when the user wants their full list with no filter, e.g.
        "show me all my tasks" or "what's on my to-do list".

        If the user mentions a keyword, topic, or status, use
        search_tasks_tool instead — it's more precise and cheaper.

        Do not modify any tasks.
        """

        db = SessionLocal()

        try:
            tasks = get_tasks(db, user_id=user_id)

            if not tasks:
                return {"success": True, "message": "No tasks found.", "data": []}

            return {
                "success": True,
                "message": f"Retrieved {len(tasks)} task(s).",
                "data": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "description": t.description,
                        "status": t.status,
                        "due_date": str(t.due_date) if t.due_date else None,
                        "created_at": str(t.created_at),
                    }
                    for t in tasks
                ],
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Could not retrieve tasks: {str(e)}",
                "data": None,
            }

        finally:
            db.close()

    @tool
    def search_tasks_tool(keyword: str | None = None, status: TaskStatus | None = None):
        """
        Search the current user's tasks by keyword and/or status. Use this
        whenever the user's request implies a filter rather than "show
        everything":
        - "find my task about the report" -> keyword="report"
        - "what tasks are still pending?" -> status="pending"

        This is also the right tool to call FIRST when the user wants to
        update or delete a task by title rather than by ID. If more than
        one result plausibly matches, list them and ask which one before
        acting.

        keyword: matched against title and description, case-insensitive.
        status: "pending" or "completed".
        """

        db = SessionLocal()

        try:
            tasks = search_tasks(db, user_id=user_id, keyword=keyword, status=status)

            if not tasks:
                return {"success": True, "message": "No matching tasks found.", "data": []}

            return {
                "success": True,
                "message": f"Found {len(tasks)} matching task(s).",
                "data": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "description": t.description,
                        "status": t.status,
                        "due_date": str(t.due_date) if t.due_date else None,
                        "created_at": str(t.created_at),
                    }
                    for t in tasks
                ],
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Could not search tasks: {str(e)}",
                "data": None,
            }

        finally:
            db.close()

    @tool
    def update_task_tool(
        task_id: int,
        title: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
    ):
        """
        Update the current user's task — title, description, due_date, or
        any combination. Only provided fields are changed.

        Requires task_id. If the user referred to the task by name only,
        call search_tasks_tool or get_tasks_tool first to find the matching
        task_id. If more than one plausibly matches, ask which one before
        calling this tool.

        due_date: ISO 8601 timestamp (e.g. "2026-07-21T21:00:00"), resolved
            relative to the current date/time in your system instructions.
        """

        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.fromisoformat(due_date)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Could not understand due_date '{due_date}'. Use ISO 8601 format.",
                    "data": None,
                }

        db = SessionLocal()

        try:
            task_data = TaskUpdate(
                title=title,
                description=description,
                due_date=parsed_due_date if due_date else None,
            )
            updated_task = update_task(db, task_id, task_data, user_id=user_id)

            return {
                "success": True,
                "message": "Task updated successfully.",
                "data": {
                    "id": updated_task.id,
                    "title": updated_task.title,
                    "description": updated_task.description,
                    "status": updated_task.status,
                    "due_date": str(updated_task.due_date) if updated_task.due_date else None,
                },
            }

        except HTTPException as e:
            return {"success": False, "message": e.detail, "data": None}

        except Exception as e:
            return {
                "success": False,
                "message": f"Could not update task: {str(e)}",
                "data": None,
            }

        finally:
            db.close()

    @tool
    def delete_task_tool(task_id: int):
        """
        Permanently delete the current user's task by ID. Cannot be undone.

        Use ONLY when the user explicitly wants to delete or remove a task.
        If they referred to it by name only and more than one task plausibly
        matches, call search_tasks_tool first and confirm the exact task_id
        before deleting.
        """

        db = SessionLocal()

        try:
            result = delete_task(db, task_id, user_id=user_id)
            return {"success": True, "message": result["message"], "data": None}

        except HTTPException as e:
            return {"success": False, "message": e.detail, "data": None}

        except Exception as e:
            return {
                "success": False,
                "message": f"Could not delete task: {str(e)}",
                "data": None,
            }

        finally:
            db.close()

    return [
        create_task_tool,
        get_tasks_tool,
        search_tasks_tool,
        update_task_tool,
        delete_task_tool,
    ]