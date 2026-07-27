# backend/app/ai/tools/tasks.py
#
# Tools are built PER USER via build_task_tools(user_id), not as static
# module-level functions. This is what makes the agent user-scoped: each
# closure below captures user_id, so create_task_tool etc. can never touch
# another user's data no matter what the LLM is told to do.

import logging
from contextlib import contextmanager
from datetime import datetime

from fastapi import HTTPException
from langchain_core.tools import tool

from backend.app.schemas.task_schema import TaskStatus, TaskCreate, TaskUpdate, TaskPriority
from backend.app.services.task_service import (
    create_task,
    get_tasks,
    search_tasks,
    update_task,
    delete_task,
    find_duplicate_task,
    get_due_soon_tasks,
)
from backend.app.database.database import SessionLocal

logger = logging.getLogger(__name__)


@contextmanager
def _db_session():
    """Shared DB session lifecycle for all tools below — opens a session
    and guarantees it's closed afterward, regardless of success/failure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _parse_due_date(due_date: str | None) -> tuple[datetime | None, dict | None]:
    """Parse an ISO 8601 due_date string. Returns (parsed_value, error_response).
    error_response is None on success, or a ready-to-return error dict on failure."""

    if not due_date:
        return None, None

    try:
        return datetime.fromisoformat(due_date), None
    except ValueError:
        return None, {
            "success": False,
            "message": f"Could not understand due_date '{due_date}'. Use ISO 8601 format.",
            "data": None,
        }


def _serialize_task(t) -> dict:
    """Common shape used to return a task to the LLM/caller."""
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "priority": t.priority.value if hasattr(t.priority, "value") else t.priority,
        "due_date": str(t.due_date) if t.due_date else None,
        "created_at": str(t.created_at) if getattr(t, "created_at", None) else None,
    }


def build_task_tools(user_id: int) -> list:
    """Build the set of task tools scoped to a single user. Call this once
    per chat session/request with the authenticated user's id, and pass
    the result into create_agent's tools list."""

    @tool
    def create_task_tool(
        title: str,
        description: str = "",
        due_date: str | None = None,
        priority: TaskPriority | None = None,
        force: bool = False,
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
        force: leave this False on the first attempt. If the result comes
            back with "duplicate": true, ask the user whether they really
            want a second copy — only call this again with force=True if
            they explicitly confirm yes.

        Infer task priority from the user's wording.

        HIGH priority:
        - urgent
        - ASAP
        - immediately
        - critical
        - important
        - deadline today
        - don't let me forget

        LOW priority:
        - whenever
        - someday
        - later
        - no rush
        - if I have time

        MEDIUM priority:
        - everything else

        Pass the priority value when calling create_task_tool or update_task_tool.
        Do not mention priority unless it helps the user.
        """

        if not title.strip():
            return {
                "success": False,
                "message": "Task title cannot be empty.",
                "data": None,
            }

        parsed_due_date, error = _parse_due_date(due_date)
        if error:
            return error

        with _db_session() as db:
            try:
                if not force:
                    existing = find_duplicate_task(db, user_id=user_id, title=title)
                    if existing:
                        return {
                            "success": False,
                            "duplicate": True,
                            "message": (
                                f"There's already a pending task titled '{existing.title}' "
                                f"(id={existing.id}). Ask the user if they want to create "
                                f"another one anyway, or if they meant to update the existing one."
                            ),
                            "data": {
                                "id": existing.id,
                                "title": existing.title,
                                "status": existing.status,
                            },
                        }

                task = TaskCreate(
                    title=title,
                    description=description,
                    due_date=parsed_due_date,
                    priority=priority or TaskPriority.MEDIUM,
                )
                created_task = create_task(db, task, user_id=user_id)

                return {
                    "success": True,
                    "message": "Task created successfully.",
                    "data": _serialize_task(created_task),
                }

            except Exception as e:
                logger.exception("Failed to create task for user_id=%s", user_id)
                return {
                    "success": False,
                    "message": f"Could not create task: {str(e)}",
                    "data": None,
                }

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

        with _db_session() as db:
            try:
                tasks = get_tasks(db, user_id=user_id)

                if not tasks:
                    return {"success": True, "message": "No tasks found.", "data": []}

                return {
                    "success": True,
                    "message": f"Retrieved {len(tasks)} task(s).",
                    "data": [_serialize_task(t) for t in tasks],
                }

            except Exception as e:
                logger.exception("Failed to retrieve tasks for user_id=%s", user_id)
                return {
                    "success": False,
                    "message": f"Could not retrieve tasks: {str(e)}",
                    "data": None,
                }

    @tool
    def search_tasks_tool(
        keyword: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ):
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

        with _db_session() as db:
            try:
                tasks = search_tasks(
                    db, user_id=user_id, keyword=keyword, status=status, priority=priority
                )

                if not tasks:
                    return {"success": True, "message": "No matching tasks found.", "data": []}

                return {
                    "success": True,
                    "message": f"Found {len(tasks)} matching task(s).",
                    "data": [_serialize_task(t) for t in tasks],
                }

            except Exception as e:
                logger.exception("Failed to search tasks for user_id=%s", user_id)
                return {
                    "success": False,
                    "message": f"Could not search tasks: {str(e)}",
                    "data": None,
                }

    @tool
    def update_task_tool(
        task_id: int,
        title: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ):
        """
        Update the current user's task — title, description, due_date,
        status, priority, or any combination. Only fields you explicitly
        provide are changed; leaving a parameter unset preserves its
        existing value.

        Requires task_id. If the user referred to the task by name only,
        call search_tasks_tool or get_tasks_tool first to find the matching
        task_id. If more than one plausibly matches, ask which one before
        calling this tool.

        status: "pending" or "completed". Use this when the user says
        something like "I finished X", "mark X as done", or "I did the
        thing about X" — that's a completion signal, call this with
        status="completed" on the matching task.

        priority: "low", "medium", or "high".

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

        # Build the update payload with ONLY the fields actually provided.
        # Passing e.g. title=None explicitly into TaskUpdate(...) would make
        # Pydantic treat title as "set" (to None) — exclude_unset=True in the
        # service layer would then wipe title in the database, since the
        # Task.title column is nullable=False. Only include keys that were
        # genuinely given a value here.
        update_fields = {}
        if title is not None:
            update_fields["title"] = title
        if description is not None:
            update_fields["description"] = description
        if parsed_due_date is not None:
            update_fields["due_date"] = parsed_due_date
        if status is not None:
            update_fields["status"] = status
        if priority is not None:
            update_fields["priority"] = priority

        if not update_fields:
            return {
                "success": False,
                "message": "No fields provided to update.",
                "data": None,
            }

        db = SessionLocal()

        try:
            task_data = TaskUpdate(**update_fields)
            updated_task = update_task(db, task_id, task_data, user_id=user_id)

            return {
                "success": True,
                "message": "Task updated successfully.",
                "data": {
                    "id": updated_task.id,
                    "title": updated_task.title,
                    "description": updated_task.description,
                    "status": updated_task.status,
                    "priority": updated_task.priority,
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

    @tool
    def delete_task_tool(task_id: int):
        """
        Permanently delete the current user's task by ID. Cannot be undone.

        Use ONLY when the user explicitly wants to delete or remove a task.
        If they referred to it by name only and more than one task plausibly
        matches, call search_tasks_tool first and confirm the exact task_id
        before deleting.
        """

        with _db_session() as db:
            try:
                result = delete_task(db, task_id, user_id=user_id)
                return {"success": True, "message": result["message"], "data": None}

            except HTTPException as e:
                return {"success": False, "message": e.detail, "data": None}

            except Exception as e:
                logger.exception("Failed to delete task_id=%s for user_id=%s", task_id, user_id)
                return {
                    "success": False,
                    "message": f"Could not delete task: {str(e)}",
                    "data": None,
                }

    @tool
    def get_daily_briefing_tool():
        """
        Get the current user's tasks due within the next 24 hours or already
        overdue, sorted soonest-first. Use this when the user asks things like
        "what's on my plate today", "what do I have due", "give me my daily
        briefing", or "what should I focus on".

        Do not modify any tasks.
        """

        db = SessionLocal()

        try:
            due_soon = get_due_soon_tasks(db, user_id=user_id, within_hours=24)

            if not due_soon:
                return {
                    "success": True,
                    "message": "Nothing due in the next 24 hours.",
                    "data": [],
                }

            return {
                "success": True,
                "message": f"{len(due_soon)} task(s) due soon or overdue.",
                "data": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "priority": t.priority,
                        "due_date": str(t.due_date),
                    }
                    for t in due_soon
                ],
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Could not fetch briefing: {str(e)}",
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
        get_daily_briefing_tool,
    ]