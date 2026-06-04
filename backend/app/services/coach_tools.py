import json
from datetime import date, timedelta
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from sqlalchemy import select

from app.database import SessionLocal
from app.models.body_measurement import BodyMeasurement
from app.models.food_entry import FoodEntry
from app.models.metabolic_profile import MetabolicProfile
from app.models.weight_loss_plan import WeightLossPlan
from app.services.weight_loss_plan import serialize_weight_loss_plan
from app.services.food_dates import food_query_window, summarize_food_by_local_date
from app.services.user_date import (
    effective_local_calendar_date,
    resolve_user_local_date,
    resolve_user_timezone,
)


def _user_id(config: RunnableConfig) -> str:
    user_id = (config.get("configurable") or {}).get("user_id")
    if not user_id:
        raise ValueError("Missing user_id in agent configuration")
    return user_id


def _iso_week(d: date) -> tuple[int, int]:
    year, week, _ = d.isocalendar()
    return year, week


@tool
def get_coach_context(
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Load the user's weight-loss context: profile, measurements, food log, and reminders."""
    user_id = _user_id(config)
    today = resolve_user_local_date(config)
    user_timezone = resolve_user_timezone(config)
    fetch_from = food_query_window(today)

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

    week_entries = [
        row
        for row in food_by_date
        if date.fromisoformat(row["local_date"]) >= today - timedelta(days=7)
    ]
    week_entry_count = sum(int(row["entry_count"]) for row in week_entries)
    week_calories = sum(float(row["calories"]) for row in week_entries)
    week_avg_calories = (
        round(week_calories / week_entry_count, 1) if week_entry_count else 0.0
    )

    latest_date = None
    if latest_measurement:
        latest_date = effective_local_calendar_date(
            latest_measurement.recorded_at,
            user_local_today=today,
            user_timezone=user_timezone,
        )

    needs_weekly_measurement = (
        latest_date is None or _iso_week(latest_date) != _iso_week(today)
    )

    payload: dict = {
        "user_timezone": user_timezone,
        "today": today.isoformat(),
        "today_note": (
            "Food and measurements are grouped by calendar date in user_timezone. "
            "DB recorded_at values may be reinterpreted from legacy UTC calendar dates."
        ),
        "needs_weekly_measurement": needs_weekly_measurement,
        "latest_measurement": None,
        "metabolic_profile": None,
        "weight_loss_plan": None,
        "daily_calorie_budget": None,
        "food_today": {
            "entry_count": int(food_today["entry_count"]),
            "calories": round(float(food_today["calories"]), 1),
            "protein_g": round(float(food_today["protein_g"]), 1),
            "carbs_g": round(float(food_today["carbs_g"]), 1),
            "fat_g": round(float(food_today["fat_g"]), 1),
            "fiber_g": round(float(food_today["fiber_g"]), 1),
        },
        "food_log_last_7_days": {
            "entry_count": week_entry_count,
            "avg_calories_per_entry": week_avg_calories,
            "total_calories": round(week_calories, 1),
        },
        "food_log_by_local_date": food_by_date,
        "app_pages": {
            "measurements": "/measurements — log body weight",
            "food": "/food — food log and daily calorie summary",
            "metabolism": "/metabolism — saved BMR/TDEE profile",
        },
        "handoffs": {
            "metabolism_coach": (
                "Call transfer_to_metabolism_coach for BMR/TDEE, profile, "
                "timelines, plan preview, and save_weight_loss_plan."
            ),
            "dietician_coach": (
                "Call transfer_to_dietician_coach for food log updates, diet coaching, "
                "meal ideas, hunger check-ins, and nutrition summaries."
            ),
        },
        "active_agent": None,
    }

    if latest_measurement:
        payload["latest_measurement"] = {
            "recorded_at_stored": latest_measurement.recorded_at.isoformat(),
            "recorded_at_local": latest_date.isoformat() if latest_date else None,
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
        if plan is None and profile.tdee_kcal is not None:
            payload["daily_calorie_budget"] = float(profile.tdee_kcal)

    if plan:
        payload["weight_loss_plan"] = serialize_weight_loss_plan(
            plan, reference_date=today
        )
        payload["daily_calorie_budget"] = float(plan.daily_calorie_target)

    return json.dumps(payload)


COACH_TOOLS = [get_coach_context]
