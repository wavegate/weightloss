"""add user event preferences

Revision ID: e7a2b9c14f20
Revises: d4f8a1c02e11
Create Date: 2026-06-04 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e7a2b9c14f20"
down_revision: Union[str, Sequence[str], None] = "d4f8a1c02e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_index(
        op.f("ix_user_event_preferences_user_id"),
        table_name="user_event_preferences",
    )
    op.drop_table("user_event_preferences")
