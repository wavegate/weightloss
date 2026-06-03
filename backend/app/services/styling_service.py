from io import BytesIO

from openai import OpenAI

from app.config import get_settings

OPENAI_IMAGE_MODEL = "gpt-image-2"

DISCLAIMER = (
    "AI-generated illustration only. Not a guarantee of results and not medical advice."
)


def _weight_loss_percent(current_lbs: float, target_lbs: float) -> float:
    if current_lbs <= 0:
        return 0.0
    return max(0.0, (current_lbs - target_lbs) / current_lbs * 100)


def _change_only_descriptor(percent_lost: float, lbs_to_lose: float) -> str:
    if percent_lost < 6:
        return (
            f"a very subtle, believable slimming (~{percent_lost:.0f}% body weight, "
            f"about {lbs_to_lose:.0f} lbs) — slightly narrower waist only"
        )
    if percent_lost < 12:
        return (
            f"a modest, believable slimming (~{percent_lost:.0f}% body weight, "
            f"about {lbs_to_lose:.0f} lbs) — slimmer waist and lower abdomen"
        )
    if percent_lost < 20:
        return (
            f"a clear but realistic slimming (~{percent_lost:.0f}% body weight, "
            f"about {lbs_to_lose:.0f} lbs) — slimmer waist, abdomen, and slightly "
            "less facial/neck fullness if visible"
        )
    if percent_lost < 30:
        return (
            f"a noticeable realistic slimming (~{percent_lost:.0f}% body weight, "
            f"about {lbs_to_lose:.0f} lbs) — leaner waist, abdomen, arms, and "
            "moderately reduced facial fullness; avoid exaggeration"
        )
    return (
        f"a significant but still realistic slimming (~{percent_lost:.0f}% body weight, "
        f"about {lbs_to_lose:.0f} lbs) — leaner torso and limbs with moderate facial "
        "slimming; must not look like a different person or a caricature"
    )


def build_edit_prompt(current_lbs: float, target_lbs: float) -> str:
    lbs_to_lose = current_lbs - target_lbs
    percent_lost = _weight_loss_percent(current_lbs, target_lbs)
    change_only = _change_only_descriptor(percent_lost, lbs_to_lose)

    return f"""Image 1: The person's current real photograph.

TASK: Create a photorealistic "goal weight" version of Image 1 showing how this same person might look after healthy weight loss from roughly {current_lbs:.0f} lbs to roughly {target_lbs:.0f} lbs.

CHANGE ONLY (surgical edit):
- Apply {change_only}.
- Clothing may hang slightly looser where fabric would naturally drape; do not change outfit style, colors, or patterns.
- Keep muscle definition plausible for this person; do not add bodybuilder musculature or model glamor.

PRESERVE EXACTLY (do not alter):
- Face, facial features, skin tone, ethnicity, age appearance, eyes, expression, makeup, and hairstyle
- Pose, hand positions, limb angles, gaze direction, and body position in frame
- Background, environment, props, lighting direction, shadows, white balance, and color grading
- Camera angle, focal length feel, framing, crop, and image grain/noise
- Number of people (must remain one person)

STYLE:
- Photorealistic real photograph taken on a phone or camera — not illustration, CGI, or airbrushed beauty ad
- Natural skin texture with pores; no smoothing filter, no plastic skin, no dramatic relighting
- No watermark, no text, no logos, no added accessories
"""


def _extension_for_media_type(media_type: str) -> str:
    return {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    }.get(media_type, "png")


def _make_image_file(image_bytes: bytes, image_media_type: str) -> BytesIO:
    image_file = BytesIO(image_bytes)
    image_file.name = f"photo.{_extension_for_media_type(image_media_type)}"
    return image_file


def _image_edit_kwargs(*, model: str, image_file: BytesIO, prompt: str) -> dict:
    kwargs: dict = {
        "model": model,
        "image": image_file,
        "prompt": prompt,
        "quality": "high",
    }
    if model == "gpt-image-2":
        kwargs["size"] = "1024x1536"
    else:
        kwargs["size"] = "auto"
        kwargs["input_fidelity"] = "high"
    return kwargs


def _run_edit(
    client: OpenAI,
    *,
    model: str,
    image_bytes: bytes,
    image_media_type: str,
    prompt: str,
):
    image_file = _make_image_file(image_bytes, image_media_type)
    return client.images.edit(
        **_image_edit_kwargs(model=model, image_file=image_file, prompt=prompt)
    )


def visualize_at_target_weight(
    *,
    image_bytes: bytes,
    image_media_type: str,
    current_weight_lbs: float,
    target_weight_lbs: float,
) -> tuple[str, str]:
    """Return (base64 PNG, edit prompt used)."""
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    prompt = build_edit_prompt(current_weight_lbs, target_weight_lbs)

    try:
        result = _run_edit(
            client,
            model=OPENAI_IMAGE_MODEL,
            image_bytes=image_bytes,
            image_media_type=image_media_type,
            prompt=prompt,
        )
    except Exception:
        if OPENAI_IMAGE_MODEL != "gpt-image-2":
            raise
        result = _run_edit(
            client,
            model="gpt-image-1.5",
            image_bytes=image_bytes,
            image_media_type=image_media_type,
            prompt=prompt,
        )

    if not result.data or not result.data[0].b64_json:
        raise RuntimeError("Image model did not return image data")

    return result.data[0].b64_json, prompt
