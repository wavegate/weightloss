ALLOWED_IMAGE_MEDIA_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def validate_image_upload(content_type: str | None, size: int) -> None:
    if content_type not in ALLOWED_IMAGE_MEDIA_TYPES:
        allowed = ", ".join(sorted(ALLOWED_IMAGE_MEDIA_TYPES))
        raise ValueError(f"Unsupported image type. Allowed: {allowed}")
    if size > MAX_IMAGE_BYTES:
        raise ValueError("Image must be 5 MB or smaller")
    if size == 0:
        raise ValueError("Image file is empty")
