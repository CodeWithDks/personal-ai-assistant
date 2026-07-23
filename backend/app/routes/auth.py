# backend/app/api/routes/auth.py

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.database.database import get_db
from backend.app.schemas.user_schema import UserCreate, UserResponse, Token
from backend.app.services.auth_service import register_user, authenticate_user
from backend.app.core.security import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    return register_user(db, user)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Uses OAuth2PasswordRequestForm (username + password fields) rather than
    our UserLogin schema, because this is what powers the Swagger UI
    "Authorize" button out of the box. The frontend can still just send
    form-encoded {username: email, password: ...} to this endpoint.
    """

    user = authenticate_user(db, form_data.username, form_data.password)
    access_token = create_access_token(data={"sub": str(user.id)})

    return Token(access_token=access_token)