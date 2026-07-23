# backend/app/api/routes/note_routes.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database.database import get_db
from backend.app.database.models import User
from backend.app.api.deps import get_current_user
from backend.app.schemas.note_schema import NoteCreate, NoteResponse, NoteUpdate
from backend.app.services.note_service import (
    create_note,
    get_notes,
    get_note_by_id,
    search_notes,
    update_note,
    delete_note,
)

router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
)


@router.post("/", response_model=NoteResponse)
def add_note(
    note: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_note(db, note, user_id=current_user.id)


@router.get("/", response_model=list[NoteResponse])
def show_notes(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_notes(db, user_id=current_user.id, limit=limit, offset=offset)


@router.get("/search", response_model=list[NoteResponse])
def search_notes_route(
    keyword: str | None = Query(None, description="Matches against title and content"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_notes(db, user_id=current_user.id, keyword=keyword, limit=limit, offset=offset)


@router.get("/{note_id}", response_model=NoteResponse)
def show_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = get_note_by_id(db, note_id, user_id=current_user.id)

    if note is None:
        raise HTTPException(status_code=404, detail=f"Note with id {note_id} not found.")

    return note


@router.put("/{note_id}", response_model=NoteResponse)
def update_note_route(
    note_id: int,
    note: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_note(db, note_id, note, user_id=current_user.id)


@router.delete("/{note_id}")
def delete_note_route(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return delete_note(db, note_id, user_id=current_user.id)