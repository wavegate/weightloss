from datetime import date

from sqlalchemy import Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recorded_at: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    body_weight_lbs: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    waist_inches: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
