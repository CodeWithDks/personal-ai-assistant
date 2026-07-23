# backend/app/services/auth_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.database.models import User
from backend.app.schemas.user_schema import UserCreate
from backend.app.core.security import hash_password, verify_password


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def register_user(db: Session, user: UserCreate) -> User:
    """Create a new user account. Raises 400 if the email is already taken."""

    existing = get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Verify credentials and return the user. Raises 401 if invalid."""

    user = get_user_by_email(db, email)

    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    return user