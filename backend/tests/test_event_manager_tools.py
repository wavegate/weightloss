from app.services.event_manager_tools import _parse_optional_bool


def test_parse_optional_bool() -> None:
    assert _parse_optional_bool("true") is True
    assert _parse_optional_bool("false") is False
