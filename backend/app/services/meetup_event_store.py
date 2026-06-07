"""Persist and query synced Meetup events."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.meetup_event import MeetupEvent
from app.services.event_date_utils import parse_listing_start
from app.services.event_embedding_service import apply_embedding, embed_text
from app.services.event_filter import filter_listings
from app.services.event_listing import EventListing


def _normalize_meetup_event_id(listing_id: str) -> str:
    return listing_id.removeprefix("meetup:")


def _parse_start_at(start: str | None) -> datetime | None:
    if not start:
        return None
    parsed_date = parse_listing_start(start)
    if parsed_date is None:
        return None
    normalized = start.strip().replace(" ", "T")
    try:
        if normalized.endswith("Z"):
            return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        return datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.combine(parsed_date, datetime.min.time(), tzinfo=timezone.utc)


def listing_to_row(
    listing: EventListing,
    *,
    search_location: str,
    search_keywords: str,
) -> MeetupEvent:
    return MeetupEvent(
        meetup_event_id=_normalize_meetup_event_id(listing.id),
        title=listing.title,
        start_at=_parse_start_at(listing.start),
        venue=listing.venue,
        city=listing.city,
        region=listing.region,
        url=listing.url,
        is_free=listing.is_free,
        cost_summary=listing.cost_summary,
        source=listing.source,
        search_location=search_location,
        search_keywords=search_keywords,
        fetched_at=datetime.now(timezone.utc),
    )


def row_to_listing(row: MeetupEvent) -> EventListing:
    start = row.start_at.isoformat() if row.start_at else None
    return EventListing(
        id=f"meetup:{row.meetup_event_id}",
        title=row.title,
        start=start,
        end=None,
        venue=row.venue,
        city=row.city,
        region=row.region,
        url=row.url,
        is_free=row.is_free,
        cost_summary=row.cost_summary,
        source=row.source,
    )


def row_to_dict(row: MeetupEvent, *, reason: str | None = None) -> dict[str, Any]:
    payload = row_to_listing(row).to_dict()
    payload["meetup_event_id"] = row.meetup_event_id
    if reason:
        payload["reason"] = reason
    return payload


def upsert_listings(
    db: Session,
    listings: list[EventListing],
    *,
    search_location: str,
    search_keywords: str,
    embed_new: bool = True,
) -> tuple[int, int]:
    """Insert new events; skip rows that already exist. Returns (saved, skipped)."""
    if not listings:
        return 0, 0

    ids = [_normalize_meetup_event_id(listing.id) for listing in listings]
    existing_ids = set(
        db.scalars(
            select(MeetupEvent.meetup_event_id).where(
                MeetupEvent.meetup_event_id.in_(ids)
            )
        ).all()
    )

    saved = 0
    skipped = 0
    now = datetime.now(timezone.utc)
    new_rows: list[MeetupEvent] = []
    for listing in listings:
        event_id = _normalize_meetup_event_id(listing.id)
        if event_id in existing_ids:
            skipped += 1
            continue
        row = listing_to_row(
            listing,
            search_location=search_location,
            search_keywords=search_keywords,
        )
        row.created_at = now
        db.add(row)
        new_rows.append(row)
        existing_ids.add(event_id)
        saved += 1

    if embed_new:
        for row in new_rows:
            try:
                apply_embedding(row)
            except Exception:  # noqa: BLE001 — embedding failure should not block sync
                pass

    db.commit()
    return saved, skipped


def count_stored_events(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(MeetupEvent)) or 0


def _rows_for_location(
    db: Session,
    location: str,
    *,
    limit: int = 2000,
) -> list[MeetupEvent]:
    loc = location.strip().lower() or "cupertino"
    return list(
        db.scalars(
            select(MeetupEvent)
            .where(MeetupEvent.search_location == loc)
            .order_by(MeetupEvent.start_at.asc().nulls_last())
            .limit(limit)
        ).all()
    )


def search_stored_events(
    db: Session,
    *,
    location: str = "cupertino",
    keywords: str = "",
    start_date: date | None = None,
    end_date: date | None = None,
    free_only: bool = False,
    max_price_usd: float | None = None,
    max_results: int = 30,
) -> dict[str, Any]:
    loc = location.strip().lower() or "cupertino"
    rows = _rows_for_location(db, loc)
    listings = [row_to_listing(row) for row in rows]
    filtered = filter_listings(
        listings,
        keywords=keywords,
        start_date=start_date,
        end_date=end_date,
        free_only=free_only,
        max_price_usd=max_price_usd,
    )[:max_results]
    filtered_ids = {_normalize_meetup_event_id(item.id) for item in filtered}

    return {
        "search_type": "keyword",
        "location": loc,
        "keywords": keywords.strip(),
        "source": "database",
        "total_in_database": count_stored_events(db),
        "matching_location": len(listings),
        "count": len(filtered),
        "events": [
            row_to_dict(row)
            for row in rows
            if row.meetup_event_id in filtered_ids
        ],
    }


def list_stored_events(
    db: Session,
    *,
    location: str = "cupertino",
    start_date: date | None = None,
    end_date: date | None = None,
    max_results: int = 200,
) -> dict[str, Any]:
    loc = location.strip().lower() or "cupertino"
    rows = _rows_for_location(db, loc, limit=max_results * 2)
    listings = [row_to_listing(row) for row in rows]
    filtered_rows = filter_listings(
        listings,
        start_date=start_date,
        end_date=end_date,
    )[:max_results]
    filtered_ids = {_normalize_meetup_event_id(item.id) for item in filtered_rows}

    return {
        "search_type": "list",
        "location": loc,
        "source": "database",
        "count": len(filtered_rows),
        "events": [
            row_to_dict(row)
            for row in rows
            if row.meetup_event_id in filtered_ids
        ],
    }


def vector_search_stored_events(
    db: Session,
    *,
    query: str,
    location: str = "cupertino",
    start_date: date | None = None,
    end_date: date | None = None,
    max_results: int = 30,
) -> dict[str, Any]:
    loc = location.strip().lower() or "cupertino"
    trimmed = query.strip()
    if not trimmed:
        raise ValueError("query is required for vector search")

    query_vector = embed_text(trimmed)
    rows = list(
        db.scalars(
            select(MeetupEvent)
            .where(MeetupEvent.search_location == loc)
            .where(MeetupEvent.embedding.is_not(None))
            .order_by(MeetupEvent.embedding.cosine_distance(query_vector))
            .limit(max(max_results * 3, 60))
        ).all()
    )

    listings = [row_to_listing(row) for row in rows]
    filtered = filter_listings(
        listings,
        start_date=start_date,
        end_date=end_date,
    )[:max_results]
    filtered_ids = {_normalize_meetup_event_id(item.id) for item in filtered}

    return {
        "search_type": "vector",
        "location": loc,
        "query": trimmed,
        "source": "database",
        "count": len(filtered),
        "events": [
            row_to_dict(row)
            for row in rows
            if row.meetup_event_id in filtered_ids
        ],
    }


def get_events_by_ids(db: Session, event_ids: list[str]) -> list[MeetupEvent]:
    normalized = [_normalize_meetup_event_id(event_id) for event_id in event_ids]
    if not normalized:
        return []
    return list(
        db.scalars(
            select(MeetupEvent).where(MeetupEvent.meetup_event_id.in_(normalized))
        ).all()
    )
