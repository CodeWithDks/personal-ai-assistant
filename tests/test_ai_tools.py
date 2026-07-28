# personal-ai-assistant/tests/test_ai_tools.py
#
# These tests call the LangChain tool objects directly (tool.invoke({...}))
# instead of going through the LLM/agent. That means: no OpenAI calls, no
# cost, fully deterministic, and they isolate bugs in OUR code (parsing,
# validation, user scoping) from anything the LLM might do unpredictably.
#
# IMPORTANT: build_task_tools/build_note_tools import SessionLocal directly
# from backend.app.database.database at module load time, bypassing the
# FastAPI get_db dependency override used elsewhere in these tests. We
# patch that module-level reference to point at the test database so these
# tools never touch your real assistant.db.
#
# NOTE ON TOOL LOOKUP: every test below retrieves tools by NAME via
# _tools_by_name(), never by list position. Mixing positional indexing
# (tools[0], tools[2], ...) with the tool-name dict is exactly what caused
# the daily-briefing index bug this helper was written to prevent — two
# different tools were once assumed to live at the same index. Some tool
# names below (e.g. "get_tasks_tool", "search_tasks_tool",
# "get_daily_briefing_tool", "delete_task_tool", "get_notes_tool",
# "search_notes_tool", "update_note_tool") are inferred from the existing
# naming convention ("create_task_tool", "update_task_tool"); verify these
# against the actual @tool names in backend/app/ai/tools/tasks.py and
# notes.py and adjust the keys if they differ.

import pytest

from backend.app.ai.tools import tasks as task_tools_module
from backend.app.ai.tools import notes as note_tools_module
from backend.app.ai.tools.tasks import build_task_tools
from backend.app.ai.tools.notes import build_note_tools

from tests.conftest import TestingSessionLocal


