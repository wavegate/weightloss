from app.services.elevenlabs_service import plain_text_for_speech


def test_plain_text_for_speech_strips_markdown() -> None:
    raw = "Hello **coach** — see [food log](/food) and `code`.\n\n# Title"
    assert plain_text_for_speech(raw) == "Hello coach — see food log and code. Title"
