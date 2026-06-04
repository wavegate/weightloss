"""Aggregate event listings from all platforms in parallel."""

from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

from app.services.eventbrite_service import EventListing, search_eventbrite_listings
from app.services.funcheap_service import search_funcheap_listings
from app.services.luma_service import search_luma_listings
from app.services.meetup_service import search_meetup_listings

DEFAULT_LOCATION = "cupertino"
DEFAULT_MAX_PER_SOURCE = 12
DEFAULT_MAX_TOTAL = 30

_SOURCE_ORDER = ("meetup", "luma", "eventbrite", "funcheap")


@dataclass(frozen=True)
class SourceFetchResult:
    source: str
    listings: list[EventListing]
    page_url: str
    error: str | None = None


def _eventbrite_category(timing: str) -> str:
    key = timing.strip().lower().replace(" ", "-")
    if key in {"today", "events--today"}:
        return "events--today"
    if key in {"weekend", "this-weekend", "events--this-weekend"}:
        return "events--this-weekend"
    if key in {"free", "free--events"}:
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
    best_by_key: dict[tuple[str, str, str], EventListing] = {}
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
    max_per_source: int = DEFAULT_MAX_PER_SOURCE,
    max_total: int = DEFAULT_MAX_TOTAL,
) -> dict[str, Any]:
    """Fetch Meetup, Eventbrite, Luma, and Funcheap in parallel, then merge."""
    if max_per_source < 1 or max_per_source > 40:
        raise ValueError("max_per_source must be between 1 and 40")
    if max_total < 1 or max_total > 60:
        raise ValueError("max_total must be between 1 and 60")

    loc = location.strip() or DEFAULT_LOCATION
    eventbrite_category = _eventbrite_category(timing)
    funcheap_filter = _funcheap_filter(timing)

    jobs = {
        "meetup": lambda: search_meetup_listings(
            location=loc,
            keywords=keywords,
            max_results=max_per_source,
        ),
        "eventbrite": lambda: search_eventbrite_listings(
            location=loc,
            category=eventbrite_category,
            max_results=max_per_source,
        ),
        "luma": lambda: search_luma_listings(city=loc, max_results=max_per_source),
        "funcheap": lambda: search_funcheap_listings(
            filter_name=funcheap_filter,
            max_results=max_per_source,
        ),
    }

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

    merged = dedupe_listings(all_listings)[:max_total]

    return {
        "location": loc,
        "keywords": keywords.strip(),
        "timing": timing,
        "fetched_in_parallel": True,
        "elapsed_ms": elapsed_ms,
        "sources": sources_meta,
        "raw_count": len(all_listings),
        "count": len(merged),
        "events": [event.to_dict() for event in merged],
    }
