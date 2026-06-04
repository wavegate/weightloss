from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class FoodEntryCreate(BaseModel):
    recorded_at: date
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)


class FoodEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recorded_at: date
    name: str
    description: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    estimation_notes: str | None
