import json

from langchain_core.tools import tool

from app.database import SessionLocal
from app.services.event_date_utils import parse_iso_date
from app.services.meetup_event_store import (
    list_stored_events,
    search_stored_events,
    vector_search_stored_events,
)


def _parse_optional_bool(value: str) -> bool:
    key = value.strip().lower()
    if key in {"true", "yes", "1"}:
        return True
    if key in {"false", "no", "0"}:
        return False
    raise ValueError(f"Expected true/false, got: {value}")


def _parse_date_range(
    start_date: str,
    end_date: str,
) -> tuple[object | None, object | None, str | None]:
    parsed_start = parse_iso_date(start_date) if start_date.strip() else None
    parsed_end = parse_iso_date(end_date) if end_date.strip() else None
    if (parsed_start is None) != (parsed_end is None):
        return None, None, "start_date and end_date must both be provided together."
    return parsed_start, parsed_end, None


@tool
def search_events(
    location: str = "cupertino",
    keywords: str = "",
    start_date: str = "",
    end_date: str = "",
    free_only: str = "",
    max_price_usd: str = "",
    max_results: int = 30,
) -> str:
    """Keyword search over synced Meetup events in the database."""
    parsed_start, parsed_end, error = _parse_date_range(start_date, end_date)
    if error:
        return json.dumps({"ok": False, "error": error}, indent=2)

    free_val: bool | None = None
    if free_only.strip():
        try:
            free_val = _parse_optional_bool(free_only)
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    price_cap: float | None = None
    price_key = max_price_usd.strip().lower()
    if price_key and price_key not in {"none", "clear", "null"}:
        try:
            price_cap = float(price_key)
        except ValueError:
            return json.dumps(
                {"ok": False, "error": f"Invalid max_price_usd: {max_price_usd}"},
                indent=2,
            )

    if max_results < 1 or max_results > 60:
        return json.dumps(
            {"ok": False, "error": "max_results must be between 1 and 60"},
            indent=2,
        )

    with SessionLocal() as db:
        payload = search_stored_events(
            db,
            location=location,
            keywords=keywords,
            start_date=parsed_start,
            end_date=parsed_end,
            free_only=free_val or False,
            max_price_usd=price_cap,
            max_results=max_results,
        )

    if payload["count"] == 0:
        payload["hint"] = (
            "No synced events matched. Ask the user to click Sync Meetup Events "
            f"for {payload['location']} in the event manager page."
        )

    return json.dumps(payload, indent=2)


@tool
def vector_search_events(
    query: str,
    location: str = "cupertino",
    start_date: str = "",
    end_date: str = "",
    max_results: int = 30,
) -> str:
    """Semantic search over synced events using embeddings (interests, vibe, topics)."""
    parsed_start, parsed_end, error = _parse_date_range(start_date, end_date)
    if error:
        return json.dumps({"ok": False, "error": error}, indent=2)

    if max_results < 1 or max_results > 60:
        return json.dumps(
            {"ok": False, "error": "max_results must be between 1 and 60"},
            indent=2,
        )

    try:
        with SessionLocal() as db:
            payload = vector_search_stored_events(
                db,
                query=query,
                location=location,
                start_date=parsed_start,
                end_date=parsed_end,
                max_results=max_results,
            )
    except ValueError as exc:
        return json.dumps({"ok": False, "error": str(exc)}, indent=2)

    if payload["count"] == 0:
        payload["hint"] = (
            "No embedded events matched. Sync events first, then retry vector search."
        )

    return json.dumps(payload, indent=2)


@tool
def list_events(
    location: str = "cupertino",
    start_date: str = "",
    end_date: str = "",
    max_results: int = 200,
) -> str:
    """Load synced events for a location, optionally filtered by date range."""
    parsed_start, parsed_end, error = _parse_date_range(start_date, end_date)
    if error:
        return json.dumps({"ok": False, "error": error}, indent=2)

    if max_results < 1 or max_results > 200:
        return json.dumps(
            {"ok": False, "error": "max_results must be between 1 and 200"},
            indent=2,
        )

    with SessionLocal() as db:
        payload = list_stored_events(
            db,
            location=location,
            start_date=parsed_start,
            end_date=parsed_end,
            max_results=max_results,
        )

    return json.dumps(payload, indent=2)


EVENT_MANAGER_TOOLS = [search_events, vector_search_events, list_events]
