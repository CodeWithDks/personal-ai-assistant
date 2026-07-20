from fastapi import HTTPException
from langchain_community.tools import tool

from app.schemas.note_schema import NoteCreate, NoteUpdate
from app.services.note_service import (
    create_note,
    get_notes,
    update_note,
    delete_note,
)
from app.database.database import SessionLocal


@tool
def create_note_tool(
    content: str,
    title: str | None = None,
):
    """
    Create a new note.

    Use this tool when the user wants to create or save a note.
    The content is required.
    """

    if not content.strip():
        return {
            "success": False,
            "message": "Note content cannot be empty.",
            "data": None,
        }

    db = SessionLocal()

    try:
        note = NoteCreate(
            title=title,
            content=content,
        )

        created_note = create_note(db, note)

        return {
            "success": True,
            "message": "Note created successfully.",
            "data": {
                "id": created_note.id,
                "title": created_note.title,
                "content": created_note.content,
                "created_at": str(created_note.created_at),
            },
        }

    finally:
        db.close()


@tool
def get_notes_tool():
    """
    Retrieve all notes.

    Use this tool when the user wants to:
    - Show notes
    - List notes
    - View notes
    - Read saved notes
    - Check their notes

    Do not modify any notes.
    """

    db = SessionLocal()

    try:
        notes = get_notes(db)

        if not notes:
            return {
                "success": True,
                "message": "No notes found.",
                "data": [],
            }

        return {
            "success": True,
            "message": f"Retrieved {len(notes)} note(s).",
            "data": [
                {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "created_at": str(note.created_at),
                }
                for note in notes
            ],
        }

    finally:
        db.close()


@tool
def update_note_tool(
    note_id: int,
    title: str | None = None,
    content: str | None = None,
):
    """
    Update an existing note.

    Update the title, content, or both.
    Only the fields provided will be updated.
    """

    db = SessionLocal()

    try:
        note_data = NoteUpdate(
            title=title,
            content=content,
        )

        updated_note = update_note(
            db=db,
            note_id=note_id,
            note=note_data,
        )

        return {
            "success": True,
            "message": "Note updated successfully.",
            "data": {
                "id": updated_note.id,
                "title": updated_note.title,
                "content": updated_note.content,
                "created_at": str(updated_note.created_at),
            },
        }

    except HTTPException as e:
        return {
            "success": False,
            "message": e.detail,
            "data": None,
        }

    finally:
        db.close()


@tool
def delete_note_tool(note_id: int):
    """
    Delete a note by its ID.

    Use this tool only when the user explicitly wants
    to delete or remove a note.
    """

    db = SessionLocal()

    try:
        result = delete_note(db, note_id)

        return {
            "success": True,
            "message": result["message"],
            "data": None,
        }

    except HTTPException as e:
        return {
            "success": False,
            "message": e.detail,
            "data": None,
        }

    finally:
        db.close()