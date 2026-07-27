# personal-ai-assistant/tests/test_tasks_api.py


def test_create_task(client, auth_headers):
    response = client.post(
        "/tasks/",
        json={"title": "Buy groceries", "description": "Milk, eggs, bread"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy groceries"
    assert data["status"] == "pending"
    assert data["priority"] == "medium"
    assert data["due_date"] is None


def test_create_task_with_due_date(client, auth_headers):
    response = client.post(
        "/tasks/",
        json={"title": "Study session", "due_date": "2026-08-01T18:00:00"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["due_date"] is not None


def test_create_task_with_priority(client, auth_headers):
    response = client.post(
        "/tasks/", json={"title": "High priority task", "priority": "high"}, headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["priority"] == "high"


def test_list_tasks(client, auth_headers):
    client.post("/tasks/", json={"title": "Task 1"}, headers=auth_headers)
    client.post("/tasks/", json={"title": "Task 2"}, headers=auth_headers)

    response = client.get("/tasks/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_single_task(client, auth_headers):
    created = client.post("/tasks/", json={"title": "Read a book"}, headers=auth_headers).json()

    response = client.get(f"/tasks/{created['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Read a book"


def test_get_nonexistent_task_returns_404(client, auth_headers):
    response = client.get("/tasks/99999", headers=auth_headers)
    assert response.status_code == 404


def test_update_task(client, auth_headers):
    created = client.post("/tasks/", json={"title": "Old title"}, headers=auth_headers).json()

    response = client.put(
        f"/tasks/{created['id']}",
        json={"title": "New title", "status": "completed"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New title"
    assert data["status"] == "completed"


def test_update_task_status_only_does_not_wipe_other_fields(client, auth_headers):
    """API-level version of the regression we found in the AI tool layer:
    a partial update (status only) must not null out title/description,
    since Task.title is nullable=False at the DB level."""

    created = client.post(
        "/tasks/",
        json={"title": "Finish the report", "description": "Q3 numbers"},
        headers=auth_headers,
    ).json()

    response = client.put(
        f"/tasks/{created['id']}",
        json={"status": "completed"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Finish the report"
    assert data["description"] == "Q3 numbers"
    assert data["status"] == "completed"


def test_update_task_priority_only_does_not_wipe_other_fields(client, auth_headers):
    created = client.post(
        "/tasks/", json={"title": "Reprioritize me"}, headers=auth_headers
    ).json()

    response = client.put(
        f"/tasks/{created['id']}",
        json={"priority": "high"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Reprioritize me"
    assert data["priority"] == "high"


def test_delete_task(client, auth_headers):
    created = client.post("/tasks/", json={"title": "Temporary task"}, headers=auth_headers).json()

    response = client.delete(f"/tasks/{created['id']}", headers=auth_headers)
    assert response.status_code == 200

    # confirm it's actually gone
    follow_up = client.get(f"/tasks/{created['id']}", headers=auth_headers)
    assert follow_up.status_code == 404


def test_search_tasks_by_keyword(client, auth_headers):
    client.post("/tasks/", json={"title": "Finish the report"}, headers=auth_headers)
    client.post("/tasks/", json={"title": "Buy milk"}, headers=auth_headers)

    response = client.get("/tasks/search", params={"keyword": "report"}, headers=auth_headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert "report" in results[0]["title"].lower()


def test_search_tasks_by_status(client, auth_headers):
    created = client.post("/tasks/", json={"title": "Done already"}, headers=auth_headers).json()
    client.put(f"/tasks/{created['id']}", json={"status": "completed"}, headers=auth_headers)
    client.post("/tasks/", json={"title": "Still pending"}, headers=auth_headers)

    response = client.get("/tasks/search", params={"status": "completed"}, headers=auth_headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["title"] == "Done already"


def test_search_tasks_by_priority(client, auth_headers):
    client.post("/tasks/", json={"title": "Urgent", "priority": "high"}, headers=auth_headers)
    client.post("/tasks/", json={"title": "Casual", "priority": "low"}, headers=auth_headers)

    response = client.get("/tasks/search", params={"priority": "high"}, headers=auth_headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["title"] == "Urgent"


# --- The tests that actually matter most: user isolation ---

def test_user_cannot_see_another_users_tasks(client, auth_headers, second_user_auth_headers):
    client.post("/tasks/", json={"title": "Alice's private task"}, headers=auth_headers)

    response = client.get("/tasks/", headers=second_user_auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_user_cannot_fetch_another_users_task_by_id(client, auth_headers, second_user_auth_headers):
    created = client.post(
        "/tasks/", json={"title": "Alice's task"}, headers=auth_headers
    ).json()

    response = client.get(f"/tasks/{created['id']}", headers=second_user_auth_headers)
    assert response.status_code == 404  # not 403 — existence itself isn't revealed


def test_user_cannot_delete_another_users_task(client, auth_headers, second_user_auth_headers):
    created = client.post(
        "/tasks/", json={"title": "Alice's task"}, headers=auth_headers
    ).json()

    response = client.delete(f"/tasks/{created['id']}", headers=second_user_auth_headers)
    assert response.status_code == 404

    # and it should still exist for Alice
    still_there = client.get(f"/tasks/{created['id']}", headers=auth_headers)
    assert still_there.status_code == 200