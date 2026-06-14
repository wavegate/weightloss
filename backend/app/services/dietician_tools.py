"""Tools for the dietician coach — food log CRUD, summaries, and diet guidance."""

import json
from datetime import date, timedelta
from typing import Annotated, Literal

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from sqlalchemy import select

from app.database import SessionLocal
from app.models.body_measurement import BodyMeasurement
from app.models.food_entry import FoodEntry
from app.models.metabolic_profile import MetabolicProfile
from app.models.weight_loss_plan import WeightLossPlan
from app.services.calorie_carry_over import (
    compute_calorie_carry_over,
    effective_daily_calorie_budget,
)
from app.services.food_dates import food_query_window, summarize_food_by_local_date
from app.services.food_matching import find_reusable_food_entry, nutrition_estimate_from_entry
from app.services.nutrition_agent import NutritionEstimate, estimate_nutrition
from app.services.user_date import (
    effective_local_calendar_date,
    resolve_user_local_date,
    resolve_user_timezone,
)
from app.services.weight_loss_plan import serialize_weight_loss_plan

MACRO_SPLIT = {"protein": 0.3, "carbs": 0.4, "fat": 0.3}


def _user_id(config: RunnableConfig) -> str:
    user_id = (config.get("configurable") or {}).get("user_id")
    if not user_id:
        raise ValueError("Missing user_id in agent configuration")
    return user_id


def _macro_targets_from_budget(budget_kcal: float) -> dict[str, float]:
    return {
        "calories": budget_kcal,
        "protein_g": round((budget_kcal * MACRO_SPLIT["protein"]) / 4),
        "carbs_g": round((budget_kcal * MACRO_SPLIT["carbs"]) / 4),
        "fat_g": round((budget_kcal * MACRO_SPLIT["fat"]) / 9),
    }


def _serialize_food_entry(entry: FoodEntry, *, local_date: date | None = None) -> dict:
    payload = {
        "id": entry.id,
        "recorded_at_stored": entry.recorded_at.isoformat(),
        "name": entry.name,
        "description": entry.description,
        "calories": float(entry.calories),
        "protein_g": float(entry.protein_g),
        "carbs_g": float(entry.carbs_g),
        "fat_g": float(entry.fat_g),
        "fiber_g": float(entry.fiber_g),
        "estimation_notes": entry.estimation_notes,
    }
    if local_date is not None:
        payload["local_date"] = local_date.isoformat()
    return payload


def _load_food_entries(
    user_id: str,
    *,
    fetch_from: date,
) -> list[FoodEntry]:
    with SessionLocal() as db:
        return list(
            db.scalars(
                select(FoodEntry)
                .where(
                    FoodEntry.user_id == user_id,
                    FoodEntry.recorded_at >= fetch_from,
                )
                .order_by(FoodEntry.recorded_at.desc(), FoodEntry.id.desc())
            ).all()
        )


def _resolve_budget(
    profile: MetabolicProfile | None,
    plan: WeightLossPlan | None,
) -> float | None:
    if plan is not None:
        return float(plan.daily_calorie_target)
    if profile is not None and profile.tdee_kcal is not None:
        return float(profile.tdee_kcal)
    return None


def _resolve_food_nutrition(
    db,
    user_id: str,
    name: str,
    description: str,
) -> NutritionEstimate:
    match = find_reusable_food_entry(db, user_id, name, description)
    if match is not None:
        return nutrition_estimate_from_entry(match)
    return estimate_nutrition(name.strip(), description.strip())


