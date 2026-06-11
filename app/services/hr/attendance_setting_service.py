from datetime import time
import math
from typing import Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.staffs.attendance_settings import AttendanceSettings
from app.repositories.hr.attendance_settings_repository import AttendanceSettingsRepository
from app.dependencies import get_db
from app.schemas.attendance_settings import AttendanceSettingsCreate
class AttendanceSettingService:
    def __init__(self,
                 db: AsyncSession,
                 repo: AttendanceSettingsRepository,
        ):
        self.db=db
        self.repo =repo
    # -----------------------------------------------------------------------
    # GET settings for a company
    # -----------------------------------------------------------------------
    async def get_settings(self, company_id: int):
            return await self.repo.get_or_create(company_id)

    # -----------------------------------------------------------------------
    # UPDATE settings for a company
    # -----------------------------------------------------------------------
    async def upsert_settings(
        self,
        company_id: int,
        office_latitude: Optional[float] = None,
        office_longitude: Optional[float] = None,
        allowed_radius_meters: Optional[int] = None,

        office_open_time: Optional[time] = None,
        office_close_time: Optional[time] = None,

        late_threshold_minutes: Optional[int] = None,
        overtime_threshold_minutes: Optional[int] = None,

        timezone: Optional[str] = None,
    ) -> AttendanceSettings:
        existing = await self.repo.get_by_company_id(company_id)
        update_data = {
            "office_latitude": office_latitude,
            "office_longitude": office_longitude,
            "allowed_radius_meters": allowed_radius_meters,

            "office_open_time": office_open_time,
            "office_close_time": office_close_time,

            "late_threshold_minutes": late_threshold_minutes,
            "overtime_threshold_minutes": overtime_threshold_minutes,

            "timezone": timezone,
        }
        update_data = {
            k: v for k, v in update_data.items()
            if v is not None
        }
        # CREATE
        if existing is None:
            return await self.repo.create(
                company_id=company_id,

                office_latitude=office_latitude or 0.0,
                office_longitude=office_longitude or 0.0,

                allowed_radius_meters=allowed_radius_meters or 100,

                office_open_time=office_open_time or time(9, 0),
                office_close_time=office_close_time or time(17, 0),

                late_threshold_minutes=late_threshold_minutes or 15,
                overtime_threshold_minutes=overtime_threshold_minutes or 480,

                timezone=timezone or "Asia/Phnom_Penh",
            )
        return await self.repo.update(
            obj=existing,
            **update_data
        )
    # -----------------------------------------------------------------------
    # CALCULATE DISTANCE BETWEEN TWO COORDINATES
    # -----------------------------------------------------------------------
    async def validate_geofence(
            self,
            company_id: int,
            latitude: float,
            longitude: float
    ) -> float:
        settings = await self.repo.get_by_company_id(company_id)
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attendance settings not configured for this company"
            )
        
        distance_m = self._haversine_metters(
            lat1= float(settings.office_latitude),
            lon1= float(settings.office_longitude),
            lat2= latitude,
            lon2= longitude
        )
        if distance_m > settings.allowed_radius_meters:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Check-in location is {distance_m:.2f} meters away from office, which exceeds the allowed radius of {settings.allowed_radius_meters} meters."
            )
        print("DISTANCE:", distance_m)
        print("RADIUS:", settings.allowed_radius_meters)
        return distance_m
    
    # -----------------------------------------------------------------------
    #  IS LATE - calculate if check-in time is after late threshold
    # -----------------------------------------------------------------------
    async def is_late(
            self,
            company_id: int,
            shif_start_minutes_sine_midnight: int,
            check_in_time_minutes_sine_midnight: int
    ) -> bool:
        settings = await self.repo.get_by_company_id(company_id)
        threshold = settings.late_threshold_minutes if settings else 9*60  # default to 9:00 AM if no settings
        return (check_in_time_minutes_sine_midnight - shif_start_minutes_sine_midnight) > threshold

    # -----------------------------------------------------------------------
    #  IS OVERTIME - calculate if check-out time is after overtime threshold
    # -----------------------------------------------------------------------
    async def is_overtime(
            self,
            company_id: int,
            worked_minutes: int,
    ) -> bool:
        settings =await self.repo.get_by_company_id(company_id)
        threshold = settings.overtime_threshold_minutes if settings else 18*60  # default to 6:00 PM if no settings
        return worked_minutes > threshold



    @staticmethod
    def _haversine_metters(
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        R = 6_371_000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2) ** 2 +
            math.cos(phi1) * math.cos(phi2) *
            math.sin(delta_lambda / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

async def get_attendance_setting_service(
        db: AsyncSession = Depends(get_db)
        )-> AttendanceSettingService:
    return AttendanceSettingService(
        db = db,
        repo = AttendanceSettingsRepository(db),
    )

    

      

    