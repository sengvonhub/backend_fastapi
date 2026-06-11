"""add chat enum

Revision ID: 7584bdf17858
Revises: 047132d5a528
Create Date: 2026-05-29 12:53:15.997224
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '7584bdf17858'
down_revision: Union[str, Sequence[str], None] = '047132d5a528'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute(
        "ALTER TYPE notificationtype ADD VALUE 'chat'"
    )

def downgrade() -> None:
    pass