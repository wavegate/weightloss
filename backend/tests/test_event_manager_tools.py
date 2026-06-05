from app.services.event_manager_tools import (
    _parse_categories,
    _parse_optional_bool,
)


def test_parse_optional_bool() -> None:
    assert _parse_optional_bool("") is None
    assert _parse_optional_bool("true") is True
    assert _parse_optional_bool("false") is False


def test_parse_categories() -> None:
    assert _parse_categories("") is None
    assert _parse_categories("clear") == []
    assert _parse_categories("tech, music") == ["tech", "music"]
