"""Deterministic weight-loss plan math (calorie deficit from goal weight + date)."""

from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil

from app.services.metabolic import Sex

KCAL_PER_LB = 3500
MAX_DAILY_DEFICIT_KCAL = 1000
MIN_DAILY_CALORIES: dict[Sex, float] = {
    "female": 1200,
    "male": 1500,
}


@dataclass(frozen=True)
class WeightLossPlanComputation:
    start_weight_lbs: float
    target_weight_lbs: float
    start_date: date
    target_date: date
    days_until_goal: int
    weight_to_lose_lbs: float
    tdee_kcal: float
    total_deficit_kcal: float
    daily_deficit_kcal: float
    daily_calorie_target: float
    minimum_days_at_max_deficit: int | None
    warning: str | None


def compute_weight_loss_plan(
    *,
    current_weight_lbs: float,
    target_weight_lbs: float,
    target_date: date,
    start_date: date,
    tdee_kcal: float,
    sex: Sex,
) -> WeightLossPlanComputation:
    if target_weight_lbs >= current_weight_lbs:
        raise ValueError("Target weight must be lower than current weight.")

    days = (target_date - start_date).days
    if days < 1:
        raise ValueError("Target date must be after today.")

    weight_to_lose = current_weight_lbs - target_weight_lbs
    total_deficit = weight_to_lose * KCAL_PER_LB
    raw_daily_deficit = total_deficit / days

    warning: str | None = None
    minimum_days: int | None = None
    if raw_daily_deficit > MAX_DAILY_DEFICIT_KCAL:
        minimum_days = int(ceil(total_deficit / MAX_DAILY_DEFICIT_KCAL))
        daily_deficit = MAX_DAILY_DEFICIT_KCAL
        warning = (
            f"Reaching this goal by {target_date.isoformat()} would require about "
            f"{round(raw_daily_deficit)} kcal/day deficit. The plan uses a safer "
            f"{MAX_DAILY_DEFICIT_KCAL} kcal/day cap (~{minimum_days} days at that rate)."
        )
    else:
        daily_deficit = raw_daily_deficit

    daily_target = tdee_kcal - daily_deficit
    floor = MIN_DAILY_CALORIES[sex]
    if daily_target < floor:
        daily_target = floor
        daily_deficit = tdee_kcal - daily_target
        warning = (
            (warning + " ") if warning else ""
        ) + (
            f"Daily target was raised to {floor} kcal minimum; actual deficit is "
            f"{round(daily_deficit)} kcal/day."
        )

    return WeightLossPlanComputation(
        start_weight_lbs=round(current_weight_lbs, 1),
        target_weight_lbs=round(target_weight_lbs, 1),
        start_date=start_date,
        target_date=target_date,
        days_until_goal=days,
        weight_to_lose_lbs=round(weight_to_lose, 1),
        tdee_kcal=round(tdee_kcal, 1),
        total_deficit_kcal=round(total_deficit, 1),
        daily_deficit_kcal=round(daily_deficit, 1),
        daily_calorie_target=round(daily_target, 1),
        minimum_days_at_max_deficit=minimum_days,
        warning=warning,
    )


@dataclass(frozen=True)
class WeightLossTimelineOption:
    label: str
    days: int
    target_date: date
    daily_deficit_kcal: float
    daily_calorie_target: float


def estimate_weight_loss_timeline(
    *,
    current_weight_lbs: float,
    target_weight_lbs: float,
    start_date: date,
    tdee_kcal: float,
    sex: Sex,
) -> dict:
    """Suggest goal dates from fastest safe, moderate, and gentle deficit paces."""
    if target_weight_lbs >= current_weight_lbs:
        raise ValueError("Target weight must be lower than current weight.")

    weight_to_lose = current_weight_lbs - target_weight_lbs
    total_deficit = weight_to_lose * KCAL_PER_LB
    floor = MIN_DAILY_CALORIES[sex]
    min_days_at_cap = int(ceil(total_deficit / MAX_DAILY_DEFICIT_KCAL))

    paces: list[tuple[str, float]] = [
        ("fastest_safe", float(MAX_DAILY_DEFICIT_KCAL)),
        ("moderate", 750.0),
        ("gentle", 500.0),
    ]
    options: list[WeightLossTimelineOption] = []
    for label, target_deficit in paces:
        days = max(1, int(ceil(total_deficit / target_deficit)))
        daily_target = tdee_kcal - target_deficit
        if daily_target < floor:
            daily_target = floor
        actual_deficit = tdee_kcal - daily_target
        options.append(
            WeightLossTimelineOption(
                label=label,
                days=days,
                target_date=start_date + timedelta(days=days),
                daily_deficit_kcal=round(actual_deficit, 1),
                daily_calorie_target=round(daily_target, 1),
            )
        )

    return {
        "start_weight_lbs": round(current_weight_lbs, 1),
        "target_weight_lbs": round(target_weight_lbs, 1),
        "weight_to_lose_lbs": round(weight_to_lose, 1),
        "total_deficit_kcal": round(total_deficit, 1),
        "minimum_days_at_max_deficit": min_days_at_cap,
        "options": [
            {
                "label": opt.label,
                "days": opt.days,
                "target_date": opt.target_date.isoformat(),
                "daily_deficit_kcal": opt.daily_deficit_kcal,
                "daily_calorie_target": opt.daily_calorie_target,
            }
            for opt in options
        ],
    }


def serialize_weight_loss_plan(
    plan,
    *,
    reference_date: date | None = None,
) -> dict:
    """JSON-friendly plan summary for tools and API responses."""
    days_span = (plan.target_date - plan.start_date).days
    days_until = (
        max(0, (plan.target_date - reference_date).days)
        if reference_date is not None
        else days_span
    )
    return {
        "start_weight_lbs": float(plan.start_weight_lbs),
        "target_weight_lbs": float(plan.target_weight_lbs),
        "start_date": plan.start_date.isoformat(),
        "target_date": plan.target_date.isoformat(),
        "tdee_kcal": float(plan.tdee_kcal),
        "daily_calorie_target": float(plan.daily_calorie_target),
        "daily_deficit_kcal": float(plan.daily_deficit_kcal),
        "weight_to_lose_lbs": round(
            float(plan.start_weight_lbs) - float(plan.target_weight_lbs), 1
        ),
        "days_until_goal": days_until,
        "notes": plan.notes,
    }


def current_weight_lbs_from_profile(
    *,
    latest_measurement_lbs: float | None,
    height_cm: float,
    sex: Sex,
    age_years: int,
) -> float | None:
    if latest_measurement_lbs is not None:
        return latest_measurement_lbs
    return None
