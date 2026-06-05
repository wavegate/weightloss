from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.event_preference_options import (
    DEFAULT_CATEGORIES,
    DEFAULT_DISTANCE_MILES,
    DEFAULT_HOME_LOCATION,
    DEFAULT_TIMING,
    VALID_CATEGORY_IDS,
    VALID_LOCATION_IDS,
    VALID_TIMING_IDS,
)


class EventPreferencesRead(BaseModel):
    home_location: str
    distance_miles: int
    default_timing: str
    start_date: date | None
    end_date: date | None
    free_only: bool
    max_price_usd: float | None
    interest_keywords: str
    categories: list[str]
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventPreferencesUpsert(BaseModel):
    home_location: str = DEFAULT_HOME_LOCATION
    distance_miles: int = Field(default=DEFAULT_DISTANCE_MILES, ge=5, le=100)
    default_timing: str = DEFAULT_TIMING
    start_date: date | None = None
    end_date: date | None = None
    free_only: bool = False
    max_price_usd: float | None = Field(default=None, ge=0)
    interest_keywords: str = Field(default="", max_length=256)
    categories: list[str] = Field(default_factory=lambda: list(DEFAULT_CATEGORIES))

    @field_validator("home_location")
    @classmethod
    def validate_location(cls, value: str) -> str:
        key = value.strip().lower()
        if key not in VALID_LOCATION_IDS:
            raise ValueError(f"Unsupported home_location: {value}")
        return key

    @field_validator("default_timing")
    @classmethod
    def validate_timing(cls, value: str) -> str:
        key = value.strip().lower()
        if key not in VALID_TIMING_IDS:
            raise ValueError(f"Unsupported default_timing: {value}")
        return key

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            key = item.strip().lower()
            if not key:
                continue
            if key not in VALID_CATEGORY_IDS:
                raise ValueError(f"Unsupported category: {item}")
            if key not in cleaned:
                cleaned.append(key)
        return cleaned

    @field_validator("interest_keywords")
    @classmethod
    def normalize_keywords(cls, value: str) -> str:
        return " ".join(value.strip().split())

    @model_validator(mode="after")
    def validate_date_range(self) -> "EventPreferencesUpsert":
        if self.default_timing == "date-range" and (
            self.start_date is None or self.end_date is None
        ):
            object.__setattr__(self, "default_timing", DEFAULT_TIMING)
            object.__setattr__(self, "start_date", None)
            object.__setattr__(self, "end_date", None)
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError("start_date and end_date must both be set or both empty")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.default_timing != "date-range" and (
            self.start_date is not None or self.end_date is not None
        ):
            object.__setattr__(self, "start_date", None)
            object.__setattr__(self, "end_date", None)
        return self
