import json

from app.services.eventbrite_service import (
    build_browse_url,
    resolve_location_slug,
    search_eventbrite_listings,
    _parse_item_list,
)

SAMPLE_ITEM_LIST_HTML = """
<html><head>
<script type="application/ld+json">{"@type":"BreadcrumbList"}</script>
<script type="application/ld+json">{
  "@type": "ItemList",
  "itemListElement": [
    {
      "position": 1,
      "@type": "ListItem",
      "item": {
        "@type": "Event",
        "name": "Bay Area Tech Meetup",
        "url": "https://www.eventbrite.com/e/bay-area-tech-meetup-tickets-1234567890",
        "startDate": "2026-06-14",
        "endDate": "2026-06-14",
        "location": {
          "@type": "Place",
          "name": "Community Hall",
          "address": {
            "@type": "PostalAddress",
            "addressLocality": "Mountain View",
            "addressRegion": "CA"
          }
        }
      }
    }
  ]
}</script>
</head><body></body></html>
"""


def test_resolve_location_slug_aliases() -> None:
    assert resolve_location_slug("Cupertino") == "ca--san-jose"
    assert resolve_location_slug("ca--mountain-view") == "ca--mountain-view"


def test_build_browse_url_with_dates() -> None:
    url = build_browse_url(
        location="mountain-view",
        category="tech",
        page=2,
        start_date="2026-06-01",
        end_date="2026-06-30",
    )
    assert url.startswith("https://www.eventbrite.com/d/ca--mountain-view/tech/")
    assert "page=2" in url
    assert "start_date=2026-06-01" in url


def test_parse_item_list_extracts_events() -> None:
    items = _parse_item_list(SAMPLE_ITEM_LIST_HTML)
    assert len(items) == 1
    assert items[0]["name"] == "Bay Area Tech Meetup"


def test_search_eventbrite_listings_parses_fixture(monkeypatch) -> None:
    def fake_get(url: str, *, headers: dict[str, str] | None = None) -> str:
        assert "eventbrite.com/d/" in url
        return SAMPLE_ITEM_LIST_HTML

    monkeypatch.setattr(
        "app.services.eventbrite_service._http_get",
        fake_get,
    )
    listings, browse_url = search_eventbrite_listings(
        location="mountain-view",
        category="tech",
        enrich_with_api=False,
    )
    assert "ca--mountain-view" in browse_url
    assert len(listings) == 1
    assert listings[0].title == "Bay Area Tech Meetup"
    assert listings[0].city == "Mountain View"
    assert "1234567890" in listings[0].url
