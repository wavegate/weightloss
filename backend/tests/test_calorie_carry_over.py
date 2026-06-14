from datetime import date

from app.services.calorie_carry_over import (
    CARRY_OVER_WINDOW_DAYS,
    compute_calorie_carry_over,
    effective_daily_calorie_budget,
)


def test_compute_calorie_carry_over_sums_prior_days_in_window() -> None:
    food_by_date = [
        {"local_date": "2026-06-10", "calories": 2200.0},
        {"local_date": "2026-06-11", "calories": 1800.0},
        {"local_date": "2026-06-12", "calories": 1500.0},
    ]

    carry = compute_calorie_carry_over(food_by_date, 2000.0, date(2026, 6, 12))

    assert carry == 0.0


def test_compute_calorie_carry_over_excludes_days_outside_window() -> None:
    food_by_date = [
        {"local_date": "2026-06-08", "calories": 1000.0},
        {"local_date": "2026-06-09", "calories": 2200.0},
    ]

    carry = compute_calorie_carry_over(food_by_date, 2000.0, date(2026, 6, 12))

    assert carry == -200.0
    assert CARRY_OVER_WINDOW_DAYS == 3


def test_effective_daily_calorie_budget() -> None:
    assert effective_daily_calorie_budget(2000.0, 200.0) == 2200.0
