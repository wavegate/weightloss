from datetime import date

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.clerk import CurrentUserId
from app.database import get_db
from app.models.metabolic_profile import MetabolicProfile
from app.models.weight_loss_plan import WeightLossPlan
from app.schemas.metabolic_profile import MetabolicProfileRead
from app.schemas.weight_loss_plan import WeightLossPlanRead
from app.services.user_date import resolve_user_local_date_from_header
from app.services.weight_loss_plan import serialize_weight_loss_plan

router = APIRouter(prefix="/metabolism", tags=["metabolism"])


def _plan_to_read(plan: WeightLossPlan, today: date) -> WeightLossPlanRead:
    summary = serialize_weight_loss_plan(plan, reference_date=today)
    return WeightLossPlanRead(
        **summary,
        updated_at=plan.updated_at.isoformat(),
    )


@router.get("/profile", response_model=MetabolicProfileRead | None)
def get_metabolic_profile(
    db: Session = Depends(get_db),
    user_id: str = CurrentUserId,
) -> MetabolicProfile | None:
    return db.scalar(
        select(MetabolicProfile).where(MetabolicProfile.user_id == user_id)
    )


@router.get("/plan", response_model=WeightLossPlanRead | None)
def get_weight_loss_plan(
    db: Session = Depends(get_db),
    user_id: str = CurrentUserId,
    x_user_local_date: str | None = Header(default=None, alias="X-User-Local-Date"),
) -> WeightLossPlanRead | None:
    plan = db.scalar(
        select(WeightLossPlan).where(WeightLossPlan.user_id == user_id)
    )
    if plan is None:
        return None
    today = resolve_user_local_date_from_header(x_user_local_date)
    return _plan_to_read(plan, today)
