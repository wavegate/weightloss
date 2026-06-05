"""Aggregate event listings from all platforms in parallel."""

from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.services.eventbrite_service import EventListing, search_eventbrite_listings
from app.services.funcheap_service import search_funcheap_listings
from app.services.luma_service import search_luma_listings
from app.services.event_date_utils import funcheap_filters_for_range
from app.services.event_keyword_filter import parse_keyword_tokens
from app.services.event_preferences_service import (
    ResolvedEventSearch,
    filter_listings_by_preferences,
)
from app.services.meetup_service import search_meetup_listings

DEFAULT_LOCATION = "cupertino"
DEFAULT_MAX_PER_SOURCE = 12
DEFAULT_MAX_PER_SOURCE_BROAD = 40
DEFAULT_MAX_TOTAL = 30
DEFAULT_LUMA_BROAD = 60

_SOURCE_ORDER = ("meetup", "luma", "eventbrite", "funcheap")


@dataclass(frozen=True)
class SourceFetchResult:
    source: str
    listings: list[EventListing]
    page_url: str
    error: str | None = None


def _eventbrite_category(timing: str, *, free_only: bool = False) -> str:
    key = timing.strip().lower().replace(" ", "-")
    if key == "date-range":
        return "free--events" if free_only else "events"
    if key in {"today", "events--today"}:
        return "events--today"
    if key in {"weekend", "this-weekend", "events--this-weekend"}:
        return "events--this-weekend"
    if key in {"free", "free--events"} or free_only:
        return "free--events"
    return "events"


def _funcheap_filter(timing: str) -> str:
    key = timing.strip().lower().replace(" ", "-")
    if key in {"weekend", "this-weekend", "events--this-weekend"}:
        return "weekend"
    return "today"


def _normalize_title(title: str) -> str:
    lowered = title.lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return " ".join(cleaned.split())


def _start_key(start: str | None) -> str:
    if not start:
        return ""
    return start[:10]


def _dedupe_key(listing: EventListing) -> tuple[str, str]:
    """Match on title + start date; venue strings differ too much across sources."""
    return (_normalize_title(listing.title), _start_key(listing.start))


def _listing_richness(listing: EventListing) -> int:
    score = 0
    for value in (
        listing.start,
        listing.venue,
        listing.city,
        listing.cost_summary,
        listing.url,
    ):
        if value:
            score += 1
    if listing.is_free is not None:
        score += 1
    return score


def _source_rank(source: str) -> int:
    try:
        return _SOURCE_ORDER.index(source)
    except ValueError:
        return len(_SOURCE_ORDER)


def dedupe_listings(listings: list[EventListing]) -> list[EventListing]:
    best_by_key: dict[tuple[str, str], EventListing] = {}
    for listing in listings:
        key = _dedupe_key(listing)
        existing = best_by_key.get(key)
        if existing is None:
            best_by_key[key] = listing
            continue
        if _listing_richness(listing) > _listing_richness(existing):
            best_by_key[key] = listing
        elif _listing_richness(listing) == _listing_richness(existing):
            if _source_rank(listing.source) < _source_rank(existing.source):
                best_by_key[key] = listing
    merged = list(best_by_key.values())
    merged.sort(key=lambda item: item.start or "9999")
    return merged


def _safe_fetch(source: str, fetch) -> SourceFetchResult:
    try:
        listings, page_url = fetch()
        return SourceFetchResult(
            source=source,
            listings=listings,
            page_url=page_url,
            error=None,
        )
    except Exception as exc:  # noqa: BLE001 — report per-source failures to the agent
        return SourceFetchResult(
            source=source,
            listings=[],
            page_url="",
            error=str(exc),
        )


