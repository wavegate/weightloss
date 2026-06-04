"""SF Funcheap discovery via public listing pages (HTML parsing)."""

from __future__ import annotations

import html as html_lib
import re

from app.services.event_fetch import http_get
from app.services.eventbrite_service import EventListing

FUNCHEAP_SITE_BASE = "https://sf.funcheap.com"

FILTER_PATHS: dict[str, str] = {
    "today": "/today/",
    "weekend": "/weekend/",
    "home": "/",
}

_EVENT_BLOCK = re.compile(
    r'entry-title"><a href="([^"]+)"[^>]*>(.*?)</a>\s*</span>\s*'
    r'<div class="meta[^"]*"[^>]*data-event-date="([^"]*)"[^>]*data-event-date-end="([^"]*)"[^>]*>'
    r"(.*?)<div class=\"thumbnail-wrapper\">",
    re.DOTALL | re.IGNORECASE,
)


def resolve_funcheap_filter(filter_name: str) -> str:
    key = filter_name.strip().lower().replace(" ", "-")
    if key in FILTER_PATHS:
        return key
    if key in {"this-weekend", "events--this-weekend"}:
        return "weekend"
    if key in {"events--today", "events-today"}:
        return "today"
    return "today"


def build_funcheap_url(filter_name: str) -> str:
    key = resolve_funcheap_filter(filter_name)
    return f"{FUNCHEAP_SITE_BASE}{FILTER_PATHS[key]}"


def _clean_title(raw: str) -> str:
    without_tags = re.sub(r"<[^>]+>", "", raw)
    return html_lib.unescape(without_tags).strip()


def _parse_listings(html: str, *, max_results: int) -> list[EventListing]:
    listings: list[EventListing] = []
    for match in _EVENT_BLOCK.finditer(html):
        url, title_raw, start, end, meta = match.groups()
        if "/city-guide/" in url:
            continue
        title = _clean_title(title_raw)
        if not title:
            continue

        cost_summary = None
        is_free = None
        if "FREE" in meta.upper():
            is_free = True
            cost_summary = "free"

        venue_match = re.search(r"<span>([^<]+)</span>\s*</div>", meta)
        venue = venue_match.group(1).strip() if venue_match else None

        event_id = url.rstrip("/").split("/")[-1]
        listings.append(
            EventListing(
                id=f"funcheap:{event_id}",
                title=title,
                start=start.replace(" ", "T") if start else None,
                end=end.replace(" ", "T") if end else None,
                venue=venue,
                city="San Francisco",
                region="CA",
                url=url,
                is_free=is_free,
                cost_summary=cost_summary,
                source="funcheap",
            ),
        )
        if len(listings) >= max_results:
            break
    return listings


def search_funcheap_listings(
    *,
    filter_name: str = "today",
    max_results: int = 20,
) -> tuple[list[EventListing], str]:
    if max_results < 1 or max_results > 50:
        raise ValueError("max_results must be between 1 and 50")

    page_url = build_funcheap_url(filter_name)
    html = http_get(page_url)
    listings = _parse_listings(html, max_results=max_results)
    return listings, page_url
