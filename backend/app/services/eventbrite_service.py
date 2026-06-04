"""Eventbrite discovery via public browse pages (JSON-LD).

Eventbrite shut down GET /v3/events/search/ in 2020. Public listing pages still
expose an ItemList in JSON-LD; EVENTBRITE_API_KEY enriches individual events via
GET /v3/events/{id}/ when available.
"""

from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

import certifi

from app.config import get_settings

EVENTBRITE_API_BASE = "https://www.eventbriteapi.com/v3"
EVENTBRITE_SITE_BASE = "https://www.eventbrite.com"
USER_AGENT = "WeightlossEventBot/1.0 (+https://github.com/weightloss)"

EVENT_TYPES = frozenset(
    {"Event", "BusinessEvent", "MusicEvent", "EducationEvent"},
)

# Bay Area slugs used by Eventbrite /d/{location}/ paths.
LOCATION_SLUGS: dict[str, str] = {
    "cupertino": "ca--san-jose",
    "mountain-view": "ca--mountain-view",
    "mountain view": "ca--mountain-view",
    "palo-alto": "ca--palo-alto",
    "palo alto": "ca--palo-alto",
    "sunnyvale": "ca--sunnyvale",
    "san-jose": "ca--san-jose",
    "san jose": "ca--san-jose",
    "san-francisco": "ca--san-francisco",
    "san francisco": "ca--san-francisco",
    "sf": "ca--san-francisco",
    "oakland": "ca--oakland",
    "berkeley": "ca--berkeley",
    "menlo-park": "ca--menlo-park",
    "menlo park": "ca--menlo-park",
    "redwood-city": "ca--redwood-city",
    "redwood city": "ca--redwood-city",
    "online": "online",
}

DATE_FILTER_SLUGS = frozenset(
    {
        "events--today",
        "events--tomorrow",
        "events--this-weekend",
        "free--events",
    },
)

CATEGORY_SLUGS = frozenset(
    {
        "events",
        "tech",
        "music",
        "food--drink",
        "health",
        "sports--fitness",
        "arts--entertainment",
        "family--education",
        "business--professional",
        "science--tech",
        "community--culture",
        "networking",
    },
)


@dataclass(frozen=True)
class EventListing:
    id: str
    title: str
    start: str | None
    end: str | None
    venue: str | None
    city: str | None
    region: str | None
    url: str
    is_free: bool | None
    cost_summary: str | None
    source: str = "eventbrite"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "start": self.start,
            "end": self.end,
            "venue": self.venue,
            "city": self.city,
            "region": self.region,
            "url": self.url,
            "is_free": self.is_free,
            "cost_summary": self.cost_summary,
            "source": self.source,
        }


def _https_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def _http_get(url: str, *, headers: dict[str, str] | None = None) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, **(headers or {})},
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


def resolve_location_slug(location: str) -> str:
    trimmed = location.strip().lower()
    if not trimmed:
        raise ValueError("location is required")
    if re.fullmatch(r"[a-z]{2}--[\w-]+", trimmed):
        return trimmed
    if trimmed in LOCATION_SLUGS:
        return LOCATION_SLUGS[trimmed]
    slug = trimmed.replace(" ", "-")
    if slug in LOCATION_SLUGS:
        return LOCATION_SLUGS[slug]
    return f"ca--{slug}"


def _normalize_category(category: str) -> str:
    slug = category.strip().lower().replace(" ", "-")
    if slug in DATE_FILTER_SLUGS:
        return slug
    if slug in CATEGORY_SLUGS:
        return slug
    return "events"