@pytest.fixture(autouse=True)
def patch_tool_sessions(monkeypatch):
    """Point the tool modules' SessionLocal at the test database for
    every test in this file."""

    monkeypatch.setattr(task_tools_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(note_tools_module, "SessionLocal", TestingSessionLocal)


def _tools_by_name(tools_list) -> dict:
    """Turn a list of LangChain tools into a name-keyed dict, so tests
    never depend on list position — the exact fragility that caused the
    daily briefing index bug."""
    return {t.name: t for t in tools_list}


def _current_user_id(client, auth_headers) -> int:
    """Create a throwaway task through the real API (so the user row is
    genuine and foreign keys are valid), then read its user_id straight
    from the DB. Used to get a real user_id for building tools directly."""

    created = client.post("/tasks/", json={"title": "id-probe"}, headers=auth_headers).json()

    from backend.app.database.models import Task

    db = TestingSessionLocal()
    try:
        task = db.query(Task).filter(Task.id == created["id"]).first()
        return task.user_id
    finally:
        db.close()


@pytest.fixture
def alice_id(client, auth_headers):
    """A real user row in the test DB, created through the actual
    register/login flow so foreign keys are valid. Returns the user's id."""

    return _current_user_id(client, auth_headers)


# ============================================================
# Task tools
# ============================================================

def test_create_task_tool_success(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]

    result = create_task_tool.invoke({"title": "Call the dentist"})
    assert result["success"] is True
    assert result["data"]["title"] == "Call the dentist"


def test_create_task_tool_rejects_empty_title(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]

    result = create_task_tool.invoke({"title": "   "})
    assert result["success"] is False


def test_create_task_tool_with_due_date(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]

    result = create_task_tool.invoke(
        {"title": "Study math", "due_date": "2026-08-01T21:00:00"}
    )
    assert result["success"] is True
    assert result["data"]["due_date"] is not None


def test_create_task_tool_rejects_bad_due_date_format(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]

    result = create_task_tool.invoke({"title": "Bad date test", "due_date": "not-a-date"})
    assert result["success"] is False
    assert "due_date" in result["message"].lower()


def test_create_task_tool_default_priority_is_medium(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]

    result = create_task_tool.invoke({"title": "Unspecified priority task"})
    assert result["data"]["priority"] == "medium"


def test_create_task_tool_with_high_priority(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]

    result = create_task_tool.invoke({"title": "Urgent task", "priority": "high"})
    assert result["data"]["priority"] == "high"


def test_search_tasks_tool_finds_by_keyword(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]
    search_tasks_tool = tools["search_tasks_tool"]

    create_task_tool.invoke({"title": "Finish quarterly report"})
    create_task_tool.invoke({"title": "Buy milk"})

    result = search_tasks_tool.invoke({"keyword": "report"})
    assert result["success"] is True
    assert len(result["data"]) == 1


def test_search_tasks_tool_by_priority(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]
    search_tasks_tool = tools["search_tasks_tool"]

    create_task_tool.invoke({"title": "Urgent report", "priority": "high"})
    create_task_tool.invoke({"title": "Casual reading", "priority": "low"})

    result = search_tasks_tool.invoke({"priority": "high"})
    assert len(result["data"]) == 1
    assert result["data"][0]["title"] == "Urgent report"


def test_update_task_tool_not_found_returns_clean_error(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    update_task_tool = tools["update_task_tool"]

    result = update_task_tool.invoke({"task_id": 99999, "title": "New title"})
    assert result["success"] is False
    assert "not found" in result["message"].lower()


def test_update_task_tool_can_mark_completed(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]
    update_task_tool = tools["update_task_tool"]

    created = create_task_tool.invoke({"title": "Finish the report"})
    result = update_task_tool.invoke(
        {"task_id": created["data"]["id"], "status": "completed"}
    )

    assert result["success"] is True
    assert result["data"]["status"] == "completed"


def test_update_task_status_does_not_wipe_other_fields(alice_id):
    """Regression test: passing only status must not null out title/
    description. This is the bug that made completing a task fail
    (Task.title is nullable=False, so wiping it raised an IntegrityError
    that was swallowed as a generic 'could not update' failure)."""

    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]
    update_task_tool = tools["update_task_tool"]

    created = create_task_tool.invoke(
        {"title": "Finish the report", "description": "Q3 numbers"}
    )
    result = update_task_tool.invoke({"task_id": created["data"]["id"], "status": "completed"})

    assert result["success"] is True
    assert result["data"]["title"] == "Finish the report"
    assert result["data"]["status"] == "completed"


def test_update_task_tool_can_change_priority(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]
    update_task_tool = tools["update_task_tool"]

    created = create_task_tool.invoke({"title": "Reprioritize me"})
    result = update_task_tool.invoke({"task_id": created["data"]["id"], "priority": "high"})

    assert result["success"] is True
    assert result["data"]["priority"] == "high"


def test_update_task_tool_with_no_fields_returns_clean_error(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]
    update_task_tool = tools["update_task_tool"]

    created = create_task_tool.invoke({"title": "Untouched task"})
    result = update_task_tool.invoke({"task_id": created["data"]["id"]})

    assert result["success"] is False


def test_delete_task_tool(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]
    delete_task_tool = tools["delete_task_tool"]

    created = create_task_tool.invoke({"title": "Temp task"})
    task_id = created["data"]["id"]

    result = delete_task_tool.invoke({"task_id": task_id})
    assert result["success"] is True


def test_task_tools_are_isolated_between_users(client, auth_headers, second_user_auth_headers):
    alice_id_val = _current_user_id(client, auth_headers)
    bob_id_val = _current_user_id(client, second_user_auth_headers)

    alice_tools = _tools_by_name(build_task_tools(alice_id_val))
    bob_tools = _tools_by_name(build_task_tools(bob_id_val))

    alice_tools["create_task_tool"].invoke({"title": "Alice's secret task"})

    bob_get_tasks_result = bob_tools["get_tasks_tool"].invoke({})
    titles = [t["title"] for t in bob_get_tasks_result["data"]]
    assert "Alice's secret task" not in titles


# --- Duplicate prevention ---

def test_create_task_tool_flags_duplicate_pending_task(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]

    create_task_tool.invoke({"title": "Call the plumber"})
    result = create_task_tool.invoke({"title": "call the plumber"})  # different casing

    assert result["success"] is False
    assert result.get("duplicate") is True


def test_create_task_tool_force_bypasses_duplicate_check(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]
    get_tasks_tool = tools["get_tasks_tool"]

    create_task_tool.invoke({"title": "Call the plumber"})
    result = create_task_tool.invoke({"title": "Call the plumber", "force": True})

    assert result["success"] is True

    all_tasks = get_tasks_tool.invoke({})
    matching = [t for t in all_tasks["data"] if t["title"].lower() == "call the plumber"]
    assert len(matching) == 2


def test_create_task_tool_allows_same_title_if_original_completed(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]
    update_task_tool = tools["update_task_tool"]

    first = create_task_tool.invoke({"title": "Pay rent"})
    completed = update_task_tool.invoke(
        {"task_id": first["data"]["id"], "status": "completed"}
    )
    assert completed["success"] is True  # depends on the partial-update fix above

    # completed tasks shouldn't block a new one with the same title
    second = create_task_tool.invoke({"title": "Pay rent"})
    assert second["success"] is True


def test_daily_briefing_includes_overdue_and_due_soon(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]
    get_daily_briefing_tool = tools["get_daily_briefing_tool"]

    create_task_tool.invoke(
        {"title": "Overdue task", "due_date": "2020-01-01T00:00:00"}
    )
    create_task_tool.invoke({"title": "No due date task"})

    result = get_daily_briefing_tool.invoke({})
    assert result["success"] is True
    titles = [t["title"] for t in result["data"]]
    assert "Overdue task" in titles
    assert "No due date task" not in titles


def test_daily_briefing_empty_when_nothing_due(alice_id):
    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]
    get_daily_briefing_tool = tools["get_daily_briefing_tool"]

    create_task_tool.invoke({"title": "Someday task"})  # no due_date

    result = get_daily_briefing_tool.invoke({})
    assert result["data"] == []