def aggregate_events(
    *,
    location: str = DEFAULT_LOCATION,
    keywords: str = "",
    timing: str = "upcoming",
    start_date: date | None = None,
    end_date: date | None = None,
    distance_miles: int | None = None,
    free_only: bool = False,
    max_price_usd: float | None = None,
    categories: list[str] | None = None,
    max_per_source: int = DEFAULT_MAX_PER_SOURCE,
    max_total: int = DEFAULT_MAX_TOTAL,
) -> dict[str, Any]:
    """Fetch Meetup, Eventbrite, Luma, and Funcheap in parallel, then merge."""
    if max_per_source < 1 or max_per_source > 40:
        raise ValueError("max_per_source must be between 1 and 40")
    if max_total < 1 or max_total > 60:
        raise ValueError("max_total must be between 1 and 60")

    loc = location.strip() or DEFAULT_LOCATION
    eventbrite_category = _eventbrite_category(timing, free_only=free_only)
    meetup_distance = distance_miles if distance_miles and distance_miles > 0 else None
    filter_categories = list(categories or [])
    keyword_tokens = parse_keyword_tokens(keywords)
    broad_topic_search = bool(keyword_tokens)
    fetch_per_source = (
        max(max_per_source, DEFAULT_MAX_PER_SOURCE_BROAD)
        if broad_topic_search
        else max_per_source
    )
    luma_cap = DEFAULT_LUMA_BROAD if broad_topic_search else fetch_per_source
    meetup_keywords = "" if broad_topic_search else keywords
    eventbrite_category = (
        "tech" if broad_topic_search and eventbrite_category == "events" else eventbrite_category
    )

    eventbrite_start = start_date.isoformat() if start_date else None
    eventbrite_end = end_date.isoformat() if end_date else None

    jobs: dict[str, Any] = {
        "meetup": lambda: search_meetup_listings(
            location=loc,
            keywords=meetup_keywords,
            distance_miles=meetup_distance,
            max_results=fetch_per_source,
        ),
        "eventbrite": lambda: search_eventbrite_listings(
            location=loc,
            category=eventbrite_category,
            start_date=eventbrite_start,
            end_date=eventbrite_end,
            max_results=fetch_per_source,
        ),
        "luma": lambda: search_luma_listings(
            city=loc,
            max_results=luma_cap,
            broad=broad_topic_search,
        ),
    }

    if start_date and end_date:
        for funcheap_filter in funcheap_filters_for_range(start_date, end_date):
            key = f"funcheap_{funcheap_filter}"
            jobs[key] = (
                lambda ff=funcheap_filter: search_funcheap_listings(
                    filter_name=ff,
                    max_results=fetch_per_source,
                )
            )
    else:
        jobs["funcheap"] = lambda: search_funcheap_listings(
            filter_name=_funcheap_filter(timing),
            max_results=fetch_per_source,
        )

    started = time.perf_counter()
    source_results: list[SourceFetchResult] = []
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {
            pool.submit(_safe_fetch, source, fetch): source
            for source, fetch in jobs.items()
        }
        for future in as_completed(futures):
            source_results.append(future.result())

    elapsed_ms = int((time.perf_counter() - started) * 1000)

    all_listings: list[EventListing] = []
    sources_meta: dict[str, Any] = {}
    for result in sorted(source_results, key=lambda r: _source_rank(r.source)):
        all_listings.extend(result.listings)
        sources_meta[result.source] = {
            "count": len(result.listings),
            "page_url": result.page_url,
            "error": result.error,
        }

    merged = dedupe_listings(all_listings)
    merged = filter_listings_by_preferences(
        merged,
        free_only=free_only,
        max_price_usd=max_price_usd,
        categories=filter_categories,
        keywords=keywords,
        start_date=start_date,
        end_date=end_date,
    )[:max_total]

    return {
        "location": loc,
        "keywords": keywords.strip(),
        "broad_fetch": broad_topic_search,
        "timing": timing,
        "start_date": eventbrite_start,
        "end_date": eventbrite_end,
        "distance_miles": meetup_distance,
        "free_only": free_only,
        "max_price_usd": max_price_usd,
        "categories": filter_categories,
        "fetched_in_parallel": True,
        "elapsed_ms": elapsed_ms,
        "sources": sources_meta,
        "raw_count": len(all_listings),
        "count": len(merged),
        "events": [event.to_dict() for event in merged],
    }


def aggregate_events_from_resolved(
    resolved: ResolvedEventSearch,
    *,
    max_per_source: int = DEFAULT_MAX_PER_SOURCE,
    max_total: int = DEFAULT_MAX_TOTAL,
) -> dict[str, Any]:
    payload = aggregate_events(
        location=resolved.location,
        keywords=resolved.keywords,
        timing=resolved.timing,
        start_date=resolved.start_date,
        end_date=resolved.end_date,
        distance_miles=resolved.distance_miles,
        free_only=resolved.free_only,
        max_price_usd=resolved.max_price_usd,
        categories=resolved.categories,
        max_per_source=max_per_source,
        max_total=max_total,
    )
    payload["preferences_applied"] = resolved.preferences_applied
    return payload
