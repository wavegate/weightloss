import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.auth.clerk import CurrentUserId
from app.schemas.voice import VoiceSpeakRequest
from app.services.elevenlabs_service import synthesize_speech

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/speak")
async def speak(
    body: VoiceSpeakRequest,
    _user_id: str = CurrentUserId,
) -> Response:
    try:
        audio = await asyncio.to_thread(synthesize_speech, body.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return Response(content=audio, media_type="audio/mpeg")