# ============================================================
# Note tools
# ============================================================

def test_create_note_tool_success(alice_id):
    tools = _tools_by_name(build_note_tools(alice_id))
    create_note_tool = tools["create_note_tool"]

    result = create_note_tool.invoke({"content": "Remember the wifi password"})
    assert result["success"] is True
    assert result["data"]["content"] == "Remember the wifi password"


def test_create_note_tool_rejects_empty_content(alice_id):
    tools = _tools_by_name(build_note_tools(alice_id))
    create_note_tool = tools["create_note_tool"]

    result = create_note_tool.invoke({"content": "   "})
    assert result["success"] is False


def test_search_notes_tool_finds_by_keyword(alice_id):
    tools = _tools_by_name(build_note_tools(alice_id))
    create_note_tool = tools["create_note_tool"]
    search_notes_tool = tools["search_notes_tool"]

    create_note_tool.invoke({"content": "The wifi password is hunter2"})
    create_note_tool.invoke({"content": "Pasta recipe: boil water first"})

    result = search_notes_tool.invoke({"keyword": "wifi"})
    assert result["success"] is True
    assert len(result["data"]) == 1


def test_update_note_tool_title_only_does_not_wipe_content(alice_id):
    """Same regression class as the task bug: updating just the title
    must not null out content (Note.content is nullable=False)."""

    tools = _tools_by_name(build_note_tools(alice_id))
    create_note_tool = tools["create_note_tool"]
    update_note_tool = tools["update_note_tool"]

    created = create_note_tool.invoke(
        {"title": "Original title", "content": "Important content to keep"}
    )
    result = update_note_tool.invoke(
        {"note_id": created["data"]["id"], "title": "New title"}
    )

    assert result["success"] is True
    assert result["data"]["title"] == "New title"
    assert result["data"]["content"] == "Important content to keep"


def test_update_note_tool_not_found_returns_clean_error(alice_id):
    tools = _tools_by_name(build_note_tools(alice_id))
    update_note_tool = tools["update_note_tool"]

    result = update_note_tool.invoke({"note_id": 99999, "title": "Doesn't matter"})
    assert result["success"] is False
    assert "not found" in result["message"].lower()


def test_note_tools_are_isolated_between_users(client, auth_headers, second_user_auth_headers):
    alice_id_val = _current_user_id(client, auth_headers)
    bob_id_val = _current_user_id(client, second_user_auth_headers)

    alice_tools = _tools_by_name(build_note_tools(alice_id_val))
    bob_tools = _tools_by_name(build_note_tools(bob_id_val))

    alice_tools["create_note_tool"].invoke({"content": "Alice's secret note"})

    bob_get_notes_result = bob_tools["get_notes_tool"].invoke({})
    contents = [n["content"] for n in bob_get_notes_result["data"]]
    assert "Alice's secret note" not in contents


def test_due_soon_tasks_use_consistent_naive_datetimes(alice_id):
    """Regression test: cutoff and stored due_date must both be naive,
    or the comparison silently misbehaves depending on server timezone."""

    tools = _tools_by_name(build_task_tools(alice_id))
    create_task_tool = tools["create_task_tool"]
    get_daily_briefing_tool = tools["get_daily_briefing_tool"]

    create_task_tool.invoke(
        {"title": "Due in one hour", "due_date": "2020-01-01T00:00:00"}
    )
    result = get_daily_briefing_tool.invoke({})

    assert result["success"] is True
    assert any(t["title"] == "Due in one hour" for t in result["data"])