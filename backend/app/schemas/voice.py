from pydantic import BaseModel, Field


class VoiceSpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8_000)
