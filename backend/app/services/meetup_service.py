"""Meetup discovery via public find pages and GraphQL cursor pagination.

Fetches the SSR find page for the first batch, then POSTs to Meetup's /gql2
endpoint with the endCursor until all pages are loaded.
"""

from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Literal

import certifi

from app.services.event_listing import EventListing

MEETUP_SITE_BASE = "https://www.meetup.com"
MEETUP_GQL_URL = f"{MEETUP_SITE_BASE}/gql2"
USER_AGENT = "WeightlossEventBot/1.0 (+https://github.com/weightloss)"

DEFAULT_PAGE_SIZE = 12
MAX_PAGES_SAFETY = 50
MAX_EVENTS_SAFETY = 500

SearchKind = Literal["recommendedEvents", "eventSearch"]

RECOMMENDED_EVENTS_QUERY = """
query recommendedEventsPage(
  $lat: Float!
  $lon: Float!
  $startDateRange: String
  $endDateRange: String
  $first: Int
  $after: String
  $radius: Float
  $doConsolidateEvents: Boolean
  $doPromotePaypalEvents: Boolean
  $indexAlias: String
  $sortField: RecommendedEventsSortField
) {
  result: recommendedEvents(
    filter: {
      lat: $lat
      lon: $lon
      startDateRange: $startDateRange
      endDateRange: $endDateRange
      doConsolidateEvents: $doConsolidateEvents
      doPromotePaypalEvents: $doPromotePaypalEvents
      indexAlias: $indexAlias
      radius: $radius
    }
    first: $first
    after: $after
    sort: { sortField: $sortField }
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
    edges {
      node {
        id
        title
        dateTime
        eventUrl
        feeSettings {
          amount
          currency
        }
        group {
          name
        }
        venue {
          name
          city
          state
        }
      }
    }
  }
}
"""

EVENT_SEARCH_QUERY = """
query eventSearchPage(
  $query: String!
  $lat: Float!
  $lon: Float!
  $city: String
  $state: String
  $country: String
  $zip: String
  $startDateRange: DateTime
  $endDateRange: DateTime
  $radius: Float
  $first: Int
  $after: String
  $doConsolidateEvents: Boolean
  $sortField: KeywordSortField
) {
  results: eventSearch(
    filter: {
      query: $query
      lat: $lat
      lon: $lon
      city: $city
      state: $state
      country: $country
      zip: $zip
      startDateRange: $startDateRange
      endDateRange: $endDateRange
      radius: $radius
      doConsolidateEvents: $doConsolidateEvents
    }
    first: $first
    after: $after
    sort: { sortField: $sortField }
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
    edges {
      node {
        id
        title
        dateTime
        eventUrl
        feeSettings {
          amount
          currency
        }
        group {
          name
        }
        venue {
          name
          city
          state
        }
      }
    }
  }
}
"""

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


@dataclass(frozen=True)
class _SearchContext:
    kind: SearchKind
    operation_name: str
    query: str
    result_key: str
    filter_params: dict[str, Any]
    sort_field: str | None
    page_info: dict[str, Any]


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


def _gql_post(
    *,
    operation_name: str,
    query: str,
    variables: dict[str, Any],
    referer: str,
) -> dict[str, Any]:
    body = json.dumps(
        {
            "operationName": operation_name,
            "query": query,
            "variables": variables,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        MEETUP_GQL_URL,
        data=body,
        method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": MEETUP_SITE_BASE,
            "Referer": referer,
        },
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=30,
            context=_https_context(),
        ) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(
            f"HTTP {exc.code} posting to Meetup GraphQL: {detail}",
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Meetup GraphQL request failed: {exc.reason}") from exc

    errors = payload.get("errors")
    if errors:
        message = errors[0].get("message", "Unknown GraphQL error")
        raise RuntimeError(f"Meetup GraphQL error: {message}")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Meetup GraphQL response missing data")
    return data


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


def _extract_event_id_from_url(url: str) -> str | None:
    match = re.search(r"/events/(\d+)", url)
    return match.group(1) if match else None


def _cost_summary_from_fee(fee: Any) -> str | None:
    if not isinstance(fee, dict):
        return None
    amount = fee.get("amount")
    currency = fee.get("currency") or "USD"
    if amount is not None:
        return f"{amount} {currency}"
    return None


def _listing_from_event_record(
    event: dict[str, Any],
    *,
    apollo: dict[str, Any] | None = None,
) -> EventListing | None:
    title = event.get("title")
    event_url = event.get("eventUrl")
    event_id = event.get("id")
    if not isinstance(title, str) or not isinstance(event_url, str):
        return None
    if not isinstance(event_id, str):
        event_id = _extract_event_id_from_url(event_url) or event_url

    venue_raw = event.get("venue")
    if apollo is not None:
        venue_raw = _deref(apollo, venue_raw)
    venue, city, region = _venue_fields(venue_raw)

    group_raw = event.get("group")
    if apollo is not None:
        group_raw = _deref(apollo, group_raw)
    group_name = group_raw.get("name") if isinstance(group_raw, dict) else None
    venue_display = venue
    if group_name and venue:
        venue_display = f"{venue} ({group_name})"
    elif group_name:
        venue_display = group_name

    fee = event.get("feeSettings")
    if apollo is not None:
        fee = _deref(apollo, fee)

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
        cost_summary=_cost_summary_from_fee(fee),
        source="meetup",
    )


