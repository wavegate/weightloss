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
from app.models.weight_loss_plan import WeightLossPlan
from app.schemas.metabolic_profile import MetabolicProfileUpsert
from app.services.food_dates import food_query_window, summarize_food_by_local_date
from app.services.user_date import (
    effective_local_calendar_date,
    resolve_user_local_date,
    resolve_user_timezone,
)
from app.services.weight_loss_plan import (
    compute_weight_loss_plan,
    estimate_weight_loss_timeline,
    serialize_weight_loss_plan,
)
from app.services.metabolic import (
    Sex,
    ACTIVITY_MULTIPLIERS,
    ActivityLevel,
    cm_to_inches,
    compute_bmr_mifflin_st_jeor,
    compute_tdee,
    inches_to_cm,
    kg_to_lbs,
    lbs_to_kg,
)


def _load_profile_and_weight(
    db,
    user_id: str,
) -> tuple[MetabolicProfile | None, float | None]:
    profile = db.scalar(
        select(MetabolicProfile).where(MetabolicProfile.user_id == user_id)
    )
    latest = db.scalar(
        select(BodyMeasurement.body_weight_lbs)
        .where(BodyMeasurement.user_id == user_id)
        .order_by(
            BodyMeasurement.recorded_at.desc(),
            BodyMeasurement.id.desc(),
        )
        .limit(1)
    )
    weight = float(latest) if latest is not None else None
    return profile, weight


def _user_id(config: RunnableConfig) -> str:
    user_id = (config.get("configurable") or {}).get("user_id")
    if not user_id:
        raise ValueError("Missing user_id in agent configuration")
    return user_id


