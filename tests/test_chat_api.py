# personal-ai-assistant/tests/test_chat_api.py
#
# These tests mock build_assistant entirely, so they never call OpenAI —
# free, fast, deterministic. They test the /chat ROUTE's own logic (auth
# enforcement, message validation, response shaping, error handling), not
# the agent's reasoning. For real end-to-end agent behavior, see
# test_chat_integration.py (marked @pytest.mark.integration).

import pytest

from backend.app.routes import chat_routes as chat_routes_module


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeAssistant:
    """Stands in for the real LangGraph agent. Records what it was called
    with so tests can assert on it, and can be told to raise to simulate
    an agent failure."""

    def __init__(self, reply_text: str = "This is a mocked reply.", raise_error: bool = False):
        self.reply_text = reply_text
        self.raise_error = raise_error
        self.last_messages = None
        self.last_config = None

    def invoke(self, messages, config=None):
        self.last_messages = messages
        self.last_config = config
        if self.raise_error:
            raise RuntimeError("simulated agent failure")
        return {"messages": [_FakeMessage(self.reply_text)]}


@pytest.fixture
def fake_assistant(monkeypatch):
    """Patches build_assistant in the chat_routes module so /chat uses our
    fake instead of building a real agent. Returns the fake so tests can
    inspect what it was called with, or flip raise_error on it."""

    fake = _FakeAssistant()
    monkeypatch.setattr(chat_routes_module, "build_assistant", lambda user_id: fake)
    return fake


def test_chat_requires_auth(client):
    response = client.post("/chat/", json={"message": "hello"})
    assert response.status_code == 401


def test_chat_rejects_empty_message(client, auth_headers):
    response = client.post("/chat/", json={"message": "   "}, headers=auth_headers)
    assert response.status_code == 400


def test_chat_returns_assistant_reply(client, auth_headers, fake_assistant):
    fake_assistant.reply_text = "I've added that task for you."

    response = client.post(
        "/chat/", json={"message": "remind me to call the plumber"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["reply"] == "I've added that task for you."


def test_chat_passes_user_message_to_assistant(client, auth_headers, fake_assistant):
    client.post("/chat/", json={"message": "remind me to call the plumber"}, headers=auth_headers)

    assert fake_assistant.last_messages == {
        "messages": [("user", "remind me to call the plumber")]
    }


def test_chat_passes_a_thread_scoped_config(client, auth_headers, fake_assistant):
    client.post("/chat/", json={"message": "hello"}, headers=auth_headers)

    config = fake_assistant.last_config
    assert config is not None
    assert "configurable" in config
    assert config["configurable"]["thread_id"].startswith("user-")


def test_chat_handles_assistant_failure_gracefully(client, auth_headers, fake_assistant):
    fake_assistant.raise_error = True

    response = client.post("/chat/", json={"message": "hello"}, headers=auth_headers)
    assert response.status_code == 500
    assert "failed to respond" in response.json()["detail"].lower()


def test_chat_does_not_leak_internal_error_details(client, auth_headers, fake_assistant):
    """The raw exception message shouldn't be hidden entirely (we do want
    it for debugging), but this at least confirms we're not leaking a
    stack trace or exception class name structure to the client."""

    fake_assistant.raise_error = True

    response = client.post("/chat/", json={"message": "hello"}, headers=auth_headers)
    detail = response.json()["detail"]
    assert "Traceback" not in detail