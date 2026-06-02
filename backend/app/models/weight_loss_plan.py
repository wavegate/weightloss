from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WeightLossPlan(Base):
    __tablename__ = "weight_loss_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    start_weight_lbs: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    target_weight_lbs: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    tdee_kcal: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    daily_calorie_target: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    daily_deficit_kcal: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
