"""Post-fetch filtering for event listings."""

from __future__ import annotations

import re
from datetime import date

from app.services.event_date_utils import listing_in_date_range
from app.services.event_keyword_filter import (
    listing_matches_keywords,
    parse_keyword_tokens,
)
from app.services.event_listing import EventListing


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


def filter_listings(
    listings: list[EventListing],
    *,
    keywords: str = "",
    start_date: date | None = None,
    end_date: date | None = None,
    free_only: bool = False,
    max_price_usd: float | None = None,
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
        if keyword_tokens and not listing_matches_keywords(listing, keyword_tokens):
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
