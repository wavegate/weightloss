from datetime import date

from app.schemas.event_preferences import EventPreferencesUpsert
from app.services.event_preferences_service import (
    build_keywords_from_preferences,
    filter_listings_by_preferences,
    merge_preferences_update,
    resolve_search_params,
)
from app.services.eventbrite_service import EventListing


def _row(**overrides):
    base = EventPreferencesUpsert(
        home_location="cupertino",
        distance_miles=25,
        default_timing="weekend",
        free_only=True,
        max_price_usd=30,
        interest_keywords="startup",
        categories=["tech", "networking"],
    )
    class FakeRow:
        pass

    row = FakeRow()
    for key, value in base.model_dump().items():
        setattr(row, key, value)
    for key, value in overrides.items():
        setattr(row, key, value)
    return row


def test_merge_preferences_update_partial() -> None:
    row = _row(interest_keywords="startup", home_location="cupertino")
    payload = merge_preferences_update(
        row,
        home_location="san-francisco",
        interest_keywords="hackathon",
    )
    assert payload.home_location == "san-francisco"
    assert payload.interest_keywords == "hackathon"
    assert payload.default_timing == "weekend"
    assert "tech" in payload.categories


def test_build_keywords_from_preferences() -> None:
    row = _row()
    keywords = build_keywords_from_preferences(row)
    assert "startup" in keywords
    assert "tech" in keywords


def test_resolve_search_params_uses_saved_defaults() -> None:
    resolved = resolve_search_params(_row(), location="", keywords="", timing="")
    assert resolved.location == "cupertino"
    assert resolved.timing == "weekend"
    assert resolved.free_only is True
    assert resolved.preferences_applied is True
    assert "startup" in resolved.keywords


def test_upsert_coerces_incomplete_date_range() -> None:
    payload = EventPreferencesUpsert(
        default_timing="date-range",
        start_date=None,
        end_date=None,
    )
    assert payload.default_timing == "upcoming"
    assert payload.start_date is None
    assert payload.end_date is None


def test_resolve_search_params_date_range() -> None:
    row = _row(
        default_timing="date-range",
        start_date=date(2026, 6, 10),
        end_date=date(2026, 6, 15),
    )
    resolved = resolve_search_params(row, location="", keywords="", timing="")
    assert resolved.timing == "date-range"
    assert resolved.start_date == date(2026, 6, 10)
    assert resolved.end_date == date(2026, 6, 15)


def test_filter_listings_by_date_range() -> None:
    listings = [
        EventListing(
            id="a",
            title="June Show",
            start="2026-06-10T19:00:00",
            end=None,
            venue=None,
            city=None,
            region=None,
            url="https://example.com/a",
            is_free=None,
            cost_summary=None,
            source="meetup",
        ),
        EventListing(
            id="b",
            title="July Show",
            start="2026-07-01T19:00:00",
            end=None,
            venue=None,
            city=None,
            region=None,
            url="https://example.com/b",
            is_free=None,
            cost_summary=None,
            source="meetup",
        ),
    ]
    filtered = filter_listings_by_preferences(
        listings,
        free_only=False,
        max_price_usd=None,
        categories=[],
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 30),
    )
    assert len(filtered) == 1
    assert filtered[0].title == "June Show"


def test_filter_listings_by_keywords() -> None:
    listings = [
        EventListing(
            id="a",
            title="Startup Mixer",
            start=None,
            end=None,
            venue=None,
            city=None,
            region=None,
            url="https://example.com/a",
            is_free=None,
            cost_summary=None,
            source="luma",
        ),
        EventListing(
            id="b",
            title="Weekend Hackathon",
            start=None,
            end=None,
            venue=None,
            city=None,
            region=None,
            url="https://example.com/b",
            is_free=None,
            cost_summary=None,
            source="luma",
        ),
    ]
    filtered = filter_listings_by_preferences(
        listings,
        free_only=False,
        max_price_usd=None,
        categories=["music"],
        keywords="hackathon",
    )
    assert len(filtered) == 1
    assert filtered[0].title == "Weekend Hackathon"


def test_filter_listings_by_preferences_free_and_category() -> None:
    listings = [
        EventListing(
            id="a",
            title="AI Startup Meetup",
            start=None,
            end=None,
            venue=None,
            city=None,
            region=None,
            url="https://example.com/a",
            is_free=True,
            cost_summary="free",
            source="meetup",
        ),
        EventListing(
            id="b",
            title="Paid Jazz Night",
            start=None,
            end=None,
            venue=None,
            city=None,
            region=None,
            url="https://example.com/b",
            is_free=False,
            cost_summary="45 USD",
            source="eventbrite",
        ),
    ]
    filtered = filter_listings_by_preferences(
        listings,
        free_only=True,
        max_price_usd=None,
        categories=["tech"],
    )
    assert len(filtered) == 1
    assert filtered[0].title.startswith("AI")
