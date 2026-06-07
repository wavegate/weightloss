from app.services.event_aggregator import aggregate_events
from app.services.event_listing import EventListing


def _listing(
    *,
    title: str,
    start: str = "2026-06-10T19:00:00",
    venue: str = "Community Hall",
    url: str = "https://example.com/1",
) -> EventListing:
    return EventListing(
        id="meetup:1",
        title=title,
        start=start,
        end=None,
        venue=venue,
        city="Mountain View",
        region="CA",
        url=url,
        is_free=None,
        cost_summary=None,
        source="meetup",
    )


def test_aggregate_events_returns_meetup_listings(monkeypatch) -> None:
    def fake_meetup(**_kwargs):
        return (
            [
                _listing(title="Meetup A"),
                _listing(title="Meetup B", url="https://meetup.com/b"),
            ],
            "https://meetup.com/find",
        )

    monkeypatch.setattr(
        "app.services.event_aggregator.search_meetup_listings",
        fake_meetup,
    )

    payload = aggregate_events(location="cupertino", keywords="")
    assert payload["count"] == 2
    assert payload["source"]["count"] == 2
    assert payload["source"]["error"] is None
    assert payload["source"]["page_url"] == "https://meetup.com/find"


def test_aggregate_events_keyword_filter_after_broad_fetch(monkeypatch) -> None:
    def fake_meetup(**kwargs):
        assert kwargs.get("keywords") == ""
        return (
            [
                _listing(title="Random Mixer"),
                _listing(title="Bay Hackathon", url="https://meetup.com/h"),
            ],
            "https://meetup.com/find",
        )

    monkeypatch.setattr(
        "app.services.event_aggregator.search_meetup_listings",
        fake_meetup,
    )

    payload = aggregate_events(
        location="cupertino",
        keywords="hackathon",
    )
    assert payload["broad_fetch"] is True
    assert payload["raw_count"] == 2
    assert payload["count"] == 1
    assert payload["events"][0]["title"] == "Bay Hackathon"


def test_aggregate_events_survives_meetup_failure(monkeypatch) -> None:
    def fake_meetup(**_kwargs):
        raise RuntimeError("Meetup unavailable")

    monkeypatch.setattr(
        "app.services.event_aggregator.search_meetup_listings",
        fake_meetup,
    )

    payload = aggregate_events(location="cupertino")
    assert payload["count"] == 0
    assert "Meetup unavailable" in payload["source"]["error"]
