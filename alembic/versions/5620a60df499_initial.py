"""initial

Revision ID: 5620a60df499
Revises: 
Create Date: 2026-03-11 14:12:04.895855

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5620a60df499'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the flag table with the unique constraint included in the CREATE TABLE
    # This avoids ALTER/ADD CONSTRAINT operations which are not supported by SQLite.
    op.create_table(
        "flag",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("app", sa.String(), nullable=False),
        sa.Column("env", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.Boolean(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("app", "env", "key", name="uix_flag_app_env_key"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the flag table (unique constraint is dropped with the table)
    op.drop_table("flag")
