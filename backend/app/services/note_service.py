# backend/app/services/note_service.py

from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.database.models import Note
from backend.app.schemas.note_schema import NoteCreate, NoteUpdate


def create_note(db: Session, note: NoteCreate, user_id: int) -> Note:
    """Create and persist a new note owned by user_id."""

    new_note = Note(
        title=note.title,
        content=note.content,
        user_id=user_id,
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return new_note


def get_notes(db: Session, user_id: int, limit: int = 100, offset: int = 0) -> list[Note]:
    """Return this user's notes, newest first."""

    return (
        db.query(Note)
        .filter(Note.user_id == user_id)
        .order_by(Note.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_note_by_id(db: Session, note_id: int, user_id: int) -> Note | None:
    """Return a single note by ID, scoped to user_id."""

    return (
        db.query(Note)
        .filter(Note.id == note_id, Note.user_id == user_id)
        .first()
    )


def search_notes(
    db: Session,
    user_id: int,
    keyword: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Note]:
    """Search this user's notes by keyword, matched against title and content."""

    query = db.query(Note).filter(Note.user_id == user_id)

    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Note.title.ilike(pattern),
                Note.content.ilike(pattern),
            )
        )

    return (
        query.order_by(Note.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_note(db: Session, note_id: int, note: NoteUpdate, user_id: int) -> Note:
    """Update a note, but only if it belongs to user_id."""

    db_note = get_note_by_id(db, note_id, user_id)

    if db_note is None:
        raise HTTPException(status_code=404, detail=f"Note with id {note_id} not found.")

    update_data = note.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_note, key, value)

    db.commit()
    db.refresh(db_note)

    return db_note


def delete_note(db: Session, note_id: int, user_id: int) -> dict:
    """Delete a note, but only if it belongs to user_id."""

    db_note = get_note_by_id(db, note_id, user_id)

    if db_note is None:
        raise HTTPException(status_code=404, detail=f"Note with id {note_id} not found.")

    deleted_title = db_note.title or "Untitled note"

    db.delete(db_note)
    db.commit()

    return {"message": f"'{deleted_title}' has been deleted successfully."}