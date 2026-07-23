from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# The database file sits at the backend root level
DATABASE_URL = "sqlite:///./assistant.db"

engine = create_engine(
    DATABASE_URL,
    # Crucial argument for SQLite to handle multi-threaded FastAPI contexts
    connect_args={'check_same_thread': False}
)

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
