
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..roles import Role

class Permission(Base):
    __tablename__ = "permissions"

    permission_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # global, not per-company — "manage_salary" means the same thing everywhere
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="role_permissions", back_populates="permissions"
    )