import json

from langchain_core.tools import tool

from app.services.event_aggregator import aggregate_events


@tool
def search_events(
    location: str = "cupertino",
    keywords: str = "",
    timing: str = "upcoming",
    max_per_source: int = 12,
    max_total: int = 30,
) -> str:
    """Search all event platforms in parallel (Meetup, Eventbrite, Luma, Funcheap).

    Always use this first for event discovery. Fetches every source concurrently,
    merges results, and dedupes likely duplicates.

    location: Bay Area city/area (default cupertino).
    keywords: Optional topic filter passed to Meetup (e.g. tech, hiking).
    timing: upcoming (default), today, weekend, or free — adjusts Eventbrite/Funcheap filters.
    max_per_source: Max events to pull from each platform before merge.
    max_total: Max events returned after dedupe.
    """
    payload = aggregate_events(
        location=location,
        keywords=keywords,
        timing=timing,
        max_per_source=max_per_source,
        max_total=max_total,
    )
    return json.dumps(payload, indent=2)


EVENT_MANAGER_TOOLS = [search_events]
