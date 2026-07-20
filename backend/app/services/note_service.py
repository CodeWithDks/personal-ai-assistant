from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database.models import Note
from app.schemas.note_schema import NoteCreate, NoteUpdate

def create_note(db: Session, note: NoteCreate):
    new_note = Note(
        title = note.title,
        content = note.content
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return new_note


def get_notes(db: Session):
    return db.query(Note).all()


def get_note_by_id(db: Session, note_id: int):
    return db.query(Note).filter(Note.id == note_id).first()


def update_note(db: Session, note_id: int, note: NoteUpdate):
    db_note = get_note_by_id(db, note_id)

    if db_note is None:
        raise HTTPException(status_code=404, detail='Note not found')
    
    update_data = note.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_note, key, value)

    db.commit()
    db.refresh(db_note)

    return db_note



def delete_note(db: Session, note_id: int):
    db_note = get_note_by_id(db, note_id)

    if db_note is None:
        raise HTTPException(status_code=404, detail='Note not found')
    
    db.delete(db_note)
    db.commit()

    return {'message': 'Note deleted successfully.'}
