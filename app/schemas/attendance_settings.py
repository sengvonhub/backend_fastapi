from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, time


class AttendanceSettingsBase(BaseModel):
    # ─────────────────────────────────────────────
    # GPS
    # ─────────────────────────────────────────────

    office_latitude: float = Field(
        ...,
        description="Office GPS latitude",
    )

    office_longitude: float = Field(
        ...,
        description="Office GPS longitude",
    )

    allowed_radius_meters: int = Field(
        100,
        ge=10,
        le=10000,
        description="Allowed check-in radius in meters",
    )

    # ─────────────────────────────────────────────
    # Attendance Rules
    # ─────────────────────────────────────────────

    office_open_time: time = Field(
        default=time(9, 0),
        description="Office opening time",
    )

    office_close_time: time = Field(
        default=time(17, 0),
        description="Office closing time",
    )

    late_threshold_minutes: int = Field(
        15,
        ge=0,
        le=480,
    )

    overtime_threshold_minutes: int = Field(
        480,
        ge=60,
        le=1440,
    )

    timezone: str = Field(
        default="Asia/Phnom_Penh",
    )


class AttendanceSettingsCreate(AttendanceSettingsBase):
    pass


class AttendanceSettingsUpdate(BaseModel):
    office_latitude: Optional[float] = None
    office_longitude: Optional[float] = None

    allowed_radius_meters: Optional[int] = Field(
        None,
        ge=10,
        le=10000,
    )

    office_open_time: Optional[time] = None

    office_close_time: Optional[time] = None

    late_threshold_minutes: Optional[int] = Field(
        None,
        ge=0,
        le=480,
    )

    overtime_threshold_minutes: Optional[int] = Field(
        None,
        ge=60,
        le=1440,
    )

    timezone: Optional[str] = None


class AttendanceSettingsResponse(AttendanceSettingsBase):
    setting_id: int
    company_id: int
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True