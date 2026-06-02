"""Deterministic metabolic calculations (Mifflin–St Jeor + PAL)."""

from typing import Literal

Sex = Literal["male", "female"]
ActivityLevel = Literal[
    "sedentary",
    "light",
    "moderate",
    "active",
    "very_active",
]

ACTIVITY_MULTIPLIERS: dict[ActivityLevel, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def lbs_to_kg(lbs: float) -> float:
    return lbs / 2.2046226218


def kg_to_lbs(kg: float) -> float:
    return kg * 2.2046226218


def inches_to_cm(inches: float) -> float:
    return inches * 2.54


def cm_to_inches(cm: float) -> float:
    return cm / 2.54


def compute_bmr_mifflin_st_jeor(
    *,
    sex: Sex,
    age_years: int,
    height_cm: float,
    weight_kg: float,
) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age_years
    if sex == "male":
        return base + 5
    return base - 161


def compute_tdee(*, bmr_kcal: float, activity_level: ActivityLevel) -> float:
    multiplier = ACTIVITY_MULTIPLIERS[activity_level]
    return bmr_kcal * multiplier
