import json
from datetime import date, timedelta
from typing import Annotated, Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from sqlalchemy import select

from app.database import SessionLocal
from app.models.body_measurement import BodyMeasurement
from app.models.food_entry import FoodEntry
from app.models.metabolic_profile import MetabolicProfile
from app.schemas.metabolic_profile import MetabolicProfileUpsert
from app.services.food_dates import food_query_window, summarize_food_by_local_date
from app.services.user_date import (
    effective_local_calendar_date,
    resolve_user_local_date,
    resolve_user_timezone,
)
from app.services.metabolic import (
    ACTIVITY_MULTIPLIERS,
    ActivityLevel,
    Sex,
    cm_to_inches,
    compute_bmr_mifflin_st_jeor,
    compute_tdee,
    inches_to_cm,
    kg_to_lbs,
    lbs_to_kg,
)


def _user_id(config: RunnableConfig) -> str:
    user_id = (config.get("configurable") or {}).get("user_id")
    if not user_id:
        raise ValueError("Missing user_id in agent configuration")
    return user_id


@tool
def compute_bmr(
    sex: Literal["male", "female"],
    age_years: int,
    height_cm: float,
    weight_kg: float,
) -> str:
    """Compute basal metabolic rate (BMR) in kcal/day using Mifflin–St Jeor."""
    bmr = compute_bmr_mifflin_st_jeor(
        sex=sex,
        age_years=age_years,
        height_cm=height_cm,
        weight_kg=weight_kg,
    )
    return json.dumps({"bmr_kcal": round(bmr, 1)})


@tool
def compute_tdee_from_bmr(
    bmr_kcal: float,
    activity_level: Literal[
        "sedentary", "light", "moderate", "active", "very_active"
    ],
) -> str:
    """Compute total daily energy expenditure (TDEE) from BMR and activity level."""
    level: ActivityLevel = activity_level
    tdee = compute_tdee(bmr_kcal=bmr_kcal, activity_level=level)
    return json.dumps(
        {
            "tdee_kcal": round(tdee, 1),
            "activity_multiplier": ACTIVITY_MULTIPLIERS[level],
        }
    )


@tool
def convert_units(
    value: float,
    from_unit: Literal["lbs", "kg", "inches", "cm"],
    to_unit: Literal["lbs", "kg", "inches", "cm"],
) -> str:
    """Convert body measurement units (lbs/kg, inches/cm)."""
    if from_unit == to_unit:
        converted = value
    elif from_unit == "lbs" and to_unit == "kg":
        converted = lbs_to_kg(value)
    elif from_unit == "kg" and to_unit == "lbs":
        converted = kg_to_lbs(value)
    elif from_unit == "inches" and to_unit == "cm":
        converted = inches_to_cm(value)
    elif from_unit == "cm" and to_unit == "inches":
        converted = cm_to_inches(value)
    else:
        raise ValueError(f"Cannot convert {from_unit} to {to_unit}")

    return json.dumps({"value": round(converted, 2), "unit": to_unit})


@tool
def get_user_context(
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Load saved metabolic profile, latest weight, and recent food log averages."""
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
                select(FoodEntry).where(
                    FoodEntry.user_id == user_id,
                    FoodEntry.recorded_at >= fetch_from,
                )
            ).all()
        )

    _, food_today = summarize_food_by_local_date(
        food_entries,
        user_local_today=today,
        user_timezone=user_timezone,
    )
    week_entries = [
        e
        for e in food_entries
        if effective_local_calendar_date(
            e.recorded_at,
            user_local_today=today,
            user_timezone=user_timezone,
        )
        >= today - timedelta(days=7)
    ]
    week_count = len(week_entries)
    week_avg = (
        sum(float(e.calories) for e in week_entries) / week_count
        if week_count
        else 0.0
    )

    payload: dict = {
        "profile": None,
        "user_timezone": user_timezone,
        "latest_weight_lbs": (
            float(latest_measurement.body_weight_lbs) if latest_measurement else None
        ),
        "food_today": {
            "entry_count": int(food_today["entry_count"]),
            "calories": round(float(food_today["calories"]), 1),
        },
        "food_log_last_7_days": {
            "entry_count": week_count,
            "avg_calories_per_entry": round(week_avg, 1),
        },
    }

    if profile:
        payload["profile"] = {
            "sex": profile.sex,
            "age_years": profile.age_years,
            "height_cm": float(profile.height_cm),
            "activity_level": profile.activity_level,
            "bmr_kcal": float(profile.bmr_kcal) if profile.bmr_kcal else None,
            "tdee_kcal": float(profile.tdee_kcal) if profile.tdee_kcal else None,
            "notes": profile.notes,
        }

    return json.dumps(payload)


@tool
def save_metabolic_profile(
    sex: Literal["male", "female"],
    age_years: int,
    height_cm: float,
    activity_level: Literal[
        "sedentary", "light", "moderate", "active", "very_active"
    ],
    bmr_kcal: float | None = None,
    tdee_kcal: float | None = None,
    notes: str | None = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Save or update the user's metabolic profile after they confirm the values."""
    user_id = _user_id(config)
    payload = MetabolicProfileUpsert(
        sex=sex,
        age_years=age_years,
        height_cm=height_cm,
        activity_level=activity_level,
        bmr_kcal=bmr_kcal,
        tdee_kcal=tdee_kcal,
        notes=notes,
    )

    with SessionLocal() as db:
        profile = db.scalar(
            select(MetabolicProfile).where(MetabolicProfile.user_id == user_id)
        )
        if profile is None:
            profile = MetabolicProfile(user_id=user_id)
            db.add(profile)

        profile.sex = payload.sex
        profile.age_years = payload.age_years
        profile.height_cm = payload.height_cm
        profile.activity_level = payload.activity_level
        profile.bmr_kcal = payload.bmr_kcal
        profile.tdee_kcal = payload.tdee_kcal
        profile.notes = payload.notes
        db.commit()
        db.refresh(profile)

    return json.dumps(
        {
            "saved": True,
            "bmr_kcal": float(profile.bmr_kcal) if profile.bmr_kcal else None,
            "tdee_kcal": float(profile.tdee_kcal) if profile.tdee_kcal else None,
        }
    )


METABOLISM_TOOLS = [
    compute_bmr,
    compute_tdee_from_bmr,
    convert_units,
    get_user_context,
    save_metabolic_profile,
]
