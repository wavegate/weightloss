from datetime import date
from unittest.mock import MagicMock

from app.services.food_dates import summarize_food_by_local_date


def test_summarize_food_by_local_date_includes_fiber() -> None:
    entry = MagicMock()
    entry.recorded_at = date(2026, 6, 2)
    entry.calories = 100.0
    entry.protein_g = 10.0
    entry.carbs_g = 12.0
    entry.fat_g = 3.0
    entry.fiber_g = 4.5

    food_by_date, food_today = summarize_food_by_local_date(
        [entry],
        user_local_today=date(2026, 6, 2),
        user_timezone="America/New_York",
    )

    assert food_today["fiber_g"] == 4.5
    assert food_by_date[0]["fiber_g"] == 4.5
