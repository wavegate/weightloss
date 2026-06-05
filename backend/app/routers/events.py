from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.clerk import CurrentUserId
from app.database import get_db
from app.schemas.event_preferences import EventPreferencesRead, EventPreferencesUpsert
from app.services.event_preferences_service import (
    get_or_create_preferences,
    preference_options_payload,
    preferences_to_read,
    upsert_preferences,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/preferences/options")
def get_event_preference_options() -> dict:
    return preference_options_payload()


@router.get("/preferences", response_model=EventPreferencesRead)
def get_event_preferences(
    db: Session = Depends(get_db),
    user_id: str = CurrentUserId,
) -> EventPreferencesRead:
    row = get_or_create_preferences(db, user_id)
    return preferences_to_read(row)


@router.put("/preferences", response_model=EventPreferencesRead)
def put_event_preferences(
    payload: EventPreferencesUpsert,
    db: Session = Depends(get_db),
    user_id: str = CurrentUserId,
) -> EventPreferencesRead:
    row = upsert_preferences(db, user_id, payload)
    return preferences_to_read(row)
