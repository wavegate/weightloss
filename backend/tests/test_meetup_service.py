import json

from app.services.meetup_service import (
    build_find_url,
    resolve_meetup_location_slug,
    search_meetup_listings,
    _parse_events_from_apollo,
)

SAMPLE_APOLLO = {
    "Event:1": {
        "__typename": "Event",
        "id": "1",
        "title": "Peninsula Tech Night",
        "dateTime": "2026-06-10T19:00:00-07:00",
        "eventUrl": "https://www.meetup.com/example-group/events/1/",
        "venue": {
            "__typename": "Venue",
            "name": "Community Center",
            "city": "Mountain View",
            "state": "CA",
        },
        "group": {"__ref": "Group:9"},
    },
    "Group:9": {
        "__typename": "Group",
        "name": "Bay Area Builders",
    },
}


def test_resolve_meetup_location_slug() -> None:
    assert resolve_meetup_location_slug("Cupertino") == "us--ca--cupertino"
    assert resolve_meetup_location_slug("us--ca--san-jose") == "us--ca--san-jose"


def test_build_find_url_keywords() -> None:
    url = build_find_url(location="mountain-view", keywords="hiking", distance_miles=15)
    assert "meetup.com/find/" in url
    assert "keywords=hiking" in url
    assert "us--ca--mountain-view" in url
    assert "distance=15" in url


def test_parse_events_from_apollo() -> None:
    listings = _parse_events_from_apollo(SAMPLE_APOLLO, max_results=10)
    assert len(listings) == 1
    assert listings[0].title == "Peninsula Tech Night"
    assert listings[0].source == "meetup"
    assert listings[0].city == "Mountain View"
    assert "Bay Area Builders" in (listings[0].venue or "")


def test_search_meetup_listings_parses_fixture(monkeypatch) -> None:
    apollo_json = json.dumps(SAMPLE_APOLLO)
    html = f'<html><script id="__NEXT_DATA__" type="application/json">{{"props":{{"pageProps":{{"__APOLLO_STATE__":{apollo_json}}}}}}}</script></html>'

    def fake_get(url: str) -> str:
        assert "meetup.com/find/" in url
        return html

    monkeypatch.setattr("app.services.meetup_service._http_get", fake_get)
    listings, find_url = search_meetup_listings(
        location="cupertino",
        keywords="tech",
        max_results=5,
    )
    assert "us--ca--cupertino" in find_url
    assert len(listings) == 1
    assert listings[0].url.endswith("/events/1/")
