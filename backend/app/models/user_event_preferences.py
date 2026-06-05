from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserEventPreferences(Base):
    __tablename__ = "user_event_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    home_location: Mapped[str] = mapped_column(String(64), nullable=False)
    distance_miles: Mapped[int] = mapped_column(Integer, nullable=False)
    default_timing: Mapped[str] = mapped_column(String(32), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    free_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_price_usd: Mapped[float | None] = mapped_column(
        Numeric(8, 2), nullable=True
    )
    interest_keywords: Mapped[str] = mapped_column(String(256), nullable=False)
    categories: Mapped[list] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
