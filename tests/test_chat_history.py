# tests/test_chat_history.py
#
# GET /chat/history and DELETE /chat/history.
#
# Two kinds of tests:
#   1. Unit tests with fake messages (fast, exact control over edge cases)
#   2. A REAL LangGraph agent + a real in-memory checkpointer driven by a fake
#      model, to prove history extraction and thread deletion work against the
#      actual message objects LangGraph stores. No OpenAI calls anywhere.

import sqlite3

# pyrefly: ignore [missing-import]
import pytest
from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver

# pyrefly: ignore [missing-import]
from backend.app.routes import chat_routes as chat_routes_module


# ---------- unit tests: message filtering ----------

def test_visible_messages_keeps_only_human_visible_turns():
    messages = [
        SystemMessage(content="you are an assistant"),
        HumanMessage(content="add milk"),
        AIMessage(content="", tool_calls=[{"name": "create_task_tool", "args": {}, "id": "c1"}]),
        ToolMessage(content='{"success": true}', tool_call_id="c1"),
        AIMessage(content="Added 'milk'."),
        HumanMessage(content="   "),                       # empty -> dropped
        AIMessage(content=[{"type": "text", "text": "Anything else?"}]),  # block content
    ]
    assert chat_routes_module._visible_messages(messages) == [
        {"role": "user", "content": "add milk"},
        {"role": "assistant", "content": "Added 'milk'."},
        {"role": "assistant", "content": "Anything else?"},
    ]


# ---------- route tests: auth, validation, paths ----------

def test_history_requires_auth(client):
    assert client.get("/chat/history").status_code == 401
    assert client.delete("/chat/history").status_code == 401


@pytest.mark.parametrize("limit", [0, 101, -5])
def test_history_rejects_bad_limit(client, auth_headers, limit):
    response = client.get(f"/chat/history?limit={limit}", headers=auth_headers)
    assert response.status_code == 422


def test_trailing_slash_variant_redirects(client, auth_headers):
    """The contract paths have NO trailing slash; the slash variant redirects."""
    response = client.get("/chat/history/", headers=auth_headers, follow_redirects=False)
    assert response.status_code == 307


# ---------- integration with a real agent + real checkpointer ----------

class _FakeToolModel(GenericFakeChatModel):
    """Scripted chat model that tolerates tool binding."""

    def bind_tools(self, tools, **kwargs):
        return self


@tool
def ping_tool():
    """Return pong."""
    return "pong"


@pytest.fixture
def real_agent(monkeypatch):
    saver = SqliteSaver(sqlite3.connect(":memory:", check_same_thread=False))
    saver.setup()

    script = iter([
        # turn 1: model calls a tool, then answers
        AIMessage(content="", tool_calls=[{"name": "ping_tool", "args": {}, "id": "call_1"}]),
        AIMessage(content="Pong done."),
        # turn 2
        AIMessage(content="Second reply."),
    ])
    agent = create_agent(model=_FakeToolModel(messages=script), tools=[ping_tool], checkpointer=saver)

    monkeypatch.setattr(chat_routes_module, "build_assistant", lambda user_id: agent)
    monkeypatch.setattr(chat_routes_module, "get_checkpointer", lambda: saver)
    return agent


def test_new_user_gets_empty_history_not_404(client, auth_headers, real_agent):
    response = client.get("/chat/history", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"messages": []}


def test_history_after_conversation_is_filtered_ordered_and_limited(client, auth_headers, real_agent):
    assert client.post("/chat/", json={"message": "ping please"}, headers=auth_headers).status_code == 200
    assert client.post("/chat/", json={"message": "again"}, headers=auth_headers).status_code == 200

    response = client.get("/chat/history", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["messages"] == [
        {"role": "user", "content": "ping please"},
        {"role": "assistant", "content": "Pong done."},
        {"role": "user", "content": "again"},
        {"role": "assistant", "content": "Second reply."},
    ]

    # limit counts individual messages and keeps the most recent
    limited = client.get("/chat/history?limit=2", headers=auth_headers).json()["messages"]
    assert limited == [
        {"role": "user", "content": "again"},
        {"role": "assistant", "content": "Second reply."},
    ]


def test_delete_clears_memory_and_is_idempotent(client, auth_headers, real_agent):
    client.post("/chat/", json={"message": "ping please"}, headers=auth_headers)
    assert len(client.get("/chat/history", headers=auth_headers).json()["messages"]) == 2

    first = client.delete("/chat/history", headers=auth_headers)
    assert first.status_code == 204
    assert first.content == b""
    assert client.get("/chat/history", headers=auth_headers).json() == {"messages": []}

    second = client.delete("/chat/history", headers=auth_headers)   # nothing left to delete
    assert second.status_code == 204


def test_users_cannot_see_or_clear_each_others_history(client, auth_headers, second_user_auth_headers, real_agent):
    client.post("/chat/", json={"message": "ping please"}, headers=auth_headers)

    # Bob sees nothing of Alice's conversation...
    assert client.get("/chat/history", headers=second_user_auth_headers).json() == {"messages": []}
    # ...and clearing Bob's history leaves Alice's intact.
    assert client.delete("/chat/history", headers=second_user_auth_headers).status_code == 204
    assert len(client.get("/chat/history", headers=auth_headers).json()["messages"]) == 2


def test_history_errors_do_not_leak_details(client, auth_headers, monkeypatch):
    class _Broken:
        def get_state(self, config):
            raise RuntimeError("secret-internal-detail postgresql://user:pw@host")

    monkeypatch.setattr(chat_routes_module, "build_assistant", lambda user_id: _Broken())
    response = client.get("/chat/history", headers=auth_headers)
    assert response.status_code == 500
    assert "secret-internal-detail" not in response.text