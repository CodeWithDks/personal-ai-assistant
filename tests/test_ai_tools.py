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


@pytest.fixture
def alice_id(client, auth_headers):
    """A real user row in the test DB, created through the actual
    register/login flow so foreign keys are valid. Returns the user's id."""

    return _current_user_id(client, auth_headers)


def _current_user_id(client, auth_headers) -> int:
    created = client.post("/tasks/", json={"title": "id-probe"}, headers=auth_headers).json()
    # the task's owner is the current user; we don't expose user_id on TaskResponse,
    # so instead grab it straight from the DB via the service layer in-process.
    from backend.app.database.models import Task

    db = TestingSessionLocal()
    try:
        task = db.query(Task).filter(Task.id == created["id"]).first()
        return task.user_id
    finally:
        db.close()


# --- Task tools ---

def test_create_task_tool_success(alice_id):
    tools = build_task_tools(alice_id)
    create_task_tool = tools[0]

    result = create_task_tool.invoke({"title": "Call the dentist"})
    assert result["success"] is True
    assert result["data"]["title"] == "Call the dentist"


def test_create_task_tool_rejects_empty_title(alice_id):
    tools = build_task_tools(alice_id)
    create_task_tool = tools[0]

    result = create_task_tool.invoke({"title": "   "})
    assert result["success"] is False


def test_create_task_tool_with_due_date(alice_id):
    tools = build_task_tools(alice_id)
    create_task_tool = tools[0]

    result = create_task_tool.invoke(
        {"title": "Study math", "due_date": "2026-08-01T21:00:00"}
    )
    assert result["success"] is True
    assert result["data"]["due_date"] is not None


def test_create_task_tool_rejects_bad_due_date_format(alice_id):
    tools = build_task_tools(alice_id)
    create_task_tool = tools[0]

    result = create_task_tool.invoke({"title": "Bad date test", "due_date": "not-a-date"})
    assert result["success"] is False
    assert "due_date" in result["message"].lower()


def test_search_tasks_tool_finds_by_keyword(alice_id):
    tools = build_task_tools(alice_id)
    create_task_tool, _, search_tasks_tool = tools[0], tools[1], tools[2]

    create_task_tool.invoke({"title": "Finish quarterly report"})
    create_task_tool.invoke({"title": "Buy milk"})

    result = search_tasks_tool.invoke({"keyword": "report"})
    assert result["success"] is True
    assert len(result["data"]) == 1


def test_update_task_tool_not_found_returns_clean_error(alice_id):
    tools = build_task_tools(alice_id)
    update_task_tool = tools[3]

    result = update_task_tool.invoke({"task_id": 99999, "title": "New title"})
    assert result["success"] is False
    assert "not found" in result["message"].lower()


def test_delete_task_tool(alice_id):
    tools = build_task_tools(alice_id)
    create_task_tool, delete_task_tool = tools[0], tools[4]

    created = create_task_tool.invoke({"title": "Temp task"})
    task_id = created["data"]["id"]

    result = delete_task_tool.invoke({"task_id": task_id})
    assert result["success"] is True


def test_task_tools_are_isolated_between_users(client, auth_headers, second_user_auth_headers):
    alice_id_val = _current_user_id(client, auth_headers)
    bob_id_val = _current_user_id(client, second_user_auth_headers)

    alice_tools = build_task_tools(alice_id_val)
    bob_tools = build_task_tools(bob_id_val)

    alice_tools[0].invoke({"title": "Alice's secret task"})

    bob_get_tasks_result = bob_tools[1].invoke({})
    titles = [t["title"] for t in bob_get_tasks_result["data"]]
    assert "Alice's secret task" not in titles


# --- Note tools ---

def test_create_note_tool_success(alice_id):
    tools = build_note_tools(alice_id)
    create_note_tool = tools[0]

    result = create_note_tool.invoke({"content": "Remember the wifi password"})
    assert result["success"] is True
    assert result["data"]["content"] == "Remember the wifi password"


def test_create_note_tool_rejects_empty_content(alice_id):
    tools = build_note_tools(alice_id)
    create_note_tool = tools[0]

    result = create_note_tool.invoke({"content": "   "})
    assert result["success"] is False


def test_search_notes_tool_finds_by_keyword(alice_id):
    tools = build_note_tools(alice_id)
    create_note_tool, _, search_notes_tool = tools[0], tools[1], tools[2]

    create_note_tool.invoke({"content": "The wifi password is hunter2"})
    create_note_tool.invoke({"content": "Pasta recipe: boil water first"})

    result = search_notes_tool.invoke({"keyword": "wifi"})
    assert result["success"] is True
    assert len(result["data"]) == 1


def test_note_tools_are_isolated_between_users(client, auth_headers, second_user_auth_headers):
    alice_id_val = _current_user_id(client, auth_headers)
    bob_id_val = _current_user_id(client, second_user_auth_headers)

    alice_tools = build_note_tools(alice_id_val)
    bob_tools = build_note_tools(bob_id_val)

    alice_tools[0].invoke({"content": "Alice's secret note"})

    bob_get_notes_result = bob_tools[1].invoke({})
    contents = [n["content"] for n in bob_get_notes_result["data"]]
    assert "Alice's secret note" not in contents