"""Load, save, and apply stored event discovery preferences."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_event_preferences import UserEventPreferences
from app.schemas.event_preferences import EventPreferencesRead, EventPreferencesUpsert
from app.services.event_preference_options import (
    BAY_AREA_LOCATIONS,
    DEFAULT_CATEGORIES,
    DEFAULT_DISTANCE_MILES,
    DEFAULT_HOME_LOCATION,
    DEFAULT_TIMING,
    EVENT_CATEGORY_OPTIONS,
    TIMING_OPTIONS,
)
from app.services.event_date_utils import listing_in_date_range, parse_iso_date
from app.services.event_keyword_filter import (
    listing_matches_keywords,
    parse_keyword_tokens,
)
from app.services.eventbrite_service import EventListing

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "tech": ["tech", "startup", "ai", "software", "engineering"],
    "networking": ["networking", "meetup", "professional"],
    "music": ["music", "concert", "dj", "live"],
    "food-drink": ["food", "wine", "beer", "tasting", "restaurant"],
    "family": ["family", "kids", "children", "education"],
    "sports": ["sport", "fitness", "run", "yoga", "cycling"],
    "arts": ["art", "theater", "theatre", "gallery", "museum"],
    "community": ["community", "volunteer", "cultural"],
    "health": ["health", "wellness", "meditation"],
}


@dataclass(frozen=True)
class ResolvedEventSearch:
    location: str
    keywords: str
    timing: str
    start_date: date | None
    end_date: date | None
    distance_miles: int
    free_only: bool
    max_price_usd: float | None
    categories: list[str]
    preferences_applied: bool


def default_preferences_upsert() -> EventPreferencesUpsert:
    return EventPreferencesUpsert()


def preferences_to_read(row: UserEventPreferences) -> EventPreferencesRead:
    return EventPreferencesRead.model_validate(row)


def get_preferences_row(
    db: Session, user_id: str
) -> UserEventPreferences | None:
    return db.scalar(
        select(UserEventPreferences).where(UserEventPreferences.user_id == user_id)
    )


def get_or_create_preferences(
    db: Session, user_id: str
) -> UserEventPreferences:
    row = get_preferences_row(db, user_id)
    if row is not None:
        return row
    defaults = default_preferences_upsert()
    row = UserEventPreferences(
        user_id=user_id,
        home_location=defaults.home_location,
        distance_miles=defaults.distance_miles,
        default_timing=defaults.default_timing,
        free_only=defaults.free_only,
        max_price_usd=defaults.max_price_usd,
        interest_keywords=defaults.interest_keywords,
        categories=list(defaults.categories),
        start_date=defaults.start_date,
        end_date=defaults.end_date,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def preferences_row_to_upsert(row: UserEventPreferences) -> EventPreferencesUpsert:
    return EventPreferencesUpsert(
        home_location=row.home_location,
        distance_miles=row.distance_miles,
        default_timing=row.default_timing,
        start_date=row.start_date,
        end_date=row.end_date,
        free_only=row.free_only,
        max_price_usd=row.max_price_usd,
        interest_keywords=row.interest_keywords or "",
        categories=list(row.categories or []),
    )


def merge_preferences_update(
    row: UserEventPreferences, **updates: Any
) -> EventPreferencesUpsert:
    data = preferences_row_to_upsert(row).model_dump()
    for key, value in updates.items():
        if value is not None:
            data[key] = value
    return EventPreferencesUpsert(**data)


def upsert_preferences(
    db: Session, user_id: str, payload: EventPreferencesUpsert
) -> UserEventPreferences:
    row = get_preferences_row(db, user_id)
    data = payload.model_dump()
    if row is None:
        row = UserEventPreferences(user_id=user_id, **data)
        db.add(row)
    else:
        for key, value in data.items():
            setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


def build_keywords_from_preferences(row: UserEventPreferences) -> str:
    parts: list[str] = []
    if row.interest_keywords.strip():
        parts.append(row.interest_keywords.strip())
    for category in row.categories or []:
        for word in _CATEGORY_KEYWORDS.get(category, [category]):
            if word not in parts:
                parts.append(word)
    return " ".join(parts)


def _resolve_dates(
    row: UserEventPreferences | None,
    *,
    start_date: str = "",
    end_date: str = "",
) -> tuple[date | None, date | None]:
    override_start = parse_iso_date(start_date)
    override_end = parse_iso_date(end_date)
    if override_start and override_end:
        return override_start, override_end
    if row is None:
        return None, None
    if row.default_timing == "date-range":
        return row.start_date, row.end_date
    return None, None


def resolve_search_params(
    row: UserEventPreferences | None,
    *,
    location: str = "",
    keywords: str = "",
    timing: str = "",
    start_date: str = "",
    end_date: str = "",
) -> ResolvedEventSearch:
    range_start, range_end = _resolve_dates(
        row, start_date=start_date, end_date=end_date
    )

    if row is None:
        resolved_timing = timing.strip() or DEFAULT_TIMING
        if range_start and range_end:
            resolved_timing = "date-range"
        return ResolvedEventSearch(
            location=location.strip() or DEFAULT_HOME_LOCATION,
            keywords=keywords.strip(),
            timing=resolved_timing,
            start_date=range_start,
            end_date=range_end,
            distance_miles=DEFAULT_DISTANCE_MILES,
            free_only=False,
            max_price_usd=None,
            categories=list(DEFAULT_CATEGORIES),
            preferences_applied=False,
        )

    resolved_timing = timing.strip() or row.default_timing
    if range_start and range_end:
        resolved_timing = "date-range"
    elif resolved_timing == "date-range":
        range_start, range_end = row.start_date, row.end_date

    if row.free_only and resolved_timing == "upcoming":
        resolved_timing = "free"

    return ResolvedEventSearch(
        location=location.strip() or row.home_location,
        keywords=keywords.strip() or build_keywords_from_preferences(row),
        timing=resolved_timing,
        start_date=range_start,
        end_date=range_end,
        distance_miles=row.distance_miles,
        free_only=row.free_only,
        max_price_usd=float(row.max_price_usd) if row.max_price_usd is not None else None,
        categories=list(row.categories or []),
        preferences_applied=True,
    )


def _parse_price_upper(cost_summary: str | None) -> float | None:
    if not cost_summary:
        return None
    lowered = cost_summary.lower()
    if "free" in lowered:
        return 0.0
    numbers = re.findall(r"(\d+(?:\.\d+)?)", cost_summary)
    if not numbers:
        return None
    return max(float(value) for value in numbers)


def _matches_categories(listing: EventListing, categories: list[str]) -> bool:
    if not categories:
        return True
    haystack = listing.title.lower()
    for category in categories:
        for word in _CATEGORY_KEYWORDS.get(category, [category]):
            if word in haystack:
                return True
    return False


def filter_listings_by_preferences(
    listings: list[EventListing],
    *,
    free_only: bool,
    max_price_usd: float | None,
    categories: list[str],
    keywords: str = "",
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[EventListing]:
    keyword_tokens = parse_keyword_tokens(keywords)
    filtered: list[EventListing] = []
    for listing in listings:
        if start_date and end_date and not listing_in_date_range(
            listing.start,
            range_start=start_date,
            range_end=end_date,
        ):
            continue
        if keyword_tokens:
            if not listing_matches_keywords(listing, keyword_tokens):
                continue
        elif categories and not _matches_categories(listing, categories):
            continue
        if free_only:
            is_free = listing.is_free is True
            cost_free = bool(
                listing.cost_summary and "free" in listing.cost_summary.lower()
            )
            if not is_free and not cost_free:
                price = _parse_price_upper(listing.cost_summary)
                if price is not None and price > 0:
                    continue
                if listing.is_free is False:
                    continue
        if max_price_usd is not None:
            upper = _parse_price_upper(listing.cost_summary)
            if upper is not None and upper > max_price_usd:
                continue
        filtered.append(listing)
    return filtered


def preference_options_payload() -> dict[str, Any]:
    return {
        "locations": BAY_AREA_LOCATIONS,
        "timings": TIMING_OPTIONS,
        "categories": EVENT_CATEGORY_OPTIONS,
    }
