import asyncio

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.clerk import CurrentUserId
from app.database import get_db
from app.models.body_measurement import BodyMeasurement
from app.models.weight_loss_plan import WeightLossPlan
from app.schemas.styling import StylingImageResult, StylingVisualizationRead
from app.services.food_image import validate_image_upload
from app.services.styling_service import DISCLAIMER, visualize_at_target_weight

router = APIRouter(prefix="/styling", tags=["styling"])


def _resolve_weights(
    *,
    latest_measurement: BodyMeasurement | None,
    plan: WeightLossPlan | None,
    target_weight_lbs: float | None,
) -> tuple[float, float]:
    current: float | None = None
    if latest_measurement is not None:
        current = float(latest_measurement.body_weight_lbs)
    elif plan is not None:
        current = float(plan.start_weight_lbs)

    target: float | None = target_weight_lbs
    if target is None and plan is not None:
        target = float(plan.target_weight_lbs)

    if current is None:
        raise HTTPException(
            status_code=422,
            detail="Log your body weight on the measurements page first.",
        )
    if target is None:
        raise HTTPException(
            status_code=422,
            detail="Set a goal weight (weight-loss plan) or enter a target weight.",
        )
    if target >= current:
        raise HTTPException(
            status_code=422,
            detail="Target weight must be less than your current weight.",
        )
    return current, target


@router.post("/visualize", response_model=StylingVisualizationRead)
async def visualize_goal_appearance(
    image: UploadFile = File(...),
    target_weight_lbs: float | None = Form(default=None),
    db: Session = Depends(get_db),
    user_id: str = CurrentUserId,
) -> StylingVisualizationRead:
    if not image.filename:
        raise HTTPException(status_code=422, detail="Photo is required.")

    image_bytes = await image.read()
    try:
        validate_image_upload(image.content_type, len(image_bytes))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    latest = db.scalar(
        select(BodyMeasurement)
        .where(BodyMeasurement.user_id == user_id)
        .order_by(
            BodyMeasurement.recorded_at.desc(),
            BodyMeasurement.id.desc(),
        )
        .limit(1)
    )
    plan = db.scalar(
        select(WeightLossPlan).where(WeightLossPlan.user_id == user_id)
    )
    current, target = _resolve_weights(
        latest_measurement=latest,
        plan=plan,
        target_weight_lbs=target_weight_lbs,
    )

    assert image.content_type is not None
    try:
        b64_png, _prompt = await asyncio.to_thread(
            visualize_at_target_weight,
            image_bytes=image_bytes,
            image_media_type=image.content_type,
            current_weight_lbs=current,
            target_weight_lbs=target,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to generate visualization. Try again with a clearer full-body photo.",
        ) from exc

    lbs_to_lose = current - target
    return StylingVisualizationRead(
        disclaimer=DISCLAIMER,
        current_weight_lbs=current,
        target_weight_lbs=target,
        lbs_to_lose=lbs_to_lose,
        images=[
            StylingImageResult(label="goal", b64_png=b64_png),
        ],
    )
