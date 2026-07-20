from langchain.agents import create_agent

from backend.app.ai.llm import llm
from backend.app.ai.prompts import SYSTEM
from backend.app.ai.tools.tasks import (
    create_task_tool,
    get_tasks_tool,
    update_task_tool,
    delete_task_tool,
)
from backend.app.ai.tools.notes import (
    create_note_tool,
    get_notes_tool,
    update_note_tool,
    delete_note_tool,
)


tools=[
        create_task_tool,
        get_tasks_tool,
        update_task_tool,
        delete_task_tool,
        create_note_tool,
        get_notes_tool,
        update_note_tool,
        delete_note_tool,
    ]

assistant = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM,
)