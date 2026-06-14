"""Match new food logs against the user's prior entries to reuse nutrition estimates."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.food_entry import FoodEntry
from app.services.nutrition_agent import NutritionEstimate

_FUZZY_MATCH_THRESHOLD = 0.88


def normalize_food_text(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())


def _combined_food_text(name: str, description: str) -> str:
    return normalize_food_text(f"{name} {description}")


def find_reusable_food_entry(
    db: Session,
    user_id: str,
    name: str,
    description: str,
    *,
    limit: int = 500,
) -> FoodEntry | None:
    """Return the most recent prior entry with matching name/description, if any."""
    trimmed_name = name.strip()
    trimmed_description = description.strip()
    if not trimmed_name:
        return None

    entries = list(
        db.scalars(
            select(FoodEntry)
            .where(FoodEntry.user_id == user_id)
            .order_by(FoodEntry.recorded_at.desc(), FoodEntry.id.desc())
            .limit(limit)
        ).all()
    )

    target_name = normalize_food_text(trimmed_name)
    target_description = normalize_food_text(trimmed_description)
    target_combined = _combined_food_text(trimmed_name, trimmed_description)

    exact_name: FoodEntry | None = None
    best_fuzzy: tuple[float, FoodEntry] | None = None

    for entry in entries:
        entry_name = normalize_food_text(entry.name)
        entry_description = normalize_food_text(entry.description)

        if entry_name == target_name and entry_description == target_description:
            return entry

        if exact_name is None and entry_name == target_name:
            if not target_description or not entry_description:
                exact_name = entry
            elif (
                target_description in entry_description
                or entry_description in target_description
            ):
                exact_name = entry

        if best_fuzzy is None or (
            best_fuzzy is not None
            and SequenceMatcher(
                None,
                target_combined,
                _combined_food_text(entry.name, entry.description),
            ).ratio()
            > best_fuzzy[0]
        ):
            ratio = SequenceMatcher(
                None,
                target_combined,
                _combined_food_text(entry.name, entry.description),
            ).ratio()
            if ratio >= _FUZZY_MATCH_THRESHOLD:
                best_fuzzy = (ratio, entry)

    if exact_name is not None:
        return exact_name
    if best_fuzzy is not None:
        return best_fuzzy[1]
    return None


def nutrition_estimate_from_entry(entry: FoodEntry) -> NutritionEstimate:
    prior_notes = (entry.estimation_notes or "").strip()
    notes = f"Reused nutrition from prior log entry #{entry.id}."
    if prior_notes:
        notes = f"{notes} {prior_notes}"

    return NutritionEstimate(
        name=entry.name,
        description=entry.description,
        calories=float(entry.calories),
        protein_g=float(entry.protein_g),
        carbs_g=float(entry.carbs_g),
        fat_g=float(entry.fat_g),
        fiber_g=float(entry.fiber_g),
        notes=notes,
    )
