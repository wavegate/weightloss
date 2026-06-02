from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Sex = Literal["male", "female"]
ActivityLevel = Literal[
    "sedentary",
    "light",
    "moderate",
    "active",
    "very_active",
]


class MetabolicProfileRead(BaseModel):
    sex: Sex
    age_years: int
    height_cm: float
    activity_level: ActivityLevel
    bmr_kcal: float | None
    tdee_kcal: float | None
    notes: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class MetabolicProfileUpsert(BaseModel):
    sex: Sex
    age_years: int = Field(ge=13, le=120)
    height_cm: float = Field(gt=0)
    activity_level: ActivityLevel
    bmr_kcal: float | None = Field(default=None, gt=0)
    tdee_kcal: float | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None, max_length=512)
