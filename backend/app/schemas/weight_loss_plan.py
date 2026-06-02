from datetime import date

from pydantic import BaseModel, Field


class WeightLossPlanRead(BaseModel):
    start_weight_lbs: float
    target_weight_lbs: float
    start_date: date
    target_date: date
    tdee_kcal: float
    daily_calorie_target: float
    daily_deficit_kcal: float
    weight_to_lose_lbs: float
    days_until_goal: int
    notes: str | None
    updated_at: str

    model_config = {"from_attributes": True}


class WeightLossPlanUpsert(BaseModel):
    target_weight_lbs: float = Field(gt=0)
    target_date: date
    current_weight_lbs: float | None = Field(default=None, gt=0)
    tdee_kcal: float | None = Field(default=None, gt=0)
    notes: str | None = None
