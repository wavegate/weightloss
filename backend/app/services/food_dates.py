from collections import defaultdict
from datetime import date, timedelta

from app.models.food_entry import FoodEntry
from app.services.user_date import effective_local_calendar_date


def summarize_food_by_local_date(
    entries: list[FoodEntry],
    *,
    user_local_today: date,
    user_timezone: str,
) -> tuple[dict[str, dict[str, float | int]], dict[str, float | int]]:
    """Group food entries by effective local calendar date in the user's timezone."""
    by_local: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"entry_count": 0, "calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    )

    for entry in entries:
        local_day = effective_local_calendar_date(
            entry.recorded_at,
            user_local_today=user_local_today,
            user_timezone=user_timezone,
        )
        key = local_day.isoformat()
        bucket = by_local[key]
        bucket["entry_count"] = int(bucket["entry_count"]) + 1
        bucket["calories"] = float(bucket["calories"]) + float(entry.calories)
        bucket["protein_g"] = float(bucket["protein_g"]) + float(entry.protein_g)
        bucket["carbs_g"] = float(bucket["carbs_g"]) + float(entry.carbs_g)
        bucket["fat_g"] = float(bucket["fat_g"]) + float(entry.fat_g)

    today_key = user_local_today.isoformat()
    food_today = by_local.get(
        today_key,
        {"entry_count": 0, "calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0},
    )

    food_by_date = [
        {
            "local_date": local_date,
            "entry_count": int(stats["entry_count"]),
            "calories": round(float(stats["calories"]), 1),
            "protein_g": round(float(stats["protein_g"]), 1),
            "carbs_g": round(float(stats["carbs_g"]), 1),
            "fat_g": round(float(stats["fat_g"]), 1),
        }
        for local_date, stats in sorted(by_local.items(), reverse=True)
    ]

    return food_by_date, food_today


def food_query_window(user_local_today: date, *, days: int = 14) -> date:
    """Widen DB fetch so UTC-stamped rows still appear after local conversion."""
    return user_local_today - timedelta(days=days)