def _iso_week(d: date) -> tuple[int, int]:
    year, week, _ = d.isocalendar()
    return year, week


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
        "needs_weekly_measurement": needs_weekly_measurement,
        "profile": None,
        "weight_loss_plan": None,
        "daily_calorie_budget": None,
        "latest_measurement": None,
        "food_today": {
            "entry_count": int(food_today["entry_count"]),
            "calories": round(float(food_today["calories"]), 1),
        },
        "food_log_last_7_days": {
            "entry_count": week_entry_count,
            "avg_calories_per_entry": week_avg_calories,
            "total_calories": round(week_calories, 1),
        },
        "food_log_by_local_date": food_by_date,
    }

    if latest_measurement:
        payload["latest_measurement"] = {
            "recorded_at_stored": latest_measurement.recorded_at.isoformat(),
            "recorded_at_local": latest_date.isoformat() if latest_date else None,
            "body_weight_lbs": float(latest_measurement.body_weight_lbs),
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
        if plan is None:
            payload["daily_calorie_budget"] = float(profile.tdee_kcal)

    if plan:
        payload["weight_loss_plan"] = serialize_weight_loss_plan(
            plan, reference_date=today
        )
        payload["daily_calorie_budget"] = float(plan.daily_calorie_target)

    return json.dumps(payload)


@tool
def estimate_weight_loss_timeline_options(
    target_weight_lbs: float,
    current_weight_lbs: float | None = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Estimate how long it may take to reach a goal weight at safe deficit paces.

    Use when the user asks for a time estimate but has not picked a target date yet.
    Returns fastest_safe (~1000 kcal/day deficit cap), moderate (~750), and gentle (~500).
    """
    user_id = _user_id(config)
    today = resolve_user_local_date(config)

    with SessionLocal() as db:
        profile, latest_weight = _load_profile_and_weight(db, user_id)

    if profile is None or profile.tdee_kcal is None:
        return json.dumps(
            {"error": "Save a metabolic profile with TDEE before estimating a timeline."}
        )

    weight = current_weight_lbs if current_weight_lbs is not None else latest_weight
    if weight is None:
        return json.dumps(
            {"error": "Log a body weight or provide current_weight_lbs for the estimate."}
        )

    try:
        result = estimate_weight_loss_timeline(
            current_weight_lbs=weight,
            target_weight_lbs=target_weight_lbs,
            start_date=today,
            tdee_kcal=float(profile.tdee_kcal),
            sex=profile.sex,  # type: ignore[arg-type]
        )
    except ValueError as exc:
        return json.dumps({"error": str(exc)})

    return json.dumps(result)


@tool
def compute_weight_loss_plan_preview(
    target_weight_lbs: float,
    target_date: str,
    current_weight_lbs: float | None = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Preview a weight-loss plan: daily calorie target and deficit from goal weight and date.

    Requires a saved metabolic profile with TDEE. target_date is YYYY-MM-DD and must be
    in the future. Uses latest body weight unless current_weight_lbs is provided.
    """
    user_id = _user_id(config)
    today = resolve_user_local_date(config)
    goal_date = date.fromisoformat(target_date)

    with SessionLocal() as db:
        profile, latest_weight = _load_profile_and_weight(db, user_id)

    if profile is None or profile.tdee_kcal is None:
        return json.dumps(
            {"error": "Save a metabolic profile with TDEE before creating a plan."}
        )

    weight = current_weight_lbs if current_weight_lbs is not None else latest_weight
    if weight is None:
        return json.dumps(
            {"error": "Log a body weight or provide current_weight_lbs for the plan."}
        )

    try:
        result = compute_weight_loss_plan(
            current_weight_lbs=weight,
            target_weight_lbs=target_weight_lbs,
            target_date=goal_date,
            start_date=today,
            tdee_kcal=float(profile.tdee_kcal),
            sex=profile.sex,  # type: ignore[arg-type]
        )
    except ValueError as exc:
        return json.dumps({"error": str(exc)})

    return json.dumps(
        {
            "start_weight_lbs": result.start_weight_lbs,
            "target_weight_lbs": result.target_weight_lbs,
            "target_date": result.target_date.isoformat(),
            "days_until_goal": result.days_until_goal,
            "weight_to_lose_lbs": result.weight_to_lose_lbs,
            "tdee_kcal": result.tdee_kcal,
            "daily_deficit_kcal": result.daily_deficit_kcal,
            "daily_calorie_target": result.daily_calorie_target,
            "warning": result.warning,
        }
    )


@tool
def save_weight_loss_plan(
    target_weight_lbs: float,
    target_date: str,
    current_weight_lbs: float | None = None,
    notes: str | None = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Save the user's weight-loss plan after they confirm the preview."""
    user_id = _user_id(config)
    today = resolve_user_local_date(config)
    goal_date = date.fromisoformat(target_date)

    with SessionLocal() as db:
        profile, latest_weight = _load_profile_and_weight(db, user_id)

        if profile is None or profile.tdee_kcal is None:
            return json.dumps(
                {"error": "Save a metabolic profile with TDEE before creating a plan."}
            )

        weight = current_weight_lbs if current_weight_lbs is not None else latest_weight
        if weight is None:
            return json.dumps(
                {"error": "Log a body weight or provide current_weight_lbs for the plan."}
            )

        try:
            result = compute_weight_loss_plan(
                current_weight_lbs=weight,
                target_weight_lbs=target_weight_lbs,
                target_date=goal_date,
                start_date=today,
                tdee_kcal=float(profile.tdee_kcal),
                sex=profile.sex,  # type: ignore[arg-type]
            )
        except ValueError as exc:
            return json.dumps({"error": str(exc)})

        plan = db.scalar(
            select(WeightLossPlan).where(WeightLossPlan.user_id == user_id)
        )
        if plan is None:
            plan = WeightLossPlan(user_id=user_id)
            db.add(plan)

        plan.start_weight_lbs = result.start_weight_lbs
        plan.target_weight_lbs = result.target_weight_lbs
        plan.start_date = result.start_date
        plan.target_date = result.target_date
        plan.tdee_kcal = result.tdee_kcal
        plan.daily_calorie_target = result.daily_calorie_target
        plan.daily_deficit_kcal = result.daily_deficit_kcal
        plan.notes = notes
        db.commit()
        db.refresh(plan)

    return json.dumps(
        {
            "saved": True,
            "weight_loss_plan": serialize_weight_loss_plan(plan, reference_date=today),
            "daily_calorie_budget": float(plan.daily_calorie_target),
        }
    )


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
    estimate_weight_loss_timeline_options,
    compute_weight_loss_plan_preview,
    save_weight_loss_plan,
    save_metabolic_profile,
]
