# backend/app/routes/chat_routes.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.database.models import User
from backend.app.api.deps import get_current_user
from backend.app.ai.agent import build_assistant
from backend.app.ai.memory import get_thread_config

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    assistant = build_assistant(user_id=current_user.id)
    thread_config = get_thread_config(current_user.id)

    try:
        result = assistant.invoke(
            {"messages": [("user", request.message)]},
            config=thread_config,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant failed to respond: {str(e)}")

    # create_agent (LangGraph-based) returns a dict with a "messages" list;
    # the last message is the assistant's final reply. If your installed
    # langchain version returns a different shape, check `result` here —
    # print(result) once during testing and adjust this line accordingly.
    reply_text = result["messages"][-1].content

    return ChatResponse(reply=reply_text)