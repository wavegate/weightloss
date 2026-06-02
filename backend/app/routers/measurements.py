from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.body_measurement import BodyMeasurement
from app.schemas.body_measurement import BodyMeasurementCreate, BodyMeasurementRead

router = APIRouter(prefix="/measurements", tags=["measurements"])


@router.get("", response_model=list[BodyMeasurementRead])
def list_measurements(db: Session = Depends(get_db)) -> list[BodyMeasurement]:
    stmt = select(BodyMeasurement).order_by(
        BodyMeasurement.recorded_at.desc(),
        BodyMeasurement.id.desc(),
    )
    return list(db.scalars(stmt).all())


@router.post("", response_model=BodyMeasurementRead, status_code=201)
def create_measurement(
    payload: BodyMeasurementCreate,
    db: Session = Depends(get_db),
) -> BodyMeasurement:
    measurement = BodyMeasurement(
        recorded_at=payload.recorded_at,
        body_weight_lbs=payload.body_weight_lbs,
        waist_inches=payload.waist_inches,
    )
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement
