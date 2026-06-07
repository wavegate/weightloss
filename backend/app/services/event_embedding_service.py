"""Generate and store embeddings for Meetup events."""

from __future__ import annotations

from openai import OpenAI

from app.config import get_settings
from app.models.meetup_event import MeetupEvent

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def build_embedding_text(row: MeetupEvent) -> str:
    parts = [
        row.title,
        row.venue,
        row.city,
        row.region,
        row.search_keywords,
        row.cost_summary,
    ]
    return " ".join(part.strip() for part in parts if part and part.strip())


def embed_text(text: str) -> list[float]:
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def apply_embedding(row: MeetupEvent) -> None:
    text = build_embedding_text(row)
    if not text:
        return
    row.embedding_text = text
    row.embedding_model = EMBEDDING_MODEL
    row.embedding = embed_text(text)
