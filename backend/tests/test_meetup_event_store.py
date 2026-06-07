from unittest.mock import MagicMock, patch

from app.services.event_listing import EventListing
from app.services.meetup_event_store import (
    listing_to_row,
    row_to_listing,
    search_stored_events,
    upsert_listings,
    _normalize_meetup_event_id,
)
from app.services.meetup_sync_service import sync_meetup_events


def _listing(event_id: str, title: str) -> EventListing:
    return EventListing(
        id=f"meetup:{event_id}",
        title=title,
        start="2026-06-10T19:00:00-07:00",
        end=None,
        venue="Community Hall",
        city="Cupertino",
        region="CA",
        url=f"https://www.meetup.com/example/events/{event_id}/",
        is_free=None,
        cost_summary=None,
        source="meetup",
    )


def test_normalize_meetup_event_id() -> None:
    assert _normalize_meetup_event_id("meetup:123") == "123"
    assert _normalize_meetup_event_id("123") == "123"


def test_listing_row_roundtrip() -> None:
    listing = _listing("42", "Tech Night")
    row = listing_to_row(listing, search_location="cupertino", search_keywords="")
    assert row.meetup_event_id == "42"
    assert row.title == "Tech Night"
    assert row.search_location == "cupertino"
    assert row_to_listing(row).title == "Tech Night"


def test_upsert_listings_counts_saved_and_skipped() -> None:
    db = MagicMock()
    db.scalars.return_value.all.return_value = ["1"]

    saved, skipped = upsert_listings(
        db,
        [_listing("1", "Existing"), _listing("2", "New")],
        search_location="cupertino",
        search_keywords="",
    )

    assert saved == 1
    assert skipped == 1
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_sync_meetup_events_streams_progress() -> None:
    db = MagicMock()
    batches = [
        (1, [_listing("1", "A")]),
        (2, [_listing("2", "B"), _listing("3", "C")]),
    ]

    with patch(
        "app.services.meetup_sync_service.iter_meetup_listing_batches",
        return_value=iter(batches),
    ), patch(
        "app.services.meetup_sync_service.upsert_listings",
        side_effect=[(1, 0), (2, 0)],
    ):
        updates = list(sync_meetup_events(db, location="cupertino"))

    assert updates[0]["type"] == "started"
    assert updates[1]["type"] == "progress"
    assert updates[1]["saved"] == 1
    assert updates[2]["saved"] == 3
    assert updates[-1]["type"] == "complete"
    assert updates[-1]["fetched"] == 3


def test_search_stored_events_applies_filters() -> None:
    db = MagicMock()
    row = listing_to_row(
        _listing("9", "Bay Hackathon"),
        search_location="cupertino",
        search_keywords="",
    )
    db.scalars.return_value.all.return_value = [row]

    with patch(
        "app.services.meetup_event_store.count_stored_events",
        return_value=1,
    ), patch(
        "app.services.meetup_event_store.apply_embedding",
    ):
        payload = search_stored_events(
            db,
            location="cupertino",
            keywords="hackathon",
            max_results=10,
        )

    assert payload["count"] == 1
    assert payload["events"][0]["title"] == "Bay Hackathon"
