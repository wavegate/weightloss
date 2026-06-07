"""drop user_event_preferences table

Revision ID: a1b2c3d4e5f6
Revises: f3c8d21a9b01
Create Date: 2026-06-06 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f3c8d21a9b01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        op.f("ix_user_event_preferences_user_id"),
        table_name="user_event_preferences",
    )
    op.drop_table("user_event_preferences")


def downgrade() -> None:
    op.create_table(
        "user_event_preferences",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("home_location", sa.String(length=64), nullable=False),
        sa.Column("distance_miles", sa.Integer(), nullable=False),
        sa.Column("default_timing", sa.String(length=32), nullable=False),
        sa.Column("free_only", sa.Boolean(), nullable=False),
        sa.Column("max_price_usd", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("interest_keywords", sa.String(length=256), nullable=False),
        sa.Column("categories", sa.JSON(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_event_preferences_user_id"),
        "user_event_preferences",
        ["user_id"],
        unique=True,
    )
