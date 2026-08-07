"""update artwork status

Revision ID: 023449be8cdc
Revises: c8467e7a2a48
Create Date: 2026-07-21 13:56:18.978713

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '023449be8cdc'
down_revision: Union[str, Sequence[str], None] = 'c8467e7a2a48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("COMMIT")
    op.execute("ALTER TYPE artwork_status ADD VALUE IF NOT EXISTS 'needs_revision'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres doesn't support dropping enum values directly.
    # A true downgrade would require creating a new enum type without
    # 'needs_revision', migrating the column to it, and dropping the old type.
    pass