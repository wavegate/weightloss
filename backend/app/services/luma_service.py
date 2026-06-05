"""Luma discovery via public pages (__NEXT_DATA__ initialData)."""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app.services.event_fetch import http_get
from app.services.eventbrite_service import EventListing

LUMA_SITE_BASE = "https://lu.ma"
LUMA_DISCOVER_URL = f"{LUMA_SITE_BASE}/discover"

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

LUMA_CATEGORY_SLUGS = ("tech", "ai")


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


def _collect_event_wrappers(node: Any, found: list[dict[str, Any]]) -> None:
    if isinstance(node, dict):
        event = node.get("event")
        if isinstance(event, dict) and isinstance(event.get("name"), str):
            if isinstance(event.get("url"), str):
                found.append(node)
        for value in node.values():
            _collect_event_wrappers(value, found)
    elif isinstance(node, list):
        for item in node:
            _collect_event_wrappers(item, found)


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


def _fetch_listings_from_url(url: str, *, max_results: int) -> list[EventListing]:
    html = http_get(url)
    initial = _parse_next_data(html)
    wrappers: list[dict[str, Any]] = []
    _collect_event_wrappers(initial, wrappers)

    listings: list[EventListing] = []
    seen_ids: set[str] = set()
    for wrapper in wrappers:
        listing = _listing_from_wrapper(wrapper)
        if not listing or listing.id in seen_ids:
            continue
        seen_ids.add(listing.id)
        listings.append(listing)
        if len(listings) >= max_results:
            break
    return listings


def _luma_fetch_urls(city: str, *, broad: bool) -> list[str]:
    urls = [build_luma_city_url(city)]
    if broad:
        urls.append(LUMA_DISCOVER_URL)
        for category in LUMA_CATEGORY_SLUGS:
            urls.append(f"{LUMA_SITE_BASE}/{category}")
    return urls


def search_luma_listings(
    *,
    city: str = "sf",
    max_results: int = 20,
    broad: bool = False,
) -> tuple[list[EventListing], str]:
    if max_results < 1 or max_results > 80:
        raise ValueError("max_results must be between 1 and 80")

    urls = _luma_fetch_urls(city, broad=broad)
    per_url_cap = max(max_results, 40) if broad else max_results

    listings: list[EventListing] = []
    seen_ids: set[str] = set()

    with ThreadPoolExecutor(max_workers=len(urls)) as pool:
        futures = {
            pool.submit(_fetch_listings_from_url, url, max_results=per_url_cap): url
            for url in urls
        }
        for future in as_completed(futures):
            try:
                batch = future.result()
            except Exception:
                continue
            for listing in batch:
                if listing.id in seen_ids:
                    continue
                seen_ids.add(listing.id)
                listings.append(listing)

    listings.sort(key=lambda item: item.start or "")
    page_url = urls[0] if len(urls) == 1 else ", ".join(urls)
    return listings[:max_results], page_url
