from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MetabolicProfile(Base):
    __tablename__ = "metabolic_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    sex: Mapped[str] = mapped_column(String(16), nullable=False)
    age_years: Mapped[int] = mapped_column(Integer, nullable=False)
    height_cm: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    activity_level: Mapped[str] = mapped_column(String(32), nullable=False)
    bmr_kcal: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    tdee_kcal: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
