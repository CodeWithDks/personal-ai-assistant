# backend/app/ai/agent.py

from datetime import datetime

from langchain.agents import create_agent

from backend.app.ai.llm import llm
from backend.app.ai.prompts import build_system_prompt
from backend.app.ai.tools.tasks import build_task_tools
from backend.app.ai.tools.notes import build_note_tools


def build_assistant(user_id: int):
    """
    Build a fresh agent instance scoped to one user, with the current
    date/time baked into its system prompt so it can resolve relative
    dates (today, tomorrow, 9pm) into real due_date values.

    Call this per chat request with the authenticated user's id.
    """

    tools = build_task_tools(user_id) + build_note_tools(user_id)

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=build_system_prompt(datetime.now()),
    )