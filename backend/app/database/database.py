import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Retrieve database connection string from environment or fall back to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./assistant.db")

# Automatically format Postgres URLs to explicitly use the psycopg (v3) driver
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Configure engine arguments based on driver
engine_options = {}
if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

# Initialize SQLAlchemy Engine
engine = create_engine(DATABASE_URL, **engine_options)

# Database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Declarative base class for models
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