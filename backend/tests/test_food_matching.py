from datetime import date
from unittest.mock import MagicMock

from app.services.food_matching import find_reusable_food_entry, normalize_food_text


def test_normalize_food_text() -> None:
    assert normalize_food_text("  Grilled Chicken!! ") == "grilled chicken"


def test_find_reusable_food_entry_exact_match() -> None:
    prior = MagicMock()
    prior.id = 5
    prior.name = "Oatmeal"
    prior.description = "1 cup with berries"
    prior.recorded_at = date(2026, 6, 1)

    db = MagicMock()
    db.scalars.return_value.all.return_value = [prior]

    match = find_reusable_food_entry(
        db,
        "user_1",
        "Oatmeal",
        "1 cup with berries",
    )

    assert match is prior


def test_find_reusable_food_entry_reuses_same_name() -> None:
    prior = MagicMock()
    prior.id = 2
    prior.name = "Greek yogurt"
    prior.description = "1 cup plain"
    prior.recorded_at = date(2026, 6, 1)

    db = MagicMock()
    db.scalars.return_value.all.return_value = [prior]

    match = find_reusable_food_entry(
        db,
        "user_1",
        "greek yogurt",
        "1 cup plain nonfat",
    )

    assert match is prior
