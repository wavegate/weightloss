"""Fetch and filter Meetup event listings."""

from __future__ import annotations

import time
from datetime import date
from typing import Any

from app.services.event_filter import filter_listings
from app.services.event_listing import EventListing
from app.services.event_keyword_filter import parse_keyword_tokens
from app.services.meetup_service import search_meetup_listings

DEFAULT_LOCATION = "cupertino"
DEFAULT_MAX_RESULTS = 30


def aggregate_events(
    *,
    location: str = DEFAULT_LOCATION,
    keywords: str = "",
    start_date: date | None = None,
    end_date: date | None = None,
    distance_miles: int | None = None,
    free_only: bool = False,
    max_price_usd: float | None = None,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> dict[str, Any]:
    if max_results < 1 or max_results > 60:
        raise ValueError("max_results must be between 1 and 60")

    loc = location.strip() or DEFAULT_LOCATION
    keyword_tokens = parse_keyword_tokens(keywords)
    broad_topic_search = bool(keyword_tokens)
    meetup_distance = distance_miles if distance_miles and distance_miles > 0 else None
    meetup_keywords = "" if broad_topic_search else keywords

    started = time.perf_counter()
    error: str | None = None
    page_url = ""
    raw_listings: list[EventListing] = []
    try:
        raw_listings, page_url = search_meetup_listings(
            location=loc,
            keywords=meetup_keywords,
            distance_miles=meetup_distance,
            max_results=None,
        )
    except Exception as exc:  # noqa: BLE001 — report failures to the agent
        error = str(exc)

    elapsed_ms = int((time.perf_counter() - started) * 1000)

    filtered = filter_listings(
        raw_listings,
        keywords=keywords,
        start_date=start_date,
        end_date=end_date,
        free_only=free_only,
        max_price_usd=max_price_usd,
    )[:max_results]

    return {
        "location": loc,
        "keywords": keywords.strip(),
        "broad_fetch": broad_topic_search,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "distance_miles": meetup_distance,
        "free_only": free_only,
        "max_price_usd": max_price_usd,
        "elapsed_ms": elapsed_ms,
        "source": {
            "name": "meetup",
            "count": len(raw_listings),
            "page_url": page_url,
            "error": error,
        },
        "raw_count": len(raw_listings),
        "count": len(filtered),
        "events": [event.to_dict() for event in filtered],
    }
