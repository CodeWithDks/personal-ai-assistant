from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):
    title : str | None = None
    content : str 


class NoteUpdate(BaseModel):
    title : str | None = None
    content : str | None = None


class NoteResponse(BaseModel):
    id  : int
    title : str | None
    content : str
    created_at : datetime

    model_config = ConfigDict(from_attributes=True)
