import json
from datetime import date, timedelta
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.body_measurement import BodyMeasurement
from app.models.food_entry import FoodEntry
from app.models.metabolic_profile import MetabolicProfile


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
    today = date.today()
    week_ago = today - timedelta(days=7)

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
        today_food = db.execute(
            select(
                func.count(FoodEntry.id),
                func.coalesce(func.sum(FoodEntry.calories), 0),
            ).where(
                FoodEntry.user_id == user_id,
                FoodEntry.recorded_at == today,
            )
        ).one()
        week_food_stats = db.execute(
            select(
                func.count(FoodEntry.id),
                func.coalesce(func.avg(FoodEntry.calories), 0),
            ).where(
                FoodEntry.user_id == user_id,
                FoodEntry.recorded_at >= week_ago,
            )
        ).one()

    today_count, today_calories = today_food
    week_entry_count, week_avg_calories = week_food_stats

    latest_date = latest_measurement.recorded_at if latest_measurement else None
    needs_weekly_measurement = (
        latest_date is None or _iso_week(latest_date) != _iso_week(today)
    )

    payload: dict = {
        "today": today.isoformat(),
        "needs_weekly_measurement": needs_weekly_measurement,
        "latest_measurement": None,
        "metabolic_profile": None,
        "food_today": {
            "entry_count": int(today_count),
            "calories": round(float(today_calories), 1),
        },
        "food_log_last_7_days": {
            "entry_count": int(week_entry_count),
            "avg_calories_per_entry": round(float(week_avg_calories), 1),
        },
        "app_pages": {
            "measurements": "/measurements — log body weight",
            "food": "/food — food log and daily calorie summary",
            "metabolism": "/metabolism — saved BMR/TDEE profile",
        },
        "subagents": {
            "metabolism_coach": "BMR/TDEE estimation and saving metabolic profile",
        },
    }

    if latest_measurement:
        payload["latest_measurement"] = {
            "recorded_at": latest_measurement.recorded_at.isoformat(),
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

    return json.dumps(payload)


COACH_TOOLS = [get_coach_context]
