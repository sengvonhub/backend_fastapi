from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Numeric,
    TIMESTAMP,
    Time,
)

from datetime import time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.timezone import cambodia_now
from app.db.base import Base


class AttendanceSettings(Base):
    __tablename__ = "attendance_settings"

    setting_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(
        Integer,
        ForeignKey("companies.company_id"),
        nullable=False,
        unique=True,
    )

    # ─────────────────────────────────────────────
    # GPS
    # ─────────────────────────────────────────────

    office_latitude = Column(
        Numeric(10, 7),
        nullable=False,
        default=0,
    )

    office_longitude = Column(
        Numeric(10, 7),
        nullable=False,
        default=0,
    )

    allowed_radius_meters = Column(
        Integer,
        nullable=False,
        default=100,
    )

    # ─────────────────────────────────────────────
    # Attendance Rules
    # ─────────────────────────────────────────────

    office_open_time = Column(
        Time,
        nullable=False,
        default=time(9, 0),
    )

    office_close_time = Column(
        Time,
        nullable=False,
        default=time(17, 0),
    )

    late_threshold_minutes = Column(
        Integer,
        nullable=False,
        default=15,
    )

    overtime_threshold_minutes = Column(
        Integer,
        nullable=False,
        default=480,
    )

    created_at = Column(
    TIMESTAMP(timezone=True),
    default=cambodia_now,
    )

    updated_at = Column(
    TIMESTAMP(timezone=True),
    default=cambodia_now,
    onupdate=cambodia_now,
    )

    # ─────────────────────────────────────────────
    # Relationships
    # ─────────────────────────────────────────────

    company = relationship(
        "Company",
        back_populates="attendance_settings",
    )