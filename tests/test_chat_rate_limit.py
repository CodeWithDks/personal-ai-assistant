# tests/test_chat_rate_limit.py

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token

client = TestClient(app)


@pytest.fixture
def auth_headers(registered_user):
    """Generates valid Bearer authentication headers using the registered_user fixture."""
    access_token = create_access_token(data={"sub": str(registered_user["id"])})
    return {"Authorization": f"Bearer {access_token}"}


def test_chat_character_limit_exceeded(auth_headers):
    """Verify that messages > 2000 characters return a 422 Unprocessable Entity."""
    long_message = "A" * 2005
    response = client.post(
        "/chat/",
        json={"message": long_message},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_chat_empty_message(auth_headers):
    """Verify that empty or whitespace messages return a 400 Bad Request."""
    response = client.post(
        "/chat/",
        json={"message": "   "},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Message cannot be empty."


def test_chat_rate_limiting(auth_headers, monkeypatch):
    """
    Verify that hitting /chat/ more than 10 times in a minute returns 429.
    Mocks build_assistant so no real LLM API calls are made.
    """
    def mock_invoke(*args, **kwargs):
        return {"messages": [type("Msg", (), {"content": "Test reply"})()]}

    monkeypatch.setattr(
        "backend.app.routes.chat_routes.build_assistant",
        lambda user_id: type("Assistant", (), {"invoke": mock_invoke})(),
    )

    # Send 10 valid requests
    for i in range(10):
        res = client.post(
            "/chat/",
            json={"message": f"Test message {i}"},
            headers=auth_headers,
        )
        assert res.status_code in (200, 429)

    # 11th request MUST hit 429 Too Many Requests
    res_exceeded = client.post(
        "/chat/",
        json={"message": "Overflow request"},
        headers=auth_headers,
    )
    assert res_exceeded.status_code == 429