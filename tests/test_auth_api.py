# personal-ai-assistant/tests/test_auth_api.py


def test_register_new_user(client):
    response = client.post(
        "/auth/register", json={"email": "new@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new@example.com"
    assert "id" in data
    assert "hashed_password" not in data  # never leak the hash


def test_register_duplicate_email_rejected(client, registered_user):
    response = client.post("/auth/register", json=registered_user)
    assert response.status_code == 400


def test_register_invalid_email_format_rejected(client):
    response = client.post(
        "/auth/register", json={"email": "not-an-email", "password": "password123"}
    )
    assert response.status_code == 422


def test_register_missing_password_rejected(client):
    response = client.post("/auth/register", json={"email": "nopass@example.com"})
    assert response.status_code == 422


def test_login_with_correct_credentials(client, registered_user):
    response = client.post(
        "/auth/login",
        data={"username": registered_user["email"], "password": registered_user["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_wrong_password_rejected(client, registered_user):
    response = client.post(
        "/auth/login",
        data={"username": registered_user["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_with_unknown_email_rejected(client):
    response = client.post(
        "/auth/login",
        data={"username": "ghost@example.com", "password": "whatever"},
    )
    assert response.status_code == 401


def test_login_token_works_on_protected_route(client, registered_user):
    """End-to-end check: a token from /auth/login should actually be
    accepted by get_current_user on a real protected route, not just
    look valid in isolation."""

    login_response = client.post(
        "/auth/login",
        data={"username": registered_user["email"], "password": registered_user["password"]},
    )
    token = login_response.json()["access_token"]

    response = client.get("/tasks/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_protected_route_requires_token(client):
    response = client.get("/tasks/")
    assert response.status_code == 401


def test_protected_route_rejects_garbage_token(client):
    response = client.get("/tasks/", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401