from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.note_schema import NoteCreate, NoteResponse,NoteUpdate
from app.services.note_service import create_note, get_notes, update_note, delete_note

router = APIRouter(
    prefix='/notes',
    tags=['Notes']
)

@router.post('/', response_model=NoteResponse)
def add_note(note: NoteCreate, db:Session = Depends(get_db)):
    return create_note(db, note)

@router.get('/', response_model=list[NoteResponse])
def show_notes(db: Session = Depends(get_db)):
    return get_notes(db)


@router.put('/{note_id}', response_model=NoteResponse)
def update_note_route(note_id: int, note: NoteUpdate, db: Session = Depends(get_db)):

    return update_note(db, note_id, note)


@router.delete('/{note_id}')
def delete_note_route(note_id: int, db: Session = Depends(get_db)):

    return delete_note(db, note_id)