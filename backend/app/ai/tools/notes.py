# backend/app/ai/tools/notes.py
#
# Tools are built PER USER via build_note_tools(user_id). See tasks.py for
# the full explanation of why.

from fastapi import HTTPException
from langchain_core.tools import tool

from backend.app.schemas.note_schema import NoteCreate, NoteUpdate
from backend.app.services.note_service import (
    create_note,
    get_notes,
    search_notes,
    update_note,
    delete_note,
)
from backend.app.database.database import SessionLocal


def build_note_tools(user_id: int) -> list:
    """Build the set of note tools scoped to a single user. Call this once
    per chat session/request with the authenticated user's id."""

    @tool
    def create_note_tool(content: str, title: str | None = None):
        """
        Save information the user wants to keep for later reference, with
        no action or reminder implied.

        Use ONLY for things like "save this recipe", "note that my wifi
        password is X", "jot this down: [info]". Do NOT use this for
        anything the user needs to DO — use create_task_tool instead.

        content: the information to save — required, cannot be empty
        title: optional short label for the note
        """

        if not content.strip():
            return {
                "success": False,
                "message": "Note content cannot be empty.",
                "data": None,
            }

        db = SessionLocal()

        try:
            note = NoteCreate(title=title, content=content)
            created_note = create_note(db, note, user_id=user_id)

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

        except Exception as e:
            return {
                "success": False,
                "message": f"Could not create note: {str(e)}",
                "data": None,
            }

        finally:
            db.close()

    @tool
    def get_notes_tool():
        """
        Retrieve ALL of the current user's notes, unfiltered.

        Use this ONLY when the user wants their full list with no filter, e.g.
        "show me all my notes" or "what notes do I have".

        If the user mentions a keyword or topic, use search_notes_tool
        instead — it's more precise and cheaper.

        Do not modify any notes.
        """

        db = SessionLocal()

        try:
            notes = get_notes(db, user_id=user_id)

            if not notes:
                return {"success": True, "message": "No notes found.", "data": []}

            return {
                "success": True,
                "message": f"Retrieved {len(notes)} note(s).",
                "data": [
                    {
                        "id": n.id,
                        "title": n.title,
                        "content": n.content,
                        "created_at": str(n.created_at),
                    }
                    for n in notes
                ],
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Could not retrieve notes: {str(e)}",
                "data": None,
            }

        finally:
            db.close()

    @tool
    def search_notes_tool(keyword: str):
        """
        Search the current user's notes by keyword, matched against title
        and content (case-insensitive). Use this whenever the user's
        request implies a filter, e.g. "find my note about wifi".

        This is also the right tool to call FIRST when the user wants to
        update or delete a note by title/content rather than by ID. If
        more than one result plausibly matches, list them and ask which
        one before acting.

        keyword: required search term.
        """

        if not keyword.strip():
            return {
                "success": False,
                "message": "Please provide a keyword to search for.",
                "data": None,
            }

        db = SessionLocal()

        try:
            notes = search_notes(db, user_id=user_id, keyword=keyword)

            if not notes:
                return {"success": True, "message": "No matching notes found.", "data": []}

            return {
                "success": True,
                "message": f"Found {len(notes)} matching note(s).",
                "data": [
                    {
                        "id": n.id,
                        "title": n.title,
                        "content": n.content,
                        "created_at": str(n.created_at),
                    }
                    for n in notes
                ],
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Could not search notes: {str(e)}",
                "data": None,
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
        Update the current user's note — title, content, or both. Only
        provided fields are changed.

        Requires note_id. If the user referred to the note by title/content
        only, call search_notes_tool first to find the matching note_id.
        If more than one plausibly matches, ask which one before calling
        this tool.
        """

        db = SessionLocal()

        try:
            note_data = NoteUpdate(title=title, content=content)
            updated_note = update_note(db, note_id, note_data, user_id=user_id)

            return {
                "success": True,
                "message": "Note updated successfully.",
                "data": {
                    "id": updated_note.id,
                    "title": updated_note.title,
                    "content": updated_note.content,
                },
            }

        except HTTPException as e:
            return {"success": False, "message": e.detail, "data": None}

        except Exception as e:
            return {
                "success": False,
                "message": f"Could not update note: {str(e)}",
                "data": None,
            }

        finally:
            db.close()

    @tool
    def delete_note_tool(note_id: int):
        """
        Permanently delete the current user's note by ID. Cannot be undone.

        Use ONLY when the user explicitly wants to delete or remove a note.
        If they referred to it by title/content only and more than one note
        plausibly matches, call search_notes_tool first and confirm the
        exact note_id before deleting.
        """

        db = SessionLocal()

        try:
            result = delete_note(db, note_id, user_id=user_id)
            return {"success": True, "message": result["message"], "data": None}

        except HTTPException as e:
            return {"success": False, "message": e.detail, "data": None}

        except Exception as e:
            return {
                "success": False,
                "message": f"Could not delete note: {str(e)}",
                "data": None,
            }

        finally:
            db.close()

    return [
        create_note_tool,
        get_notes_tool,
        search_notes_tool,
        update_note_tool,
        delete_note_tool,
    ]