@tool
def get_dietician_context(
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Load food log, calorie budget, weight-loss plan, and macro targets for diet coaching."""
    user_id = _user_id(config)
    today = resolve_user_local_date(config)
    user_timezone = resolve_user_timezone(config)
    fetch_from = food_query_window(today, days=35)

    with SessionLocal() as db:
        profile = db.scalar(
            select(MetabolicProfile).where(MetabolicProfile.user_id == user_id)
        )
        latest_measurement = db.scalar(
            select(BodyMeasurement)
            .where(BodyMeasurement.user_id == user_id)
            .order_by(
                BodyMeasurement.recorded_at.desc(),
                BodyMeasurement.id.desc(),
            )
            .limit(1)
        )
        food_entries = list(
            db.scalars(
                select(FoodEntry)
                .where(
                    FoodEntry.user_id == user_id,
                    FoodEntry.recorded_at >= fetch_from,
                )
                .order_by(FoodEntry.recorded_at.desc(), FoodEntry.id.desc())
            ).all()
        )
        plan = db.scalar(
            select(WeightLossPlan).where(WeightLossPlan.user_id == user_id)
        )

    food_by_date, food_today = summarize_food_by_local_date(
        food_entries,
        user_local_today=today,
        user_timezone=user_timezone,
    )

    recent_entries = [
        _serialize_food_entry(
            entry,
            local_date=effective_local_calendar_date(
                entry.recorded_at,
                user_local_today=today,
                user_timezone=user_timezone,
            ),
        )
        for entry in food_entries[:20]
    ]

    budget = _resolve_budget(profile, plan)
    macro_targets = _macro_targets_from_budget(budget) if budget else None
    carry_over = (
        compute_calorie_carry_over(food_by_date, budget, today) if budget else None
    )
    effective_budget = (
        effective_daily_calorie_budget(budget, carry_over)
        if budget is not None and carry_over is not None
        else budget
    )

    payload: dict = {
        "user_timezone": user_timezone,
        "today": today.isoformat(),
        "daily_calorie_budget": budget,
        "calorie_carry_over_kcal": carry_over,
        "effective_daily_calorie_budget": effective_budget,
        "macro_targets_30_40_30": macro_targets,
        "food_today": {
            "entry_count": int(food_today["entry_count"]),
            "calories": round(float(food_today["calories"]), 1),
            "protein_g": round(float(food_today["protein_g"]), 1),
            "carbs_g": round(float(food_today["carbs_g"]), 1),
            "fat_g": round(float(food_today["fat_g"]), 1),
            "fiber_g": round(float(food_today["fiber_g"]), 1),
            "remaining_calories": (
                round(effective_budget - float(food_today["calories"]), 1)
                if effective_budget
                else None
            ),
        },
        "food_log_by_local_date": food_by_date,
        "recent_food_entries": recent_entries,
        "metabolic_profile": None,
        "weight_loss_plan": None,
        "latest_measurement": None,
        "handoffs": {
            "metabolism_coach": (
                "Call transfer_to_metabolism_coach for BMR/TDEE or weight-loss plan changes."
            ),
            "weight_loss_coach": (
                "Call transfer_to_weight_loss_coach for body measurements or general app help."
            ),
        },
    }

    if latest_measurement:
        local_date = effective_local_calendar_date(
            latest_measurement.recorded_at,
            user_local_today=today,
            user_timezone=user_timezone,
        )
        payload["latest_measurement"] = {
            "recorded_at_local": local_date.isoformat(),
            "body_weight_lbs": float(latest_measurement.body_weight_lbs),
        }

    if profile:
        payload["metabolic_profile"] = {
            "sex": profile.sex,
            "age_years": profile.age_years,
            "height_cm": float(profile.height_cm),
            "activity_level": profile.activity_level,
            "bmr_kcal": float(profile.bmr_kcal) if profile.bmr_kcal else None,
            "tdee_kcal": float(profile.tdee_kcal) if profile.tdee_kcal else None,
        }

    if plan:
        payload["weight_loss_plan"] = serialize_weight_loss_plan(
            plan, reference_date=today
        )

    return json.dumps(payload)


@tool
def summarize_food_log(
    period: Literal["today", "week", "month"],
    *,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Summarize the user's food log for today, the past 7 days, or the past 30 days."""
    user_id = _user_id(config)
    today = resolve_user_local_date(config)
    user_timezone = resolve_user_timezone(config)

    if period == "today":
        days_back = 0
        fetch_days = 14
    elif period == "week":
        days_back = 7
        fetch_days = 21
    else:
        days_back = 30
        fetch_days = 45

    fetch_from = food_query_window(today, days=fetch_days)
    food_entries = _load_food_entries(user_id, fetch_from=fetch_from)
    food_by_date, food_today = summarize_food_by_local_date(
        food_entries,
        user_local_today=today,
        user_timezone=user_timezone,
    )

    cutoff = today - timedelta(days=days_back)
    period_rows = [
        row
        for row in food_by_date
        if date.fromisoformat(row["local_date"]) >= cutoff
    ]

    total_calories = sum(float(row["calories"]) for row in period_rows)
    total_protein = sum(float(row["protein_g"]) for row in period_rows)
    total_carbs = sum(float(row["carbs_g"]) for row in period_rows)
    total_fat = sum(float(row["fat_g"]) for row in period_rows)
    total_fiber = sum(float(row["fiber_g"]) for row in period_rows)
    total_entries = sum(int(row["entry_count"]) for row in period_rows)
    days_with_food = len([row for row in period_rows if int(row["entry_count"]) > 0])

    with SessionLocal() as db:
        profile = db.scalar(
            select(MetabolicProfile).where(MetabolicProfile.user_id == user_id)
        )
        plan = db.scalar(
            select(WeightLossPlan).where(WeightLossPlan.user_id == user_id)
        )

    budget = _resolve_budget(profile, plan)
    avg_daily_calories = (
        round(total_calories / days_with_food, 1) if days_with_food else 0.0
    )

    result = {
        "period": period,
        "start_date": cutoff.isoformat(),
        "end_date": today.isoformat(),
        "days_with_entries": days_with_food,
        "total_entries": total_entries,
        "totals": {
            "calories": round(total_calories, 1),
            "protein_g": round(total_protein, 1),
            "carbs_g": round(total_carbs, 1),
            "fat_g": round(total_fat, 1),
            "fiber_g": round(total_fiber, 1),
        },
        "avg_calories_on_logged_days": avg_daily_calories,
        "daily_calorie_budget": budget,
        "vs_budget_avg": (
            round(avg_daily_calories - budget, 1)
            if budget and days_with_food
            else None
        ),
        "daily_breakdown": period_rows,
    }

    if period == "today":
        result["today_detail"] = food_today

    return json.dumps(result)


@tool
def list_food_entries(
    start_date: str | None = None,
    end_date: str | None = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """List individual food log entries with IDs for editing or removal.

    Dates are YYYY-MM-DD in the user's local calendar. Defaults to the past 7 days.
    """
    user_id = _user_id(config)
    today = resolve_user_local_date(config)
    user_timezone = resolve_user_timezone(config)

    end = date.fromisoformat(end_date) if end_date else today
    start = date.fromisoformat(start_date) if start_date else today - timedelta(days=7)

    fetch_from = food_query_window(min(start, today), days=14)
    food_entries = _load_food_entries(user_id, fetch_from=fetch_from)

    entries = []
    for entry in food_entries:
        local_day = effective_local_calendar_date(
            entry.recorded_at,
            user_local_today=today,
            user_timezone=user_timezone,
        )
        if start <= local_day <= end:
            entries.append(_serialize_food_entry(entry, local_date=local_day))

    return json.dumps({"entries": entries, "count": len(entries)})


@tool
def add_food_entry(
    name: str,
    description: str,
    recorded_at: str | None = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Add a food entry to the log. Estimates nutrition via the nutrition agent."""
    user_id = _user_id(config)
    today = resolve_user_local_date(config)
    entry_date = date.fromisoformat(recorded_at) if recorded_at else today

    with SessionLocal() as db:
        try:
            estimate = _resolve_food_nutrition(db, user_id, name, description)
        except Exception as exc:
            return json.dumps({"error": f"Failed to estimate nutrition: {exc}"})

        entry_name = name.strip() or estimate.name
        entry_description = description.strip() or estimate.description

        entry = FoodEntry(
            user_id=user_id,
            recorded_at=entry_date,
            name=entry_name,
            description=entry_description,
            calories=estimate.calories,
            protein_g=estimate.protein_g,
            carbs_g=estimate.carbs_g,
            fat_g=estimate.fat_g,
            fiber_g=estimate.fiber_g,
            estimation_notes=estimate.notes,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)

        return json.dumps(
            {
                "saved": True,
                "entry": _serialize_food_entry(entry),
            }
        )


@tool
def update_food_entry(
    entry_id: int,
    name: str | None = None,
    description: str | None = None,
    recorded_at: str | None = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Update a food log entry. Re-estimates nutrition if name or description changes."""
    user_id = _user_id(config)

    with SessionLocal() as db:
        entry = db.get(FoodEntry, entry_id)
        if entry is None or entry.user_id != user_id:
            return json.dumps({"error": "Food entry not found"})

        new_name = name.strip() if name else entry.name
        new_description = description.strip() if description else entry.description

        if recorded_at:
            entry.recorded_at = date.fromisoformat(recorded_at)

        if name is not None or description is not None:
            try:
                estimate = estimate_nutrition(new_name, new_description)
            except Exception as exc:
                return json.dumps({"error": f"Failed to re-estimate nutrition: {exc}"})

            entry.name = new_name
            entry.description = new_description
            entry.calories = estimate.calories
            entry.protein_g = estimate.protein_g
            entry.carbs_g = estimate.carbs_g
            entry.fat_g = estimate.fat_g
            entry.fiber_g = estimate.fiber_g
            entry.estimation_notes = estimate.notes
        else:
            entry.name = new_name
            entry.description = new_description

        db.commit()
        db.refresh(entry)

    return json.dumps({"saved": True, "entry": _serialize_food_entry(entry)})


@tool
def remove_food_entry(
    entry_id: int,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Remove a food entry from the log by ID."""
    user_id = _user_id(config)

    with SessionLocal() as db:
        entry = db.get(FoodEntry, entry_id)
        if entry is None or entry.user_id != user_id:
            return json.dumps({"error": "Food entry not found"})

        removed = _serialize_food_entry(entry)
        db.delete(entry)
        db.commit()

    return json.dumps({"removed": True, "entry": removed})


_ddg_search = DuckDuckGoSearchRun()


@tool
def search_nutrition_info(query: str) -> str:
    """Search the web for recipes, meal ideas, nutrition facts, or dietary guidance."""
    return _ddg_search.invoke(query)


DIETICIAN_TOOLS = [
    get_dietician_context,
    summarize_food_log,
    list_food_entries,
    add_food_entry,
    update_food_entry,
    remove_food_entry,
    search_nutrition_info,
]
