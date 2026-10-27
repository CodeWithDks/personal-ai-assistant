# tests/test_chat_voice.py
#
# Tests for the /chat/voice route's own logic. Whisper, TTS and the agent are
# all mocked, so nothing here calls OpenAI.

import inspect

# pyrefly: ignore [missing-import]
import pytest

# pyrefly: ignore [missing-import]
from backend.app.routes import chat_routes as chat_routes_module


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeAssistant:
    def __init__(self, reply="Done."):
        self.reply = reply

    def invoke(self, messages, config=None):
        return {"messages": [_FakeMessage(self.reply)]}


@pytest.fixture
def voice_mocks(monkeypatch):
    """Mocks Whisper, TTS and the agent. Returns a dict recording what the
    route passed to Whisper."""
    calls = {}

    def fake_transcribe(audio_bytes, filename="audio.wav"):
        calls["filename"] = filename
        calls["size"] = len(audio_bytes)
        return "add a task to buy milk"

    monkeypatch.setattr(chat_routes_module, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(chat_routes_module, "synthesize_speech", lambda text: b"fake-mp3-bytes")
    monkeypatch.setattr(chat_routes_module, "build_assistant", lambda user_id: _FakeAssistant())
    return calls


def _upload(client, auth_headers, name="recording.webm", content=b"x" * 100, content_type="audio/webm"):
    return client.post(
        "/chat/voice",
        files={"audio": (name, content, content_type)},
        headers=auth_headers,
    )


def test_voice_route_is_a_plain_def():
    """Regression guard: an `async def` route running blocking OpenAI calls
    freezes the whole server. It must stay a plain `def`."""
    assert not inspect.iscoroutinefunction(chat_routes_module.voice_chat)


def test_voice_requires_auth(client):
    response = client.post("/chat/voice", files={"audio": ("recording.webm", b"x", "audio/webm")})
    assert response.status_code == 401


def test_voice_happy_path_webm_keeps_extension(client, auth_headers, voice_mocks):
    response = _upload(client, auth_headers, "recording.webm", content_type="audio/webm;codecs=opus")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["transcript"] == "add a task to buy milk"
    assert body["reply"] == "Done."
    assert body["audio_format"] == "mp3"
    assert voice_mocks["filename"] == "recording.webm"


def test_voice_safari_mp4_keeps_extension(client, auth_headers, voice_mocks):
    response = _upload(client, auth_headers, "recording.mp4", content_type="audio/mp4")
    assert response.status_code == 200, response.text
    assert voice_mocks["filename"] == "recording.mp4"


def test_voice_extension_inferred_from_content_type(client, auth_headers, voice_mocks):
    response = _upload(client, auth_headers, "blob", content_type="audio/mp4")
    assert response.status_code == 200, response.text
    assert voice_mocks["filename"] == "recording.mp4"


def test_voice_rejects_non_audio_content_type(client, auth_headers, voice_mocks):
    response = _upload(client, auth_headers, "evil.webm", content_type="text/html")
    assert response.status_code == 415


def test_voice_rejects_unknown_extension(client, auth_headers, voice_mocks):
    response = _upload(client, auth_headers, "clip.exe", content_type="audio/unknown")
    assert response.status_code == 415


def test_voice_rejects_empty_file(client, auth_headers, voice_mocks):
    response = _upload(client, auth_headers, content=b"")
    assert response.status_code == 400


def test_voice_rejects_oversized_file(client, auth_headers, voice_mocks):
    too_big = b"x" * (chat_routes_module.MAX_AUDIO_BYTES + 1)
    response = _upload(client, auth_headers, content=too_big)
    assert response.status_code == 413
    assert "size" not in voice_mocks  # Whisper was never called


def test_voice_accepts_file_exactly_at_the_limit(client, auth_headers, voice_mocks):
    at_limit = b"x" * chat_routes_module.MAX_AUDIO_BYTES
    response = _upload(client, auth_headers, content=at_limit)
    assert response.status_code == 200, response.text


def test_voice_does_not_leak_internal_errors(client, auth_headers, monkeypatch):
    def boom(audio_bytes, filename="audio.wav"):
        raise RuntimeError("secret-internal-detail postgresql://user:pw@host")

    monkeypatch.setattr(chat_routes_module, "transcribe_audio", boom)
    response = _upload(client, auth_headers)
    assert response.status_code == 500
    assert "secret-internal-detail" not in response.text
    assert "postgresql" not in response.text


@pytest.mark.parametrize("content", ["", "   ", None, [], [{"type": "text", "text": "  "}]])
def test_extract_reply_falls_back_when_empty(content):
    result = {"messages": [_FakeMessage(content)]}
    assert chat_routes_module._extract_reply(result) == chat_routes_module.FALLBACK_REPLY


def test_extract_reply_joins_content_blocks():
    result = {"messages": [_FakeMessage([{"type": "text", "text": "Hello "}, {"type": "text", "text": "there"}])]}
    assert chat_routes_module._extract_reply(result) == "Hello there"