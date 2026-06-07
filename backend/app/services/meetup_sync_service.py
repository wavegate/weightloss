"""Fetch Meetup listings and persist them with progress updates."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from sqlalchemy.orm import Session

from app.services.meetup_event_store import upsert_listings
from app.services.meetup_service import iter_meetup_listing_batches


def sync_meetup_events(
    db: Session,
    *,
    location: str,
    keywords: str = "",
) -> Iterator[dict[str, Any]]:
    loc = location.strip().lower() or "cupertino"
    keyword_value = keywords.strip()
    total_fetched = 0
    total_saved = 0
    total_skipped = 0

    yield {
        "type": "started",
        "page": 0,
        "fetched": 0,
        "saved": 0,
        "skipped": 0,
        "message": f"Starting Meetup sync for {loc}",
    }

    try:
        for page, batch in iter_meetup_listing_batches(
            location=loc,
            keywords=keyword_value,
        ):
            total_fetched += len(batch)
            saved, skipped = upsert_listings(
                db,
                batch,
                search_location=loc,
                search_keywords=keyword_value,
            )
            total_saved += saved
            total_skipped += skipped
            yield {
                "type": "progress",
                "page": page,
                "fetched": total_fetched,
                "saved": total_saved,
                "skipped": total_skipped,
                "message": (
                    f"Page {page}: {total_saved} saved, "
                    f"{total_skipped} already in database"
                ),
            }
    except Exception as exc:  # noqa: BLE001 — surface sync failures to client
        yield {
            "type": "error",
            "page": 0,
            "fetched": total_fetched,
            "saved": total_saved,
            "skipped": total_skipped,
            "message": str(exc),
        }
        return

    yield {
        "type": "complete",
        "page": 0,
        "fetched": total_fetched,
        "saved": total_saved,
        "skipped": total_skipped,
        "message": (
            f"Sync complete: {total_saved} new events saved, "
            f"{total_skipped} duplicates skipped ({total_fetched} fetched)"
        ),
    }
