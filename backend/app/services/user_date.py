from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain_core.runnables import RunnableConfig

DEFAULT_TIMEZONE = "UTC"


def resolve_user_local_date_from_header(header_value: str | None) -> date:
    if header_value:
        return date.fromisoformat(header_value)
    return date.today()


def resolve_user_timezone_from_header(header_value: str | None) -> str:
    if header_value and header_value.strip():
        return header_value.strip()
    return DEFAULT_TIMEZONE


def resolve_user_local_date(config: RunnableConfig) -> date:
    value = (config.get("configurable") or {}).get("user_local_date")
    return resolve_user_local_date_from_header(
        str(value) if value is not None else None
    )


def resolve_user_timezone(config: RunnableConfig) -> str:
    value = (config.get("configurable") or {}).get("user_timezone")
    return resolve_user_timezone_from_header(
        str(value) if value is not None else None
    )


def _zone(timezone: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_TIMEZONE)


def calendar_date_in_timezone(
    stored: date,
    *,
    source_timezone: str,
    target_timezone: str,
) -> date:
    """Interpret a calendar date as midnight in source TZ, return calendar date in target TZ."""
    source = _zone(source_timezone)
    target = _zone(target_timezone)
    instant = datetime(stored.year, stored.month, stored.day, tzinfo=source)
    return instant.astimezone(target).date()


def effective_local_calendar_date(
    stored: date,
    *,
    user_local_today: date,
    user_timezone: str,
) -> date:
    """Map a stored DB date to the user's local calendar day.

    New entries use the browser's local calendar date as stored.
    Legacy entries used UTC calendar dates from toISOString(); when the stored
    date is ahead of local today, reinterpret as UTC midnight → local date.
    """
    as_local = stored
    as_from_utc = calendar_date_in_timezone(
        stored,
        source_timezone="UTC",
        target_timezone=user_timezone,
    )
    if stored > user_local_today and as_from_utc <= user_local_today:
        return as_from_utc
    return as_local
