"""Post-fetch keyword matching for event listings."""

from __future__ import annotations

import re

from app.services.eventbrite_service import EventListing


def parse_keyword_tokens(keywords: str) -> list[str]:
    tokens = re.split(r"[\s,]+", keywords.strip().lower())
    return [token for token in tokens if len(token) >= 2]


def listing_search_text(listing: EventListing) -> str:
    parts = [
        listing.title,
        listing.venue,
        listing.city,
        listing.region,
        listing.url,
    ]
    return " ".join(part for part in parts if part).lower()


def listing_matches_keywords(listing: EventListing, tokens: list[str]) -> bool:
    if not tokens:
        return True
    haystack = listing_search_text(listing)
    return any(token in haystack for token in tokens)
