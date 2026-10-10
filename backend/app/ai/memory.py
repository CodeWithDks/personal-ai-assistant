# backend/app/ai/memory.py
#
# Conversation memory for the agent (LangGraph checkpointer).
#
# - If DATABASE_URL is Postgres (Supabase): checkpoints are stored there,
#   so chat history survives restarts/redeploys on ephemeral hosts.
# - Otherwise: falls back to a local SQLite file (dev/tests only).

import logging
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CHECKPOINT_DB_PATH = Path(__file__).resolve().parents[2] / "chat_memory.db"


def _postgres_conninfo() -> str | None:
    """Return a plain libpq-style URL if DATABASE_URL is Postgres, else None."""
    url = os.getenv("DATABASE_URL", "")
    if url.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
        # psycopg_pool wants a plain postgresql:// URL, not the SQLAlchemy
        # "+psycopg" driver form.
        url = url.replace("postgresql+psycopg://", "postgresql://", 1)
        url = url.replace("postgres://", "postgresql://", 1)
        return url
    return None


def _create_postgres_checkpointer(conninfo: str):
    # pyrefly: ignore [missing-import]
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg.rows import dict_row
    # pyrefly: ignore [missing-import]
    from psycopg_pool import ConnectionPool

    # These connection kwargs are REQUIRED by PostgresSaver:
    #   autocommit=True  -> setup() and writes must commit on their own
    #   row_factory=dict_row -> the saver reads rows as dicts
    #   prepare_threshold=0 -> avoids prepared-statement problems behind poolers
    pool = ConnectionPool(
        conninfo=conninfo,
        min_size=1,
        max_size=5,  # keep small: Supabase free tier has limited connections
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
        check=ConnectionPool.check_connection,  # drop dead connections
        open=True,
    )

    checkpointer = PostgresSaver(pool)
    checkpointer.setup()  # creates checkpoint tables on first run, no-op after
    logger.info("Chat memory checkpointer initialized (Postgres)")
    return checkpointer


def _create_sqlite_checkpointer():
    from langgraph.checkpoint.sqlite import SqliteSaver

    CHECKPOINT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(CHECKPOINT_DB_PATH), check_same_thread=False)
    checkpointer = SqliteSaver(connection)
    checkpointer.setup()
    logger.info("Chat memory checkpointer initialized at %s (SQLite)", CHECKPOINT_DB_PATH)
    return checkpointer


def _create_checkpointer():
    conninfo = _postgres_conninfo()
    if conninfo:
        return _create_postgres_checkpointer(conninfo)
    return _create_sqlite_checkpointer()


# One checkpointer, reused for the lifetime of the app process.
_checkpointer = _create_checkpointer()


def get_checkpointer():
    """The shared checkpointer instance."""
    return _checkpointer


def get_thread_config(user_id: int) -> dict:
    """
    Scope conversation memory to one user's ongoing thread. Pass as the
    `config` argument to assistant.invoke(...).

    One thread per user for now. For multiple conversations per user later:
    f"user-{user_id}-conv-{conversation_id}".
    """
    return {"configurable": {"thread_id": f"user-{user_id}"}}