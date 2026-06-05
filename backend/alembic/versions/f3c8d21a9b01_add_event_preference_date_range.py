"""add event preference date range

Revision ID: f3c8d21a9b01
Revises: e7a2b9c14f20
Create Date: 2026-06-04 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f3c8d21a9b01"
down_revision: Union[str, Sequence[str], None] = "e7a2b9c14f20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_event_preferences",
        sa.Column("start_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "user_event_preferences",
        sa.Column("end_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_event_preferences", "end_date")
    op.drop_column("user_event_preferences", "start_date")
