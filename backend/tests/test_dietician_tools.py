import json
from datetime import date
from unittest.mock import MagicMock, patch

from app.services.dietician_tools import (
    _macro_targets_from_budget,
    _serialize_food_entry,
    summarize_food_log,
)
from app.services.handoff_tools import (
    DIETICIAN_AGENT_NAME,
    transfer_to_dietician_coach,
)


def test_macro_targets_from_budget_30_40_30() -> None:
    targets = _macro_targets_from_budget(2000)
    assert targets == {
        "calories": 2000,
        "protein_g": 150,
        "carbs_g": 200,
        "fat_g": 67,
    }


def test_serialize_food_entry_includes_local_date() -> None:
    entry = MagicMock()
    entry.id = 1
    entry.recorded_at = date(2026, 6, 1)
    entry.name = "Oatmeal"
    entry.description = "1 cup with berries"
    entry.calories = 350.0
    entry.protein_g = 12.0
    entry.carbs_g = 55.0
    entry.fat_g = 8.0
    entry.estimation_notes = "Estimated from USDA"

    payload = _serialize_food_entry(entry, local_date=date(2026, 6, 1))
    assert payload["id"] == 1
    assert payload["local_date"] == "2026-06-01"
    assert payload["calories"] == 350.0


@patch("app.services.dietician_tools._load_food_entries")
@patch("app.services.dietician_tools.SessionLocal")
def test_summarize_food_log_week(mock_session_local, mock_load_entries) -> None:
    mock_load_entries.return_value = []
    mock_session_local.return_value.__enter__.return_value.scalar.return_value = None

    config = {
        "configurable": {
            "user_id": "user_test",
            "user_local_date": "2026-06-02",
            "user_timezone": "America/New_York",
        }
    }

    result = json.loads(
        summarize_food_log.func(period="week", config=config)  # type: ignore[attr-defined]
    )
    assert result["period"] == "week"
    assert result["start_date"] == "2026-05-26"
    assert result["end_date"] == "2026-06-02"
    assert result["total_entries"] == 0


def test_transfer_to_dietician_coach_sets_active_agent() -> None:
    runtime = MagicMock()
    runtime.tool_call_id = "call_123"

    command = transfer_to_dietician_coach.func(  # type: ignore[attr-defined]
        reason="User wants to log lunch",
        runtime=runtime,
    )

    assert command.update["active_agent"] == DIETICIAN_AGENT_NAME
    assert command.update["messages"][0].tool_call_id == "call_123"
