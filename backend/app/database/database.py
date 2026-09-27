import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./assistant.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

engine_options = {}
if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_options)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Standard declarative base class for your models to inherit from
Base = declarative_base()

def get_db():
    """Dependency provider for FastAPI route operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def reset_db_development_only():
    """
    Call this function only during active local testing.
    Drops existing mismatched tables and builds clean structures.
    """
    import logging
    logging.warning("Resetting development database schemas...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
