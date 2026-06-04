"""Meetup discovery via public find pages (Apollo state in __NEXT_DATA__).

No Meetup API subscription required. Parses Event objects from server-rendered data.
"""

from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import certifi

from app.services.eventbrite_service import EventListing

MEETUP_SITE_BASE = "https://www.meetup.com"
USER_AGENT = "WeightlossEventBot/1.0 (+https://github.com/weightloss)"

# Meetup find URLs use location slugs like us--ca--cupertino.
LOCATION_SLUGS: dict[str, str] = {
    "cupertino": "us--ca--cupertino",
    "mountain-view": "us--ca--mountain-view",
    "mountain view": "us--ca--mountain-view",
    "palo-alto": "us--ca--palo-alto",
    "palo alto": "us--ca--palo-alto",
    "sunnyvale": "us--ca--sunnyvale",
    "san-jose": "us--ca--san-jose",
    "san jose": "us--ca--san-jose",
    "san-francisco": "us--ca--san-francisco",
    "san francisco": "us--ca--san-francisco",
    "sf": "us--ca--san-francisco",
    "oakland": "us--ca--oakland",
    "berkeley": "us--ca--berkeley",
    "menlo-park": "us--ca--menlo-park",
    "menlo park": "us--ca--menlo-park",
    "redwood-city": "us--ca--redwood-city",
    "redwood city": "us--ca--redwood-city",
    "fremont": "us--ca--fremont",
    "online": "online",
}


def _https_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def _http_get(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
        method="GET",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=30,
            context=_https_context(),
        ) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(
            f"HTTP {exc.code} fetching {url}: {detail}",
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc.reason}") from exc


def resolve_meetup_location_slug(location: str) -> str:
    trimmed = location.strip().lower()
    if not trimmed:
        raise ValueError("location is required")
    if re.fullmatch(r"us--[\w-]+", trimmed) or trimmed == "online":
        return trimmed
    if trimmed in LOCATION_SLUGS:
        return LOCATION_SLUGS[trimmed]
    slug = trimmed.replace(" ", "-")
    if slug in LOCATION_SLUGS:
        return LOCATION_SLUGS[slug]
    return f"us--ca--{slug}"


def build_find_url(
    *,
    location: str,
    keywords: str = "",
    distance_miles: int | None = None,
) -> str:
    location_slug = resolve_meetup_location_slug(location)
    params: dict[str, str] = {
        "location": location_slug,
        "source": "EVENTS",
    }
    if keywords.strip():
        params["keywords"] = keywords.strip()
    if distance_miles is not None and distance_miles > 0:
        params["distance"] = str(distance_miles)
    return f"{MEETUP_SITE_BASE}/find/?{urllib.parse.urlencode(params)}"


def _parse_next_data(html: str) -> dict[str, Any]:
    match = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError("Meetup page did not include __NEXT_DATA__")
    payload = json.loads(match.group(1))
    page_props = payload.get("props", {}).get("pageProps", {})
    apollo = page_props.get("__APOLLO_STATE__")
    if not isinstance(apollo, dict):
        raise RuntimeError("Meetup page missing __APOLLO_STATE__")
    return apollo


def _deref(apollo: dict[str, Any], value: Any) -> Any:
    if isinstance(value, dict) and "__ref" in value:
        return apollo.get(value["__ref"])
    return value


def _venue_fields(venue: Any) -> tuple[str | None, str | None, str | None]:
    if not isinstance(venue, dict):
        return None, None, None
    name = venue.get("name")
    city = venue.get("city")
    region = venue.get("state") or venue.get("region")
    return (
        name if isinstance(name, str) else None,
        city if isinstance(city, str) else None,
        region if isinstance(region, str) else None,
    )


def _listing_from_event(apollo: dict[str, Any], event: dict[str, Any]) -> EventListing | None:
    title = event.get("title")
    event_url = event.get("eventUrl")
    event_id = event.get("id")
    if not isinstance(title, str) or not isinstance(event_url, str):
        return None
    if not isinstance(event_id, str):
        event_id = _extract_event_id_from_url(event_url) or event_url

    venue, city, region = _venue_fields(_deref(apollo, event.get("venue")))
    group = _deref(apollo, event.get("group"))
    group_name = group.get("name") if isinstance(group, dict) else None
    venue_display = venue
    if group_name and venue:
        venue_display = f"{venue} ({group_name})"
    elif group_name:
        venue_display = group_name

    fee = event.get("feeSettings")
    cost_summary = None
    if isinstance(fee, dict):
        amount = fee.get("amount")
        currency = fee.get("currency") or "USD"
        if amount is not None:
            cost_summary = f"{amount} {currency}"

    return EventListing(
        id=f"meetup:{event_id}",
        title=title.strip(),
        start=event.get("dateTime") if isinstance(event.get("dateTime"), str) else None,
        end=None,
        venue=venue_display,
        city=city,
        region=region,
        url=event_url,
        is_free=None,
        cost_summary=cost_summary,
        source="meetup",
    )


def _extract_event_id_from_url(url: str) -> str | None:
    match = re.search(r"/events/(\d+)", url)
    return match.group(1) if match else None


def _parse_events_from_apollo(
    apollo: dict[str, Any],
    *,
    max_results: int,
) -> list[EventListing]:
    listings: list[EventListing] = []
    for key, value in apollo.items():
        if not key.startswith("Event:") or not isinstance(value, dict):
            continue
        if value.get("__typename") != "Event":
            continue
        listing = _listing_from_event(apollo, value)
        if listing:
            listings.append(listing)
    listings.sort(key=lambda item: item.start or "")
    return listings[:max_results]


def search_meetup_listings(
    *,
    location: str,
    keywords: str = "",
    distance_miles: int | None = None,
    max_results: int = 20,
) -> tuple[list[EventListing], str]:
    if max_results < 1 or max_results > 50:
        raise ValueError("max_results must be between 1 and 50")

    find_url = build_find_url(
        location=location,
        keywords=keywords,
        distance_miles=distance_miles,
    )
    html = _http_get(find_url)
    apollo = _parse_next_data(html)
    listings = _parse_events_from_apollo(apollo, max_results=max_results)
    return listings, find_url
