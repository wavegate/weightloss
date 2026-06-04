from app.services.funcheap_service import (
    build_funcheap_url,
    resolve_funcheap_filter,
    search_funcheap_listings,
    _parse_listings,
)

SAMPLE_HTML = """
<div class="entry-title"><a href="https://sf.funcheap.com/sample-free-music-night-3/" rel="bookmark"
>Free Music Night</a></span>
<div class="meta archive-meta date-time" data-event-date="2026-06-04 19:00"
 data-event-date-end="2026-06-04 22:00">Thursday |
<span class="cost">Cost:</span> <a class="tt">FREE</a> | <span>The Function</span> </div>
<div class="thumbnail-wrapper">
"""


def test_resolve_funcheap_filter() -> None:
    assert resolve_funcheap_filter("this-weekend") == "weekend"
    assert resolve_funcheap_filter("events--today") == "today"


def test_parse_listings() -> None:
    listings = _parse_listings(SAMPLE_HTML, max_results=5)
    assert len(listings) == 1
    assert listings[0].title == "Free Music Night"
    assert listings[0].is_free is True
    assert listings[0].venue == "The Function"


def test_search_funcheap_listings_fixture(monkeypatch) -> None:
    def fake_get(url: str, *, extra_headers=None) -> str:
        assert url == build_funcheap_url("today")
        return SAMPLE_HTML

    monkeypatch.setattr("app.services.funcheap_service.http_get", fake_get)
    listings, page_url = search_funcheap_listings(filter_name="today", max_results=5)
    assert len(listings) == 1
    assert "funcheap.com/today" in page_url
