import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.clerk import CurrentUserId
from app.database import get_db
from app.models.food_entry import FoodEntry
from app.schemas.food_entry import FoodEntryCreate, FoodEntryRead
from app.services.nutrition_agent import estimate_nutrition

router = APIRouter(prefix="/foods", tags=["foods"])


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
    payload: FoodEntryCreate,
    db: Session = Depends(get_db),
    user_id: str = CurrentUserId,
) -> FoodEntry:
    try:
        estimate = await asyncio.to_thread(
            estimate_nutrition,
            payload.name,
            payload.description,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to estimate nutrition: {exc}",
        ) from exc

    entry = FoodEntry(
        user_id=user_id,
        recorded_at=payload.recorded_at,
        name=payload.name,
        description=payload.description,
        calories=estimate.calories,
        protein_g=estimate.protein_g,
        carbs_g=estimate.carbs_g,
        fat_g=estimate.fat_g,
        estimation_notes=estimate.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
