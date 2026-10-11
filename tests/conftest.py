# personal-ai-assistant/tests/conftest.py
#
# Shared fixtures for every test file. Run pytest from the
# personal-ai-assistant/ project root so the `backend` package resolves.

# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker
# pyrefly: ignore [missing-import]
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database.database import Base, get_db
from backend.app.core.rate_limit import limiter

# In-memory SQLite, shared across connections within a test via StaticPool.
# Completely separate from assistant.db — tests never touch your real data.
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Automatically reset the in-memory rate limiter before/after every test function
    to prevent shared client IP rate-limiting (429 errors) during test runs."""
    limiter.reset()
    yield
    limiter.reset()


def _login(client: TestClient, email: str, password: str) -> dict:
    """Shared helper: log in a user and return ready-to-use Authorization
    headers. Used by both auth_headers and second_user_auth_headers so the
    login flow only has to be written (and fixed, if it ever breaks) once."""

    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def client():
    """A fresh, empty test database for every single test function."""
    Base.metadata.drop_all(bind=engine)  # Wipe any existing data/tables first
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def registered_user(client):
    """Register one test user (using an 8+ character password). Returns their credentials for login."""

    credentials = {
        "email": "alice@example.com",
        "password": "testpass123"  # Meets the new min_length=8 requirement
    }

    response = client.post("/auth/register", json=credentials)
    assert response.status_code == 200, response.text

    user = response.json()

    return {
        "id": user["id"],
        "email": credentials["email"],
        "password": credentials["password"],
    }

@pytest.fixture
def alice_id(registered_user):
    """Return Alice's database ID."""
    return registered_user["id"]


@pytest.fixture
def auth_headers(client, registered_user):
    """Register + log in a user, return ready-to-use Authorization headers."""

    return _login(client, registered_user["email"], registered_user["password"])


@pytest.fixture
def second_user_auth_headers(client):
    """A second, separate user — used to test that users can't see each
    other's data (the whole point of user scoping)."""

    credentials = {
        "email": "bob@example.com", 
        "password": "testpass456"  # Meets the new min_length=8 requirement
    }
    response = client.post("/auth/register", json=credentials)
    assert response.status_code == 200, response.text

    return _login(client, credentials["email"], credentials["password"])