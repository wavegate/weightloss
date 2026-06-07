"""add meetup_events table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-07 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meetup_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("meetup_event_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("venue", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("region", sa.String(length=64), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("is_free", sa.Boolean(), nullable=True),
        sa.Column("cost_summary", sa.String(length=128), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("search_location", sa.String(length=64), nullable=False),
        sa.Column("search_keywords", sa.String(length=256), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meetup_event_id"),
    )
    op.create_index(
        op.f("ix_meetup_events_search_location"),
        "meetup_events",
        ["search_location"],
        unique=False,
    )
    op.create_index(
        op.f("ix_meetup_events_start_at"),
        "meetup_events",
        ["start_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_meetup_events_start_at"), table_name="meetup_events")
    op.drop_index(op.f("ix_meetup_events_search_location"), table_name="meetup_events")
    op.drop_table("meetup_events")