def _listing_from_gql_node(node: dict[str, Any]) -> EventListing | None:
    return _listing_from_event_record(node)


def _search_context_from_root(root: dict[str, Any]) -> _SearchContext:
    for key, connection in root.items():
        if not isinstance(connection, dict):
            continue
        if key.startswith("recommendedEvents:"):
            params = json.loads(key.split(":", 1)[1])
            return _SearchContext(
                kind="recommendedEvents",
                operation_name="recommendedEventsPage",
                query=RECOMMENDED_EVENTS_QUERY,
                result_key="result",
                filter_params=params.get("filter", {}),
                sort_field=(params.get("sort") or {}).get("sortField"),
                page_info=connection.get("pageInfo", {}),
            )
        if key.startswith("eventSearch:"):
            params = json.loads(key.split(":", 1)[1])
            return _SearchContext(
                kind="eventSearch",
                operation_name="eventSearchPage",
                query=EVENT_SEARCH_QUERY,
                result_key="results",
                filter_params=params.get("filter", {}),
                sort_field=(params.get("sort") or {}).get("sortField"),
                page_info=connection.get("pageInfo", {}),
            )
    raise RuntimeError("Meetup page did not include an event search connection")


def _listings_from_connection(
    apollo: dict[str, Any],
    connection: dict[str, Any],
) -> list[EventListing]:
    listings: list[EventListing] = []
    edges = connection.get("edges")
    if not isinstance(edges, list):
        return listings

    for edge in edges:
        edge_obj = _deref(apollo, edge)
        if not isinstance(edge_obj, dict):
            continue
        node = edge_obj.get("node")
        if isinstance(node, dict) and "title" in node:
            listing = _listing_from_event_record(node, apollo=apollo)
        else:
            event = _deref(apollo, node)
            if not isinstance(event, dict):
                continue
            listing = _listing_from_event_record(event, apollo=apollo)
        if listing:
            listings.append(listing)
    return listings


def _gql_variables(
    context: _SearchContext,
    *,
    after: str | None,
    page_size: int,
) -> dict[str, Any]:
    variables = dict(context.filter_params)
    variables["sortField"] = context.sort_field
    variables["first"] = page_size
    if after:
        variables["after"] = after
    return variables


