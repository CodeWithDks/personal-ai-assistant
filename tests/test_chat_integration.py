# personal-ai-assistant/tests/test_chat_integration.py
#
# These tests call the REAL OpenAI API through the actual agent. They cost
# a small amount of money and are non-deterministic (an LLM might phrase
# things differently or occasionally pick a slightly different tool path).
#
# They do NOT run with a plain `pytest` invocation. Run them explicitly:
#     pytest -m integration
#
# Keep this file small — a handful of smoke tests that prove the full
# stack (auth -> agent -> tools -> DB) works end to end. Detailed logic
# testing belongs in test_ai_tools.py, not here.

import pytest

pytestmark = pytest.mark.integration


def test_chat_can_create_a_task(client, auth_headers):
    response = client.post(
        "/chat/", json={"message": "remind me to call the plumber"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert len(response.json()["reply"]) > 0

    # confirm it actually landed in the database, not just a chatty reply
    tasks = client.get("/tasks/", headers=auth_headers).json()
    assert any("plumber" in t["title"].lower() for t in tasks)


def test_chat_refuses_out_of_scope_request(client, auth_headers):
    response = client.post(
        "/chat/",
        json={"message": "write me a Python function to reverse a string"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    reply = response.json()["reply"].lower()
    # loose check — we're not pinning exact wording, just that it declined
    assert "code" not in reply or "can't" in reply or "cannot" in reply


def test_chat_creates_task_with_resolved_due_date(client, auth_headers):
    response = client.post(
        "/chat/", json={"message": "I have a meeting at 9pm today"}, headers=auth_headers
    )
    assert response.status_code == 200

    tasks = client.get("/tasks/", headers=auth_headers).json()
    meeting_task = next((t for t in tasks if "meeting" in t["title"].lower()), None)
    assert meeting_task is not None
    assert meeting_task["due_date"] is not None


def test_chat_empty_message_rejected(client, auth_headers):
    response = client.post("/chat/", json={"message": "   "}, headers=auth_headers)
    assert response.status_code == 400