# backend/app/ai/memory.py
#
# Requires: pip install langgraph-checkpoint-sqlite
#
# This gives the agent real cross-message memory. Without it, every
# /chat call was a blank-slate agent — "delete the task I just made"
# couldn't work because nothing remembered "just made" referred to.

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

# Separate file from assistant.db — this only stores conversation
# checkpoints (message history per thread), never task/note data.
# Resolves to backend/chat_memory.db regardless of where the process is run from.
CHECKPOINT_DB_PATH = Path(__file__).resolve().parents[2] / "chat_memory.db"

# check_same_thread=False because FastAPI's sync routes run in a thread
# pool; SqliteSaver serializes access internally with its own lock, so
# this is safe at small-to-moderate scale. If you outgrow SQLite here
# (many concurrent users), swap this for a Postgres-backed checkpointer —
# get_checkpointer()'s return type is the only thing callers depend on.
_connection = sqlite3.connect(str(CHECKPOINT_DB_PATH), check_same_thread=False)
_checkpointer = SqliteSaver(_connection)
_checkpointer.setup()  # creates the checkpoint tables on first run, no-op after


def get_checkpointer() -> SqliteSaver:
    """The shared checkpointer instance. One connection, reused for the
    lifetime of the app process."""

    return _checkpointer


def get_thread_config(user_id: int) -> dict:
    """
    Build the LangGraph config that scopes conversation memory to one
    user's ongoing thread. Pass this as the `config` argument to
    assistant.invoke(...).

    Currently one thread per user (their entire chat history is one
    continuous conversation). If you later want multiple separate
    conversations per user (like ChatGPT's sidebar), change this to
    incorporate a conversation_id too: f"user-{user_id}-conv-{conversation_id}".
    """

    return {"configurable": {"thread_id": f"user-{user_id}"}}