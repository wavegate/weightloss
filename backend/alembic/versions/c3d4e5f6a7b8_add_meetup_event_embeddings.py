"""add meetup event embeddings

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-07 18:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "meetup_events",
        sa.Column("embedding_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "meetup_events",
        sa.Column("embedding_model", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "meetup_events",
        sa.Column("embedding", Vector(1536), nullable=True),
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_meetup_events_embedding_hnsw
        ON meetup_events USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_meetup_events_embedding_hnsw")
    op.drop_column("meetup_events", "embedding")
    op.drop_column("meetup_events", "embedding_model")
    op.drop_column("meetup_events", "embedding_text")
