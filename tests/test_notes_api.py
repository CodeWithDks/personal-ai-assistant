# personal-ai-assistant/tests/test_notes_api.py


def test_create_note(client, auth_headers):
    response = client.post(
        "/notes/",
        json={"title": "Wifi password", "content": "The password is hunter2"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Wifi password"
    assert data["content"] == "The password is hunter2"


def test_create_note_without_title(client, auth_headers):
    response = client.post(
        "/notes/", json={"content": "Untitled but valid"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["title"] is None


def test_list_notes(client, auth_headers):
    client.post("/notes/", json={"content": "Note 1"}, headers=auth_headers)
    client.post("/notes/", json={"content": "Note 2"}, headers=auth_headers)

    response = client.get("/notes/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_nonexistent_note_returns_404(client, auth_headers):
    response = client.get("/notes/99999", headers=auth_headers)
    assert response.status_code == 404


def test_update_note(client, auth_headers):
    created = client.post(
        "/notes/", json={"content": "Original content"}, headers=auth_headers
    ).json()

    response = client.put(
        f"/notes/{created['id']}",
        json={"content": "Updated content"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["content"] == "Updated content"


def test_update_note_title_only_does_not_wipe_content(client, auth_headers):
    """Regression test: same bug class as tasks — updating just the title
    must not null out content, since Note.content is nullable=False."""

    created = client.post(
        "/notes/",
        json={"title": "Original title", "content": "Important content to keep"},
        headers=auth_headers,
    ).json()

    response = client.put(
        f"/notes/{created['id']}",
        json={"title": "New title"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New title"
    assert data["content"] == "Important content to keep"


def test_delete_note(client, auth_headers):
    created = client.post(
        "/notes/", json={"content": "Temporary note"}, headers=auth_headers
    ).json()

    response = client.delete(f"/notes/{created['id']}", headers=auth_headers)
    assert response.status_code == 200

    follow_up = client.get(f"/notes/{created['id']}", headers=auth_headers)
    assert follow_up.status_code == 404


def test_search_notes_by_keyword_in_content(client, auth_headers):
    client.post("/notes/", json={"content": "My wifi password is xyz"}, headers=auth_headers)
    client.post("/notes/", json={"content": "Recipe for pasta"}, headers=auth_headers)

    response = client.get("/notes/search", params={"keyword": "wifi"}, headers=auth_headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert "wifi" in results[0]["content"].lower()


def test_search_notes_by_keyword_in_title(client, auth_headers):
    client.post(
        "/notes/", json={"title": "Trip Ideas", "content": "Somewhere warm"}, headers=auth_headers
    )
    client.post("/notes/", json={"content": "Unrelated note"}, headers=auth_headers)

    response = client.get("/notes/search", params={"keyword": "trip"}, headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


# --- User isolation ---

def test_user_cannot_see_another_users_notes(client, auth_headers, second_user_auth_headers):
    client.post("/notes/", json={"content": "Alice's private note"}, headers=auth_headers)

    response = client.get("/notes/", headers=second_user_auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_user_cannot_update_another_users_note(client, auth_headers, second_user_auth_headers):
    created = client.post(
        "/notes/", json={"content": "Alice's note"}, headers=auth_headers
    ).json()

    response = client.put(
        f"/notes/{created['id']}",
        json={"content": "Hacked by Bob"},
        headers=second_user_auth_headers,
    )
    assert response.status_code == 404

    still_original = client.get(f"/notes/{created['id']}", headers=auth_headers)
    assert still_original.json()["content"] == "Alice's note"