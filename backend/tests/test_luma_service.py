import json

from app.services.luma_service import (
    build_luma_city_url,
    resolve_luma_city_slug,
    search_luma_listings,
    _listing_from_wrapper,
)

SAMPLE_WRAPPER = {
    "api_id": "evt-test",
    "start_at": "2026-06-10T19:00:00.000Z",
    "ticket_info": {"is_free": True, "price": None},
    "event": {
        "api_id": "evt-test",
        "name": "AI Builders Night",
        "url": "abc123",
        "start_at": "2026-06-10T19:00:00.000Z",
        "end_at": "2026-06-10T22:00:00.000Z",
        "geo_address_info": {
            "city": "San Francisco",
            "region": "California",
            "address": "123 Market St",
        },
    },
}


def test_resolve_luma_city_slug() -> None:
    assert resolve_luma_city_slug("cupertino") == "sf"
    assert resolve_luma_city_slug("sf") == "sf"


def test_listing_from_wrapper() -> None:
    listing = _listing_from_wrapper(SAMPLE_WRAPPER)
    assert listing is not None
    assert listing.title == "AI Builders Night"
    assert listing.url == "https://lu.ma/abc123"
    assert listing.cost_summary == "free"


def test_search_luma_listings_fixture(monkeypatch) -> None:
    initial = {"featured_place": {"events": [SAMPLE_WRAPPER]}}
    html = (
        '<html><script id="__NEXT_DATA__" type="application/json">'
        f'{{"props":{{"pageProps":{{"initialData":{json.dumps(initial)}}}}}}}'
        "</script></html>"
    )

    def fake_get(url: str, *, extra_headers=None) -> str:
        return html

    monkeypatch.setattr("app.services.luma_service.http_get", fake_get)
    listings, page_url = search_luma_listings(city="sf", max_results=5)
    assert build_luma_city_url("sf") in page_url
    assert len(listings) == 1


def test_keyword_filter_on_hackathon_title() -> None:
    from app.services.event_keyword_filter import listing_matches_keywords, parse_keyword_tokens

    from app.services.luma_service import _listing_from_wrapper

    wrapper = {
        **SAMPLE_WRAPPER,
        "event": {**SAMPLE_WRAPPER["event"], "name": "Bay Area Hackathon Weekend"},
    }
    listing = _listing_from_wrapper(wrapper)
    assert listing is not None
    tokens = parse_keyword_tokens("hackathon")
    assert listing_matches_keywords(listing, tokens)
