import asyncio
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.clerk import CurrentUserId
from app.database import get_db
from app.models.food_entry import FoodEntry
from app.schemas.food_entry import FoodEntryRead
from app.services.food_image import validate_image_upload
from app.services.food_matching import find_reusable_food_entry, nutrition_estimate_from_entry
from app.services.nutrition_agent import estimate_nutrition

router = APIRouter(prefix="/foods", tags=["foods"])


def _resolve_entry_text(
    name: str,
    description: str,
    *,
    has_image: bool,
    estimate_name: str,
    estimate_description: str,
) -> tuple[str, str]:
    entry_name = name.strip() or estimate_name.strip()
    entry_description = description.strip() or estimate_description.strip()
    if not entry_name or not entry_description:
        if has_image:
            raise HTTPException(
                status_code=502,
                detail="Nutrition agent did not return a food name and description",
            )
        raise HTTPException(
            status_code=422,
            detail="Provide a photo or both food name and description",
        )
    return entry_name, entry_description


@router.get("", response_model=list[FoodEntryRead])
def list_food_entries(
    db: Session = Depends(get_db),
    user_id: str = CurrentUserId,
) -> list[FoodEntry]:
    stmt = (
        select(FoodEntry)
        .where(FoodEntry.user_id == user_id)
        .order_by(
            FoodEntry.recorded_at.desc(),
            FoodEntry.id.desc(),
        )
    )
    return list(db.scalars(stmt).all())


@router.post("", response_model=FoodEntryRead, status_code=201)
async def create_food_entry(
    recorded_at: str = Form(...),
    name: str = Form(""),
    description: str = Form(""),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user_id: str = CurrentUserId,
) -> FoodEntry:
    try:
        entry_date = date.fromisoformat(recorded_at)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="recorded_at must be an ISO date (YYYY-MM-DD)",
        ) from exc

    image_bytes: bytes | None = None
    image_media_type: str | None = None
    has_image = image is not None and bool(image.filename)

    if has_image:
        assert image is not None
        image_bytes = await image.read()
        image_media_type = image.content_type
        try:
            validate_image_upload(image_media_type, len(image_bytes))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    elif not name.strip() or not description.strip():
        raise HTTPException(
            status_code=422,
            detail="Provide a photo or both food name and description",
        )

    try:
        if has_image:
            estimate = await asyncio.to_thread(
                estimate_nutrition,
                name,
                description,
                image_bytes=image_bytes,
                image_media_type=image_media_type,
            )
        else:
            match = find_reusable_food_entry(db, user_id, name, description)
            if match is not None:
                estimate = nutrition_estimate_from_entry(match)
            else:
                estimate = await asyncio.to_thread(
                    estimate_nutrition,
                    name,
                    description,
                )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to estimate nutrition: {exc}",
        ) from exc

    entry_name, entry_description = _resolve_entry_text(
        name,
        description,
        has_image=has_image,
        estimate_name=estimate.name,
        estimate_description=estimate.description,
    )

    entry = FoodEntry(
        user_id=user_id,
        recorded_at=entry_date,
        name=entry_name,
        description=entry_description,
        calories=estimate.calories,
        protein_g=estimate.protein_g,
        carbs_g=estimate.carbs_g,
        fat_g=estimate.fat_g,
        fiber_g=estimate.fiber_g,
        estimation_notes=estimate.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_food_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    user_id: str = CurrentUserId,
) -> None:
    entry = db.get(FoodEntry, entry_id)
    if entry is None or entry.user_id != user_id:
        raise HTTPException(status_code=404, detail="Food entry not found")
    db.delete(entry)
    db.commit()
