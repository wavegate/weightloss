from datetime import date

from app.services.event_date_utils import listing_in_date_range, parse_listing_start


def test_parse_listing_start_variants() -> None:
    assert parse_listing_start("2026-06-10T19:00:00-07:00") == date(2026, 6, 10)
    assert parse_listing_start("2026-06-04 10:00") == date(2026, 6, 4)


def test_listing_in_date_range() -> None:
    assert listing_in_date_range(
        "2026-06-05T18:00:00Z",
        range_start=date(2026, 6, 1),
        range_end=date(2026, 6, 30),
    )
    assert not listing_in_date_range(
        "2026-07-01T18:00:00Z",
        range_start=date(2026, 6, 1),
        range_end=date(2026, 6, 30),
    )
