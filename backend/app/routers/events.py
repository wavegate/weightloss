import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.clerk import CurrentUserId
from app.database import get_db
from app.schemas.meetup_event import MeetupSyncRequest
from app.services.meetup_event_store import count_stored_events
from app.services.meetup_service import LOCATION_SLUGS
from app.services.meetup_sync_service import sync_meetup_events

router = APIRouter(prefix="/events", tags=["events"])

SYNC_LOCATIONS = sorted(
    {
        key
        for key in LOCATION_SLUGS
        if " " not in key and key != "online"
    }
)


@router.get("/locations")
def list_sync_locations() -> dict[str, list[str]]:
    return {"locations": SYNC_LOCATIONS}


@router.get("/count")
def get_stored_event_count(
    db: Session = Depends(get_db),
    _user_id: str = CurrentUserId,
) -> dict[str, int]:
    return {"count": count_stored_events(db)}


@router.post("/sync")
def sync_events(
    payload: MeetupSyncRequest,
    db: Session = Depends(get_db),
    _user_id: str = CurrentUserId,
) -> StreamingResponse:
    def event_stream():
        for update in sync_meetup_events(
            db,
            location=payload.location,
            keywords=payload.keywords,
        ):
            yield f"data: {json.dumps(update)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
