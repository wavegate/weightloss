"""add fiber_g to food entries

Revision ID: d4f8a1c02e11
Revises: b8c4e2f91a03
Create Date: 2026-06-03 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4f8a1c02e11"
down_revision: Union[str, Sequence[str], None] = "b8c4e2f91a03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_entries",
        sa.Column(
            "fiber_g",
            sa.Numeric(precision=7, scale=2),
            nullable=False,
            server_default="0",
        ),
    )
    op.alter_column("food_entries", "fiber_g", server_default=None)


def downgrade() -> None:
    op.drop_column("food_entries", "fiber_g")
