"""add weight loss plans

Revision ID: b8c4e2f91a03
Revises: 400b39ab0d58
Create Date: 2026-06-02 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8c4e2f91a03"
down_revision: Union[str, Sequence[str], None] = "400b39ab0d58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "weight_loss_plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("start_weight_lbs", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("target_weight_lbs", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("tdee_kcal", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column(
            "daily_calorie_target", sa.Numeric(precision=8, scale=2), nullable=False
        ),
        sa.Column(
            "daily_deficit_kcal", sa.Numeric(precision=8, scale=2), nullable=False
        ),
        sa.Column("notes", sa.String(length=512), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_weight_loss_plans_user_id"),
        "weight_loss_plans",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_weight_loss_plans_user_id"), table_name="weight_loss_plans")
    op.drop_table("weight_loss_plans")
