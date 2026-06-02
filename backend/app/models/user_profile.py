from datetime import date
from enum import StrEnum

from sqlalchemy import Date, Enum, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(StrEnum):
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTREMELY_ACTIVE = "extremely_active"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    sex: Mapped[Sex] = mapped_column(Enum(Sex, native_enum=False), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    activity_level: Mapped[ActivityLevel] = mapped_column(
        Enum(ActivityLevel, native_enum=False),
        nullable=False,
    )
