"""Running calorie balance from prior logged days."""

from __future__ import annotations

from datetime import date, timedelta

CARRY_OVER_WINDOW_DAYS = 3


def compute_calorie_carry_over(
    food_by_date: list[dict],
    daily_budget: float,
    before_date: date,
    *,
    window_days: int = CARRY_OVER_WINDOW_DAYS,
) -> float:
    """Sum (daily_budget - consumed) for logged days in the sliding window before ``before_date``."""
    window_start = before_date - timedelta(days=window_days)
    carry = 0.0
    for row in food_by_date:
        local = date.fromisoformat(row["local_date"])
        if local >= before_date or local < window_start:
            continue
        consumed = float(row["calories"])
        carry += daily_budget - consumed
    return round(carry, 1)


def effective_daily_calorie_budget(
    daily_budget: float,
    carry_over_kcal: float,
) -> float:
    return round(daily_budget + carry_over_kcal, 1)
