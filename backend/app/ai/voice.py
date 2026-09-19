# backend/app/ai/voice.py
#
# Requires: pip install openai python-multipart
# (openai is likely already installed via langchain_openai, but confirm)
#
# Uses the OpenAI Whisper API for speech-to-text and the OpenAI TTS API
# for text-to-speech — same account/API key as llm.py already uses.

import io

from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from the environment, same as ChatOpenAI does


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """
    Convert recorded speech into text using Whisper.

    filename matters even though we're passing raw bytes — the OpenAI
    client uses its extension to infer the audio format (wav, mp3, m4a,
    etc.), so pass through whatever filename the client actually uploaded.
    """

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )

    return transcript.text


def synthesize_speech(text: str, voice: str = "alloy") -> bytes:
    """
    Convert the assistant's text reply into spoken audio (MP3 bytes).

    voice options as of writing: alloy, echo, fable, onyx, nova, shimmer.
    Pick whichever fits the assistant's personality — "alloy" is a
    reasonable neutral default.
    """

    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
    )

    return response.content