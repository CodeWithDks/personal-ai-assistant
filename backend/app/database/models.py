from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from .database import Base
from sqlalchemy.orm import relationship


class User(Base):  # noqa: F821  (Base = your existing declarative base)
    __tablename__ = "users"
 
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
 
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")
 
 
class Task(Base):  # noqa: F821
    __tablename__ = "tasks"
 
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="pending")
    due_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
 
    # NEW — links each task to its owner
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="tasks")
 
 
class Note(Base):  # noqa: F821
    __tablename__ = "notes"
 
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
 
    # NEW — links each note to its owner
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="notes")