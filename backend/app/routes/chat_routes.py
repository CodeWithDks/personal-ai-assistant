# backend/app/routes/chat_routes.py

import base64
import logging
import os
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from pydantic import BaseModel, Field

from backend.app.core.rate_limit import limiter
from backend.app.database.models import User
from backend.app.api.deps import get_current_user
from backend.app.ai.agent import build_assistant
from backend.app.ai.memory import get_thread_config
from backend.app.ai.voice import transcribe_audio, synthesize_speech

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

# --- Voice upload limits -----------------------------------------------------
MAX_AUDIO_BYTES = 5 * 1024 * 1024  # 5 MB per voice message

# Formats Whisper accepts. Browsers send recording.webm (Chrome/Firefox/Android)
# or recording.mp4 (Safari/iOS).
ALLOWED_AUDIO_EXTENSIONS = {
    "webm", "mp4", "m4a", "mp3", "mpeg", "mpga", "wav", "ogg", "oga", "flac",
}

# Some browsers label audio-only webm/mp4 containers as video/*, so those two
# (and a generic binary type) are tolerated alongside anything starting audio/.
EXTRA_ALLOWED_CONTENT_TYPES = {"video/webm", "video/mp4", "application/octet-stream"}

EXTENSION_BY_CONTENT_TYPE = {
    "audio/webm": "webm", "video/webm": "webm",
    "audio/mp4": "mp4", "video/mp4": "mp4",
    "audio/x-m4a": "m4a", "audio/m4a": "m4a",
    "audio/mpeg": "mp3", "audio/mp3": "mp3",
    "audio/wav": "wav", "audio/x-wav": "wav", "audio/wave": "wav",
    "audio/ogg": "ogg", "audio/flac": "flac",
}

FALLBACK_REPLY = "Sorry, I couldn't come up with a reply. Please try again."


def _audio_filename(upload: UploadFile) -> str:
    """
    Validate the upload's type and return a safe filename that keeps the real
    extension (Whisper uses the extension to detect the audio format).
    """
    content_type = (upload.content_type or "").split(";")[0].strip().lower()
    if not (content_type.startswith("audio/") or content_type in EXTRA_ALLOWED_CONTENT_TYPES):
        raise HTTPException(status_code=415, detail="Unsupported audio format.")

    extension = os.path.splitext(upload.filename or "")[1].lower().lstrip(".")
    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        extension = EXTENSION_BY_CONTENT_TYPE.get(content_type, "")
    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Unsupported audio format.")

    return f"recording.{extension}"


def _extract_reply(result: dict) -> str:
    """Always return a non-empty plain string from the agent's final message."""
    content = result["messages"][-1].content
    if isinstance(content, list):  # some models return content blocks
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    content = (content or "").strip()
    return content or FALLBACK_REPLY


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
    except Exception:
        logger.exception("Chat failed for user_id=%s", current_user.id)
        raise HTTPException(
            status_code=500,
            detail="The assistant couldn't respond right now. Please try again."
        )

    return ChatResponse(reply=_extract_reply(result))


@router.post("/voice", response_model=VoiceChatResponse)
@limiter.limit("5/minute")
def voice_chat(
    request: Request,
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    # NOTE: this is a plain `def` on purpose. The calls below (Whisper, the
    # agent, TTS) are blocking; FastAPI runs plain-def routes in a worker
    # thread, so they can't freeze the event loop for other requests.
    filename = _audio_filename(audio)

    audio_bytes = audio.file.read(MAX_AUDIO_BYTES + 1)
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="No audio data received.")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio is too large (max 5 MB).")

    try:
        transcript = transcribe_audio(audio_bytes, filename=filename)
    except Exception:
        logger.exception("Transcription failed for user_id=%s", current_user.id)
        raise HTTPException(
            status_code=500,
            detail="Could not transcribe audio."
        )

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
    except Exception:
        logger.exception("Chat via voice failed for user_id=%s", current_user.id)
        raise HTTPException(
            status_code=500,
            detail="The assistant couldn't respond right now. Please try again."
        )

    reply_text = _extract_reply(result)

    try:
        audio_reply_bytes = synthesize_speech(reply_text)
    except Exception:
        logger.exception("Speech synthesis failed for user_id=%s", current_user.id)
        raise HTTPException(
            status_code=500,
            detail="Could not synthesize speech."
        )

    return VoiceChatResponse(
        transcript=transcript,
        reply=reply_text,
        audio_base64=base64.b64encode(audio_reply_bytes).decode("utf-8"),
        audio_format="mp3",
    )