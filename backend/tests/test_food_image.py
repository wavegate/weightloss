import pytest

from app.services.food_image import MAX_IMAGE_BYTES, validate_image_upload


def test_validate_image_upload_accepts_jpeg() -> None:
    validate_image_upload("image/jpeg", 1024)


def test_validate_image_upload_rejects_unknown_type() -> None:
    with pytest.raises(ValueError, match="Unsupported image type"):
        validate_image_upload("application/pdf", 1024)


def test_validate_image_upload_rejects_oversized() -> None:
    with pytest.raises(ValueError, match="5 MB"):
        validate_image_upload("image/png", MAX_IMAGE_BYTES + 1)


def test_validate_image_upload_rejects_empty() -> None:
    with pytest.raises(ValueError, match="empty"):
        validate_image_upload("image/png", 0)
