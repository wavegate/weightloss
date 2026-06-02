from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.clerk import CurrentUserId
from app.database import get_db
from app.models.metabolic_profile import MetabolicProfile
from app.schemas.metabolic_profile import MetabolicProfileRead

router = APIRouter(prefix="/metabolism", tags=["metabolism"])


@router.get("/profile", response_model=MetabolicProfileRead | None)
def get_metabolic_profile(
    db: Session = Depends(get_db),
    user_id: str = CurrentUserId,
) -> MetabolicProfile | None:
    return db.scalar(
        select(MetabolicProfile).where(MetabolicProfile.user_id == user_id)
    )