def build_browse_url(
    *,
    location: str,
    category: str = "events",
    page: int = 1,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    location_slug = resolve_location_slug(location)
    category_slug = _normalize_category(category)
    path = f"{EVENTBRITE_SITE_BASE}/d/{location_slug}/{category_slug}/"
    params: dict[str, str] = {}
    if page > 1:
        params["page"] = str(page)
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if params:
        return f"{path}?{urllib.parse.urlencode(params)}"
    return path


def _extract_event_id(url: str) -> str | None:
    match = re.search(r"-tickets-(\d+)(?:\?|$)", url)
    return match.group(1) if match else None


def _parse_item_list(html: str) -> list[dict[str, Any]]:
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    for block in blocks:
        parsed = json.loads(block)
        if isinstance(parsed, dict) and parsed.get("@type") == "ItemList":
            elements = parsed.get("itemListElement") or []
            items: list[dict[str, Any]] = []
            for element in elements:
                if not isinstance(element, dict):
                    continue
                item = element.get("item")
                if isinstance(item, dict):
                    items.append(item)
            return items
    return []


def _place_fields(location: dict[str, Any] | None) -> tuple[str | None, str | None, str | None]:
    if not location:
        return None, None, None
    venue = location.get("name")
    address = location.get("address") or {}
    if not isinstance(address, dict):
        return venue, None, None
    return (
        venue if isinstance(venue, str) else None,
        address.get("addressLocality"),
        address.get("addressRegion"),
    )


def _listing_from_item(item: dict[str, Any]) -> EventListing | None:
    url = item.get("url")
    name = item.get("name")
    if not isinstance(url, str) or not isinstance(name, str):
        return None
    event_id = _extract_event_id(url) or url
    venue, city, region = _place_fields(
        item.get("location") if isinstance(item.get("location"), dict) else None,
    )
    return EventListing(
        id=f"eventbrite:{event_id}",
        title=name.strip(),
        start=item.get("startDate") if isinstance(item.get("startDate"), str) else None,
        end=item.get("endDate") if isinstance(item.get("endDate"), str) else None,
        venue=venue,
        city=city if isinstance(city, str) else None,
        region=region if isinstance(region, str) else None,
        url=url,
        is_free=None,
        cost_summary=None,
    )


def _api_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": USER_AGENT,
    }


def _enrich_from_api(listing: EventListing, token: str) -> EventListing:
    event_id = _extract_event_id(listing.url)
    if not event_id:
        return listing

    url = (
        f"{EVENTBRITE_API_BASE}/events/{event_id}/"
        f"?expand=venue,organizer,ticket_availability"
    )
    try:
        raw = _http_get(url, headers=_api_headers(token))
    except RuntimeError:
        return listing

    payload = json.loads(raw)
    is_free = payload.get("is_free")
    cost_summary = None
    ticket = payload.get("ticket_availability") or {}
    if isinstance(ticket, dict):
        min_price = ticket.get("minimum_ticket_price")
        max_price = ticket.get("maximum_ticket_price")
        currency = (min_price or {}).get("currency") if isinstance(min_price, dict) else None
        if isinstance(min_price, dict) and min_price.get("major_value") is not None:
            low = min_price.get("major_value")
            high = (
                max_price.get("major_value")
                if isinstance(max_price, dict)
                else low
            )
            cost_summary = f"{low}-{high} {currency or 'USD'}".strip()
        elif is_free is True:
            cost_summary = "free"

    venue = listing.venue
    city = listing.city
    region = listing.region
    venue_payload = payload.get("venue")
    if isinstance(venue_payload, dict):
        venue = venue or venue_payload.get("name")
        address = venue_payload.get("address") or {}
        if isinstance(address, dict):
            city = city or address.get("city")
            region = region or address.get("region")

    start = listing.start
    if isinstance(payload.get("start"), dict):
        utc = payload["start"].get("utc")
        if isinstance(utc, str):
            start = utc

    return EventListing(
        id=listing.id,
        title=listing.title,
        start=start,
        end=listing.end,
        venue=venue if isinstance(venue, str) else listing.venue,
        city=city if isinstance(city, str) else listing.city,
        region=region if isinstance(region, str) else listing.region,
        url=listing.url,
        is_free=is_free if isinstance(is_free, bool) else listing.is_free,
        cost_summary=cost_summary or listing.cost_summary,
    )


def search_eventbrite_listings(
    *,
    location: str,
    category: str = "events",
    page: int = 1,
    start_date: str | None = None,
    end_date: str | None = None,
    max_results: int = 20,
    enrich_with_api: bool = True,
) -> tuple[list[EventListing], str]:
    """Return normalized listings and the browse URL that was fetched."""
    if page < 1:
        raise ValueError("page must be >= 1")
    if max_results < 1 or max_results > 40:
        raise ValueError("max_results must be between 1 and 40")

    browse_url = build_browse_url(
        location=location,
        category=category,
        page=page,
        start_date=start_date,
        end_date=end_date,
    )
    html = _http_get(browse_url)
    items = _parse_item_list(html)

    listings: list[EventListing] = []
    for item in items:
        listing = _listing_from_item(item)
        if listing:
            listings.append(listing)
        if len(listings) >= max_results:
            break

    token = get_settings().eventbrite_api_key
    if enrich_with_api and token:
        cap = min(5, len(listings))
        listings = [
            _enrich_from_api(listings[i], token) if i < cap else listings[i]
            for i in range(len(listings))
        ]

    return listings, browse_url
