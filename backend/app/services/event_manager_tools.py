import json
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from pydantic import ValidationError

from app.database import SessionLocal
from app.services.event_aggregator import aggregate_events_from_resolved
from app.services.event_preferences_service import (
    get_or_create_preferences,
    merge_preferences_update,
    preference_options_payload,
    preferences_to_read,
    resolve_search_params,
    upsert_preferences,
)
from app.services.event_date_utils import parse_iso_date


def _user_id(config: RunnableConfig) -> str:
    user_id = (config.get("configurable") or {}).get("user_id")
    if not user_id:
        raise ValueError("Missing user_id in agent configuration")
    return user_id


@tool
def get_event_preferences(
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Load the user's saved event discovery preferences (location, interests, cost, timing)."""
    with SessionLocal() as db:
        row = get_or_create_preferences(db, _user_id(config))
        payload = preferences_to_read(row).model_dump(mode="json")
    payload["note"] = (
        "Use these when the user omits location/timing/topics. "
        "If their message implies different prefs, call update_event_preferences before searching."
    )
    return json.dumps(payload, indent=2)


@tool
def get_event_preference_options() -> str:
    """List valid IDs for home_location, default_timing, and categories when updating prefs."""
    return json.dumps(preference_options_payload(), indent=2)


def _parse_optional_bool(value: str) -> bool | None:
    key = value.strip().lower()
    if not key:
        return None
    if key in {"true", "yes", "1"}:
        return True
    if key in {"false", "no", "0"}:
        return False
    raise ValueError(f"Expected true/false, got: {value}")


def _parse_categories(value: str) -> list[str] | None:
    key = value.strip().lower()
    if not key:
        return None
    if key in {"clear", "none", "[]"}:
        return []
    return [part.strip().lower() for part in value.split(",") if part.strip()]


@tool
def update_event_preferences(
    config: Annotated[RunnableConfig, InjectedToolArg],
    home_location: str = "",
    distance_miles: int = 0,
    default_timing: str = "",
    start_date: str = "",
    end_date: str = "",
    clear_dates: bool = False,
    free_only: str = "",
    max_price_usd: str = "",
    interest_keywords: str = "",
    clear_interest_keywords: bool = False,
    categories: str = "",
) -> str:
    """Update the user's saved event discovery preferences (same fields as the preferences UI).

    Call proactively whenever the user states or implies location, timing, budget, categories, or interests
    — including inside a search request — not only when they ask to "save" settings.
    Only pass fields to change; omitted fields keep current values.
    Call get_event_preference_options if you need valid location/timing/category IDs.

    home_location: Bay Area city id (e.g. cupertino, san-francisco).
    distance_miles: Search radius 5–100; pass 0 to leave unchanged.
    default_timing: upcoming, today, weekend, free, or date-range.
    start_date / end_date: YYYY-MM-DD when using date-range; both required together.
    clear_dates: Set true to drop a saved date range and use upcoming timing.
    free_only: "true" or "false".
    max_price_usd: Numeric cap, or "none" to remove budget limit.
    interest_keywords: Topic keywords merged into searches; use clear_interest_keywords to wipe.
    categories: Comma-separated category ids (e.g. tech,music), or "clear" for none.
    """
    updates: dict = {}
    if home_location.strip():
        updates["home_location"] = home_location.strip().lower()
    if distance_miles > 0:
        updates["distance_miles"] = distance_miles
    if default_timing.strip():
        updates["default_timing"] = default_timing.strip().lower()
    if clear_dates:
        updates["default_timing"] = "upcoming"
        updates["start_date"] = None
        updates["end_date"] = None
    else:
        parsed_start = parse_iso_date(start_date) if start_date.strip() else None
        parsed_end = parse_iso_date(end_date) if end_date.strip() else None
        if parsed_start is not None:
            updates["start_date"] = parsed_start
        if parsed_end is not None:
            updates["end_date"] = parsed_end
    free_val = _parse_optional_bool(free_only)
    if free_val is not None:
        updates["free_only"] = free_val
    price_key = max_price_usd.strip().lower()
    if price_key:
        if price_key in {"none", "clear", "null"}:
            updates["max_price_usd"] = None
        else:
            updates["max_price_usd"] = float(price_key)
    if clear_interest_keywords:
        updates["interest_keywords"] = ""
    elif interest_keywords.strip():
        updates["interest_keywords"] = interest_keywords.strip()
    parsed_categories = _parse_categories(categories)
    if parsed_categories is not None:
        updates["categories"] = parsed_categories

    with SessionLocal() as db:
        row = get_or_create_preferences(db, _user_id(config))
        try:
            payload = merge_preferences_update(row, **updates)
            row = upsert_preferences(db, _user_id(config), payload)
            saved = preferences_to_read(row).model_dump(mode="json")
        except (ValidationError, ValueError) as exc:
            return json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "hint": "Call get_event_preference_options for valid IDs.",
                },
                indent=2,
            )

    return json.dumps(
        {
            "ok": True,
            "message": "Preferences saved. Future searches use these defaults unless overridden.",
            "preferences": saved,
        },
        indent=2,
        default=str,
    )


@tool
def search_events(
    config: Annotated[RunnableConfig, InjectedToolArg],
    location: str = "",
    keywords: str = "",
    timing: str = "",
    start_date: str = "",
    end_date: str = "",
    max_per_source: int = 12,
    max_total: int = 30,
) -> str:
    """Search all event platforms in parallel (Meetup, Eventbrite, Luma, Funcheap).

    Uses saved user preferences as defaults for empty location/keywords/timing/dates.
    Fetches every source concurrently, merges, dedupes, and applies cost/category filters.

    location: Override home area (e.g. cupertino, mountain-view). Empty = saved preference.
    keywords: Override topic keywords. Empty = saved interests + categories.
    timing: Override timing (upcoming, today, weekend, free, date-range). Empty = saved.
    start_date / end_date: YYYY-MM-DD range override. Empty = saved (when timing is date-range).
    max_per_source: Max events per platform before merge.
    max_total: Max events returned after filters.
    """
    with SessionLocal() as db:
        row = get_or_create_preferences(db, _user_id(config))
        resolved = resolve_search_params(
            row,
            location=location,
            keywords=keywords,
            timing=timing,
            start_date=start_date,
            end_date=end_date,
        )
    payload = aggregate_events_from_resolved(
        resolved,
        max_per_source=max_per_source,
        max_total=max_total,
    )
    return json.dumps(payload, indent=2)


EVENT_MANAGER_TOOLS = [
    get_event_preferences,
    get_event_preference_options,
    update_event_preferences,
    search_events,
]
