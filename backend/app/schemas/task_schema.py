# backend/app/schemas/task_schema.py

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class TaskStatus(str, Enum):
    """Allowed task statuses. Using an enum instead of a raw string prevents
    typos or casing drift (e.g. 'Pending' vs 'pending') from silently
    creating an unmatched status."""

    PENDING = "pending"
    COMPLETED = "completed"


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    due_date: datetime | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    due_date: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)