def _fetch_gql_page(
    context: _SearchContext,
    *,
    after: str | None,
    referer: str,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict[str, Any]:
    data = _gql_post(
        operation_name=context.operation_name,
        query=context.query,
        variables=_gql_variables(context, after=after, page_size=page_size),
        referer=referer,
    )
    result = data.get(context.result_key)
    if not isinstance(result, dict):
        raise RuntimeError("Meetup GraphQL page missing result connection")
    return result


def _listings_from_gql_page(page: dict[str, Any]) -> list[EventListing]:
    listings: list[EventListing] = []
    edges = page.get("edges")
    if not isinstance(edges, list):
        return listings
    for edge in edges:
        node = edge.get("node") if isinstance(edge, dict) else None
        if not isinstance(node, dict):
            continue
        listing = _listing_from_gql_node(node)
        if listing:
            listings.append(listing)
    return listings


def _merge_listings(
    collected: list[EventListing],
    seen_ids: set[str],
    new_listings: list[EventListing],
) -> None:
    for listing in new_listings:
        if listing.id in seen_ids:
            continue
        seen_ids.add(listing.id)
        collected.append(listing)


def _paginate_all_listings(
    apollo: dict[str, Any],
    context: _SearchContext,
    *,
    referer: str,
    max_results: int | None,
) -> list[EventListing]:
    collected: list[EventListing] = []
    for _page, batch in _iter_listing_batches(apollo, context, referer=referer):
        collected.extend(batch)
        if max_results is not None and len(collected) >= max_results:
            return collected[:max_results]
    collected.sort(key=lambda item: item.start or "")
    if max_results is not None:
        return collected[:max_results]
    return collected


def _iter_listing_batches(
    apollo: dict[str, Any],
    context: _SearchContext,
    *,
    referer: str,
) -> Iterator[tuple[int, list[EventListing]]]:
    root = apollo.get("ROOT_QUERY", {})
    connection = None
    for key, value in root.items():
        if key.startswith(f"{context.kind}:"):
            connection = value
            break
    if not isinstance(connection, dict):
        raise RuntimeError("Meetup page missing search connection data")

    seen_ids: set[str] = set()
    first_batch = _listings_from_connection(apollo, connection)
    unique_first: list[EventListing] = []
    _merge_listings(unique_first, seen_ids, first_batch)
    if unique_first:
        yield 1, unique_first

    cursor = context.page_info.get("endCursor")
    has_next = bool(context.page_info.get("hasNextPage"))
    pages_fetched = 0
    total_collected = len(unique_first)

    while has_next and cursor and pages_fetched < MAX_PAGES_SAFETY:
        if total_collected >= MAX_EVENTS_SAFETY:
            break

        page = _fetch_gql_page(context, after=str(cursor), referer=referer)
        batch: list[EventListing] = []
        _merge_listings(batch, seen_ids, _listings_from_gql_page(page))
        pages_fetched += 1
        page_num = pages_fetched + 1
        if batch:
            total_collected += len(batch)
            yield page_num, batch

        page_info = page.get("pageInfo", {})
        has_next = bool(page_info.get("hasNextPage"))
        cursor = page_info.get("endCursor")


def iter_meetup_listing_batches(
    *,
    location: str,
    keywords: str = "",
    distance_miles: int | None = None,
) -> Iterator[tuple[int, list[EventListing]]]:
    find_url = build_find_url(
        location=location,
        keywords=keywords,
        distance_miles=distance_miles,
    )
    html = _http_get(find_url)
    apollo = _parse_next_data(html)
    context = _search_context_from_root(apollo.get("ROOT_QUERY", {}))
    yield from _iter_listing_batches(apollo, context, referer=find_url)


def _parse_events_from_apollo(
    apollo: dict[str, Any],
    *,
    max_results: int | None = None,
) -> list[EventListing]:
    """Parse events from a standalone Apollo cache (used in tests)."""
    listings: list[EventListing] = []
    for key, value in apollo.items():
        if not key.startswith("Event:") or not isinstance(value, dict):
            continue
        if value.get("__typename") != "Event":
            continue
        listing = _listing_from_event_record(value, apollo=apollo)
        if listing:
            listings.append(listing)
    listings.sort(key=lambda item: item.start or "")
    if max_results is not None:
        return listings[:max_results]
    return listings


def search_meetup_listings(
    *,
    location: str,
    keywords: str = "",
    distance_miles: int | None = None,
    max_results: int | None = None,
) -> tuple[list[EventListing], str]:
    if max_results is not None and (max_results < 1 or max_results > MAX_EVENTS_SAFETY):
        raise ValueError(f"max_results must be between 1 and {MAX_EVENTS_SAFETY}")

    find_url = build_find_url(
        location=location,
        keywords=keywords,
        distance_miles=distance_miles,
    )
    html = _http_get(find_url)
    apollo = _parse_next_data(html)
    context = _search_context_from_root(apollo.get("ROOT_QUERY", {}))
    listings = _paginate_all_listings(
        apollo,
        context,
        referer=find_url,
        max_results=max_results,
    )
    return listings, find_url
