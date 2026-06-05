from app.services.event_aggregator import aggregate_events, dedupe_listings
from app.services.eventbrite_service import EventListing


def _listing(
    *,
    source: str,
    title: str,
    start: str = "2026-06-10T19:00:00",
    venue: str = "Community Hall",
    url: str = "https://example.com/1",
) -> EventListing:
    return EventListing(
        id=f"{source}:1",
        title=title,
        start=start,
        end=None,
        venue=venue,
        city="Mountain View",
        region="CA",
        url=url,
        is_free=None,
        cost_summary=None,
        source=source,
    )


def test_dedupe_listings_prefers_richer_duplicate() -> None:
    sparse = _listing(source="meetup", title="Tech Night", venue="")
    rich = _listing(
        source="luma",
        title="Tech Night!",
        venue="Community Hall",
        url="https://lu.ma/tech-night",
    )
    merged = dedupe_listings([sparse, rich])
    assert len(merged) == 1
    assert merged[0].source == "luma"


def test_aggregate_events_parallel(monkeypatch) -> None:
    def fake_meetup(**_kwargs):
        return ([_listing(source="meetup", title="Meetup A")], "https://meetup.com/find")

    def fake_eventbrite(**_kwargs):
        return (
            [_listing(source="eventbrite", title="Festival B", url="https://eb.com/2")],
            "https://eventbrite.com/d/test",
        )

    def fake_luma(**_kwargs):
        return ([], "https://lu.ma/sf")

    def fake_funcheap(**_kwargs):
        return (
            [_listing(source="funcheap", title="Free C", url="https://funcheap.com/c")],
            "https://sf.funcheap.com/today/",
        )

    monkeypatch.setattr(
        "app.services.event_aggregator.search_meetup_listings",
        fake_meetup,
    )
    monkeypatch.setattr(
        "app.services.event_aggregator.search_eventbrite_listings",
        fake_eventbrite,
    )
    monkeypatch.setattr(
        "app.services.event_aggregator.search_luma_listings",
        fake_luma,
    )
    monkeypatch.setattr(
        "app.services.event_aggregator.search_funcheap_listings",
        fake_funcheap,
    )

    payload = aggregate_events(
        location="cupertino",
        keywords="",
        timing="weekend",
        categories=[],
    )
    assert payload["fetched_in_parallel"] is True
    assert payload["broad_fetch"] is False
    assert payload["count"] == 3
    assert payload["sources"]["meetup"]["count"] == 1
    assert payload["sources"]["luma"]["count"] == 0
    assert payload["sources"]["luma"]["error"] is None


def test_aggregate_events_keyword_filter_after_broad_fetch(monkeypatch) -> None:
    def fake_meetup(**kwargs):
        assert kwargs.get("keywords") == ""
        return (
            [
                _listing(source="meetup", title="Random Mixer"),
                _listing(source="meetup", title="Bay Hackathon", url="https://meetup.com/h"),
            ],
            "https://meetup.com/find",
        )

    def fake_luma(**kwargs):
        assert kwargs.get("broad") is True
        return (
            [_listing(source="luma", title="Cursor Hackathon", url="https://lu.ma/h")],
            "https://lu.ma/sf",
        )

    monkeypatch.setattr(
        "app.services.event_aggregator.search_meetup_listings",
        fake_meetup,
    )
    monkeypatch.setattr(
        "app.services.event_aggregator.search_eventbrite_listings",
        lambda **_kwargs: ([], "https://eventbrite.com"),
    )
    monkeypatch.setattr(
        "app.services.event_aggregator.search_luma_listings",
        fake_luma,
    )
    monkeypatch.setattr(
        "app.services.event_aggregator.search_funcheap_listings",
        lambda **_kwargs: ([], "https://sf.funcheap.com/today/"),
    )

    payload = aggregate_events(
        location="cupertino",
        keywords="hackathon",
        timing="upcoming",
        categories=[],
    )
    assert payload["broad_fetch"] is True
    assert payload["raw_count"] == 3
    assert payload["count"] == 2
    titles = {e["title"] for e in payload["events"]}
    assert titles == {"Bay Hackathon", "Cursor Hackathon"}


def test_aggregate_events_survives_source_failure(monkeypatch) -> None:
    def fake_meetup(**_kwargs):
        raise RuntimeError("Meetup unavailable")

    def fake_eventbrite(**_kwargs):
        return ([_listing(source="eventbrite", title="Only EB")], "https://eb.com")

    monkeypatch.setattr(
        "app.services.event_aggregator.search_meetup_listings",
        fake_meetup,
    )
    monkeypatch.setattr(
        "app.services.event_aggregator.search_eventbrite_listings",
        fake_eventbrite,
    )
    monkeypatch.setattr(
        "app.services.event_aggregator.search_luma_listings",
        lambda **_kwargs: ([], "https://lu.ma/sf"),
    )
    monkeypatch.setattr(
        "app.services.event_aggregator.search_funcheap_listings",
        lambda **_kwargs: ([], "https://sf.funcheap.com/today/"),
    )

    payload = aggregate_events(location="cupertino")
    assert payload["count"] == 1
    assert "Meetup unavailable" in payload["sources"]["meetup"]["error"]
