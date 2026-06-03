import json
import re
import ssl
import urllib.error
import urllib.request

import certifi

from app.config import get_settings

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
DEFAULT_MODEL_ID = "eleven_turbo_v2_5"
MAX_TTS_CHARS = 4_000


def _https_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def plain_text_for_speech(text: str) -> str:
    """Strip markdown-ish formatting before TTS."""
    cleaned = text
    cleaned = re.sub(r"```[\s\S]*?```", "", cleaned)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"[#*_~]+", "", cleaned)
    return " ".join(cleaned.split())


def synthesize_speech(text: str) -> bytes:
    settings = get_settings()
    api_key = settings.elevenlabs_api_key
    voice_id = settings.elevenlabs_voice_id
    if not api_key or not voice_id:
        raise RuntimeError(
            "Voice is not configured. Set ELEVENLABS_API_KEY and VOICE_ID.",
        )

    spoken = plain_text_for_speech(text).strip()
    if not spoken:
        raise ValueError("Nothing to speak after removing formatting.")

    if len(spoken) > MAX_TTS_CHARS:
        spoken = spoken[:MAX_TTS_CHARS]

    payload = json.dumps(
        {
            "text": spoken,
            "model_id": DEFAULT_MODEL_ID,
        },
    ).encode("utf-8")

    request = urllib.request.Request(
        ELEVENLABS_TTS_URL.format(voice_id=voice_id),
        data=payload,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=90,
            context=_https_context(),
        ) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(
            f"ElevenLabs request failed ({exc.code}): {detail}",
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"ElevenLabs request failed: {exc.reason}") from exc
