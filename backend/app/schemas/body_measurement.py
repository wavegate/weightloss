from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class BodyMeasurementCreate(BaseModel):
    recorded_at: date
    body_weight_lbs: float = Field(gt=0, description="Body weight in pounds")
    waist_inches: float = Field(gt=0, description="Waist circumference in inches")


class BodyMeasurementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recorded_at: date
    body_weight_lbs: float
    waist_inches: float
