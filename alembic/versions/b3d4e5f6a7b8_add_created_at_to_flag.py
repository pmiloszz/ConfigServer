"""add created_at to flag

Revision ID: b3d4e5f6a7b8
Revises: 5620a60df499
Create Date: 2026-03-24 12:00:00.000000

HOW ALEMBIC VERSIONING WORKS:
  Each migration file has:
    - revision:      its own unique ID
    - down_revision: the ID of the migration it builds on top of
  This forms a chain: None → 5620a60df499 → b3d4e5f6a7b8 → ...
  "alembic upgrade head" walks this chain and applies any unapplied migrations.
  "alembic downgrade -1" reverses the most recent one.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "5620a60df499"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add created_at column to the flag table.

    CURRENT_TIMESTAMP is used as server_default so that:
    - Existing rows (if any) get a sensible value immediately
    - New rows get the correct timestamp if the application layer somehow
      doesn't provide one

    Works on both PostgreSQL and SQLite (used in tests).
    """
    op.add_column(
        "flag",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade() -> None:
    """Remove the created_at column.

    Uses batch_alter_table for SQLite compatibility — SQLite pre-3.35 doesn't
    support DROP COLUMN directly. batch mode recreates the table without the
    column, which works on all versions.
    PostgreSQL uses the direct ALTER TABLE DROP COLUMN path (fast, no copy).
    """
    with op.batch_alter_table("flag") as batch_op:
        batch_op.drop_column("created_at")