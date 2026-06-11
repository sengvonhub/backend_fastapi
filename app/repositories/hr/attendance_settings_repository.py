from datetime import time

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from app.models.staffs import AttendanceSettings, attendance_settings
from app.schemas.attendance_settings import AttendanceSettingsCreate, AttendanceSettingsUpdate
from typing import Optional

class AttendanceSettingsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # GET settings for a company
    # -----------------------------------------------------------------------
    async def get_by_company_id(self, company_id: int) -> Optional[AttendanceSettings]:
        result = await self.db.execute(
            select(AttendanceSettings).where(AttendanceSettings.company_id == company_id)
        )
        return result.scalar_one_or_none()
    
    # -----------------------------------------------------------------------
    # GET OR CREATE WITH DEFAULTS  = SCREEN ALWAYS CALLS THIS BEFORE CHECK-IN
    # -----------------------------------------------------------------------
    
    async def get_or_create(self, company_id: int):
        obj = await self.get_by_company_id(company_id)
        if obj:
            return obj
        obj = AttendanceSettings(
            company_id=company_id,
            office_latitude=11.5564,
            office_longitude=104.9282,
            allowed_radius_meters=100,
            office_open_time=time(9, 0),
            office_close_time=time(17, 0),
            late_threshold_minutes=15,
            overtime_threshold_minutes=480,
            timezone="Asia/Phnom_Penh",
        )
        self.db.add(obj)
        try:
            await self.db.commit()
            await self.db.refresh(obj)
            return obj
        except IntegrityError:
            await self.db.rollback()
            return await self.get_by_company_id(company_id)
    

    # -----------------------------------------------------------------------
    # create settings
    # -----------------------------------------------------------------------
    async def create(
        self,
        company_id: int,
        office_latitude: float,
        office_longitude: float,
        allowed_radius_meters: int,
        office_open_time: time,
        office_close_time: time,
        late_threshold_minutes: int,
        overtime_threshold_minutes: int,
        timezone: str,
    ) -> AttendanceSettings:

        obj = AttendanceSettings(
            company_id=company_id,
            office_latitude=office_latitude,
            office_longitude=office_longitude,
            allowed_radius_meters=allowed_radius_meters,
            office_open_time=office_open_time,
            office_close_time=office_close_time,
            late_threshold_minutes=late_threshold_minutes,
            overtime_threshold_minutes=overtime_threshold_minutes,
            timezone=timezone,
        )
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)

        return obj
    
    # -----------------------------------------------------------------------
    # update settings
    # -----------------------------------------------------------------------
    async def update(
        self,
        obj: AttendanceSettings,

        office_latitude: Optional[float] = None,
        office_longitude: Optional[float] = None,
        allowed_radius_meters: Optional[int] = None,

        office_open_time: Optional[time] = None,
        office_close_time: Optional[time] = None,

        late_threshold_minutes: Optional[int] = None,
        overtime_threshold_minutes: Optional[int] = None,

        timezone: Optional[str] = None,
    ) -> AttendanceSettings:

        if office_latitude is not None:
            obj.office_latitude = office_latitude

        if office_longitude is not None:
            obj.office_longitude = office_longitude

        if allowed_radius_meters is not None:
            obj.allowed_radius_meters = allowed_radius_meters

        if office_open_time is not None:
            obj.office_open_time = office_open_time

        if office_close_time is not None:
            obj.office_close_time = office_close_time

        if late_threshold_minutes is not None:
            obj.late_threshold_minutes = late_threshold_minutes

        if overtime_threshold_minutes is not None:
            obj.overtime_threshold_minutes = overtime_threshold_minutes

        if timezone is not None:
            obj.timezone = timezone
        await self.db.commit()
        await self.db.refresh(obj)

        return obj
        
                
        
