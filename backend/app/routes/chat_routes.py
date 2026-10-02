# backend/app/routes/chat_routes.py

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from pydantic import BaseModel, Field
from backend.app.core.rate_limit import limiter

from backend.app.database.models import User
from backend.app.api.deps import get_current_user
from backend.app.ai.agent import build_assistant
from backend.app.ai.memory import get_thread_config
import base64

from backend.app.ai.voice import transcribe_audio, synthesize_speech

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)  # caps token cost per call


class ChatResponse(BaseModel):
    reply: str


class VoiceChatResponse(BaseModel):
    transcript: str
    reply: str
    audio_base64: str
    audio_format: str = "mp3"


@router.post("/", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat(
    request: Request,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    assistant = build_assistant(user_id=current_user.id)
    thread_config = get_thread_config(current_user.id)

    try:
        result = assistant.invoke(
            {"messages": [("user", body.message)]},
            config=thread_config,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant failed to respond: {str(e)}")

    reply_text = result["messages"][-1].content
    return ChatResponse(reply=reply_text)


@router.post("/voice", response_model=VoiceChatResponse)
@limiter.limit("5/minute")
async def voice_chat(
    request: Request,
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="No audio data received.")

    try:
        transcript = transcribe_audio(audio_bytes, filename=audio.filename or "audio.wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not transcribe audio: {str(e)}")

    if not transcript.strip():
        raise HTTPException(
            status_code=400, detail="Could not understand any speech in the audio."
        )

    assistant = build_assistant(user_id=current_user.id)
    thread_config = get_thread_config(current_user.id)

    try:
        result = assistant.invoke(
            {"messages": [("user", transcript)]},
            config=thread_config,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant failed to respond: {str(e)}")

    reply_text = result["messages"][-1].content

    try:
        audio_reply_bytes = synthesize_speech(reply_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not synthesize speech: {str(e)}")

    return VoiceChatResponse(
        transcript=transcript,
        reply=reply_text,
        audio_base64=base64.b64encode(audio_reply_bytes).decode("utf-8"),
        audio_format="mp3",
    )