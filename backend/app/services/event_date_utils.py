"""Parse and filter event listing dates."""

from __future__ import annotations

from datetime import date, timedelta


def parse_iso_date(value: str | None) -> date | None:
    if not value or not value.strip():
        return None
    trimmed = value.strip()[:10]
    try:
        return date.fromisoformat(trimmed)
    except ValueError:
        return None


def parse_listing_start(start: str | None) -> date | None:
    if not start:
        return None
    normalized = start.strip().replace(" ", "T")
    return parse_iso_date(normalized)


def listing_in_date_range(
    start: str | None,
    *,
    range_start: date,
    range_end: date,
) -> bool:
    event_day = parse_listing_start(start)
    if event_day is None:
        return True
    return range_start <= event_day <= range_end


def funcheap_filters_for_range(
    range_start: date,
    range_end: date,
    *,
    reference: date | None = None,
) -> list[str]:
    """Pick Funcheap listing pages that may overlap a date range."""
    ref = reference or date.today()
    include_today = range_start <= ref <= range_end
    include_weekend = False
    cursor = range_start
    while cursor <= range_end:
        if cursor.weekday() >= 5:
            include_weekend = True
            break
        cursor += timedelta(days=1)

    filters: list[str] = []
    if include_today:
        filters.append("today")
    if include_weekend:
        filters.append("weekend")
    return filters
