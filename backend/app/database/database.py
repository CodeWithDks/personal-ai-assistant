# backend/app/core/database.py

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
else:
    engine_options.update(
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,   # test a connection before using it
        pool_recycle=300,     # replace connections idle > 5 min
    )

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