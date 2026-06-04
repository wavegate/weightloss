"""Luma discovery via public city pages (__NEXT_DATA__ initialData)."""

from __future__ import annotations

import json
import re
from typing import Any

from app.services.event_fetch import http_get
from app.services.eventbrite_service import EventListing

LUMA_SITE_BASE = "https://lu.ma"

# Luma city pages use short slugs (e.g. lu.ma/sf). No dedicated South Bay page yet.
CITY_SLUGS: dict[str, str] = {
    "sf": "sf",
    "san-francisco": "sf",
    "san francisco": "sf",
    "cupertino": "sf",
    "mountain-view": "sf",
    "mountain view": "sf",
    "palo-alto": "sf",
    "palo alto": "sf",
    "sunnyvale": "sf",
    "san-jose": "sf",
    "san jose": "sf",
    "oakland": "sf",
    "berkeley": "sf",
    "peninsula": "sf",
    "south-bay": "sf",
    "bay-area": "sf",
}


def resolve_luma_city_slug(city: str) -> str:
    trimmed = city.strip().lower()
    if not trimmed:
        return "sf"
    if trimmed in CITY_SLUGS:
        return CITY_SLUGS[trimmed]
    slug = trimmed.replace(" ", "-")
    return CITY_SLUGS.get(slug, slug)


def build_luma_city_url(city: str) -> str:
    slug = resolve_luma_city_slug(city)
    return f"{LUMA_SITE_BASE}/{slug}"


def _parse_next_data(html: str) -> dict[str, Any]:
    match = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError("Luma page did not include __NEXT_DATA__")
    payload = json.loads(match.group(1))
    initial = payload.get("props", {}).get("pageProps", {}).get("initialData", {})
    if not isinstance(initial, dict):
        raise RuntimeError("Luma page missing initialData")
    return initial


def _listing_from_wrapper(wrapper: dict[str, Any]) -> EventListing | None:
    event = wrapper.get("event")
    if not isinstance(event, dict):
        return None
    title = event.get("name")
    slug = event.get("url")
    api_id = event.get("api_id") or wrapper.get("api_id")
    if not isinstance(title, str) or not isinstance(slug, str):
        return None

    geo = event.get("geo_address_info") or {}
    city = geo.get("city") if isinstance(geo, dict) else None
    region = geo.get("region") if isinstance(geo, dict) else None
    address = geo.get("address") if isinstance(geo, dict) else None
    venue = address if isinstance(address, str) else None

    ticket_info = wrapper.get("ticket_info") or {}
    cost_summary = None
    is_free = None
    if isinstance(ticket_info, dict):
        is_free = ticket_info.get("is_free")
        if is_free is True:
            cost_summary = "free"
        elif ticket_info.get("price") is not None:
            cost_summary = str(ticket_info.get("price"))

    start = wrapper.get("start_at") or event.get("start_at")
    end = event.get("end_at")

    return EventListing(
        id=f"luma:{api_id or slug}",
        title=title.strip(),
        start=start if isinstance(start, str) else None,
        end=end if isinstance(end, str) else None,
        venue=venue,
        city=city if isinstance(city, str) else None,
        region=region if isinstance(region, str) else None,
        url=f"{LUMA_SITE_BASE}/{slug}",
        is_free=is_free if isinstance(is_free, bool) else None,
        cost_summary=cost_summary,
        source="luma",
    )


def search_luma_listings(
    *,
    city: str = "sf",
    max_results: int = 20,
) -> tuple[list[EventListing], str]:
    if max_results < 1 or max_results > 50:
        raise ValueError("max_results must be between 1 and 50")

    page_url = build_luma_city_url(city)
    html = http_get(page_url)
    initial = _parse_next_data(html)
    data = initial.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Luma page did not include event data")

    wrappers = data.get("events")
    if not isinstance(wrappers, list):
        raise RuntimeError("Luma page did not include events list")

    listings: list[EventListing] = []
    for wrapper in wrappers:
        if not isinstance(wrapper, dict):
            continue
        listing = _listing_from_wrapper(wrapper)
        if listing:
            listings.append(listing)
        if len(listings) >= max_results:
            break

    listings.sort(key=lambda item: item.start or "")
    return listings, page_url
