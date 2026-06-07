import json

from app.services.meetup_service import (
    RECOMMENDED_EVENTS_QUERY,
    _paginate_all_listings,
    _parse_events_from_apollo,
    _search_context_from_root,
    build_find_url,
    resolve_meetup_location_slug,
    search_meetup_listings,
)

SAMPLE_APOLLO = {
    "ROOT_QUERY": {
        'recommendedEvents:{"filter":{"lat":37.31,"lon":-122.04,"doConsolidateEvents":true,"doPromotePaypalEvents":false},"sort":{"sortField":"RELEVANCE"}}': {
            "__typename": "RecommendedEventsConnection",
            "totalCount": 2,
            "pageInfo": {
                "__typename": "PageInfo",
                "hasNextPage": True,
                "endCursor": "MTI=",
            },
            "edges": [
                {"__ref": 'RecommendedEventsEdge:{"node":{"id":"1"}}'},
                {"__ref": 'RecommendedEventsEdge:{"node":{"id":"2"}}'},
            ],
        }
    },
    'RecommendedEventsEdge:{"node":{"id":"1"}}': {
        "node": {"__ref": "Event:1"},
    },
    'RecommendedEventsEdge:{"node":{"id":"2"}}': {
        "node": {"__ref": "Event:2"},
    },
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
    "Event:2": {
        "__typename": "Event",
        "id": "2",
        "title": "Board Games",
        "dateTime": "2026-06-11T19:00:00-07:00",
        "eventUrl": "https://www.meetup.com/example-group/events/2/",
        "venue": {
            "__typename": "Venue",
            "name": "Library",
            "city": "Cupertino",
            "state": "CA",
        },
        "group": {"__ref": "Group:9"},
    },
    "Group:9": {
        "__typename": "Group",
        "name": "Bay Area Builders",
    },
}

GQL_PAGE = {
    "pageInfo": {"hasNextPage": False, "endCursor": None},
    "totalCount": 1,
    "edges": [
        {
            "node": {
                "id": "3",
                "title": "GraphQL Meetup",
                "dateTime": "2026-06-12T19:00:00-07:00",
                "eventUrl": "https://www.meetup.com/example-group/events/3/",
                "feeSettings": None,
                "group": {"name": "Bay Area Builders"},
                "venue": {
                    "name": "Office",
                    "city": "Palo Alto",
                    "state": "CA",
                },
            }
        }
    ],
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
    assert len(listings) == 2
    assert listings[0].title == "Peninsula Tech Night"
    assert listings[0].source == "meetup"
    assert listings[0].city == "Mountain View"
    assert "Bay Area Builders" in (listings[0].venue or "")


def test_search_context_from_root() -> None:
    context = _search_context_from_root(SAMPLE_APOLLO["ROOT_QUERY"])
    assert context.kind == "recommendedEvents"
    assert context.operation_name == "recommendedEventsPage"
    assert context.filter_params["lat"] == 37.31


def test_paginate_all_listings_fetches_next_page(monkeypatch) -> None:
    context = _search_context_from_root(SAMPLE_APOLLO["ROOT_QUERY"])

    def fake_fetch_gql_page(_context, *, after, referer, page_size=12):
        assert after == "MTI="
        assert referer == "https://meetup.com/find"
        return GQL_PAGE

    monkeypatch.setattr("app.services.meetup_service._fetch_gql_page", fake_fetch_gql_page)
    listings = _paginate_all_listings(
        SAMPLE_APOLLO,
        context,
        referer="https://meetup.com/find",
        max_results=None,
    )
    assert len(listings) == 3
    assert {listing.title for listing in listings} == {
        "Peninsula Tech Night",
        "Board Games",
        "GraphQL Meetup",
    }


def test_search_meetup_listings_parses_fixture(monkeypatch) -> None:
    apollo_json = json.dumps(SAMPLE_APOLLO)
    html = f'<html><script id="__NEXT_DATA__" type="application/json">{{"props":{{"pageProps":{{"__APOLLO_STATE__":{apollo_json}}}}}}}</script></html>'

    def fake_get(url: str) -> str:
        assert "meetup.com/find/" in url
        return html

    monkeypatch.setattr("app.services.meetup_service._http_get", fake_get)
    monkeypatch.setattr(
        "app.services.meetup_service._fetch_gql_page",
        lambda _context, **kwargs: GQL_PAGE,
    )
    listings, find_url = search_meetup_listings(
        location="cupertino",
        keywords="tech",
        max_results=10,
    )
    assert "us--ca--cupertino" in find_url
    assert len(listings) == 3
    assert listings[0].url.endswith("/events/1/")


def test_recommended_events_query_is_valid_graphql() -> None:
    assert "recommendedEventsPage" in RECOMMENDED_EVENTS_QUERY
    assert "pageInfo" in RECOMMENDED_EVENTS_QUERY
