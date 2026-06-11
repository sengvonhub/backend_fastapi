"""update staff to users in chat group

Revision ID: 1c88180eba3b
Revises: 7584bdf17858
Create Date: 2026-06-09 06:12:52.055156
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1c88180eba3b"
down_revision: Union[str, Sequence[str], None] = "7584bdf17858"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Add new column as nullable
    op.add_column(
        "chat_group_members",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )

    # 2. Create FK to users
    op.create_foreign_key(
        "fk_chat_group_members_user",
        "chat_group_members",
        "users",
        ["user_id"],
        ["user_id"],
        ondelete="CASCADE",
    )

    # 3. Copy staff.user_id into chat_group_members.user_id
    op.execute("""
        UPDATE chat_group_members cgm
        SET user_id = s.user_id
        FROM staff s
        WHERE cgm.staff_id = s.staff_id
    """)

    # 4. Make user_id required
    op.alter_column(
        "chat_group_members",
        "user_id",
        nullable=False,
    )

    # 5. Remove old FK
    op.drop_constraint(
        "chat_group_members_staff_id_fkey",
        "chat_group_members",
        type_="foreignkey",
    )

    # 6. Remove old column
    op.drop_column(
        "chat_group_members",
        "staff_id",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.add_column(
        "chat_group_members",
        sa.Column(
            "staff_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "chat_group_members_staff_id_fkey",
        "chat_group_members",
        "staff",
        ["staff_id"],
        ["staff_id"],
    )

    op.execute("""
        UPDATE chat_group_members cgm
        SET staff_id = s.staff_id
        FROM staff s
        WHERE cgm.user_id = s.user_id
    """)

    op.alter_column(
        "chat_group_members",
        "staff_id",
        nullable=False,
    )

    op.drop_constraint(
        "fk_chat_group_members_user",
        "chat_group_members",
        type_="foreignkey",
    )

    op.drop_column(
        "chat_group_members",
        "user_id",
    )