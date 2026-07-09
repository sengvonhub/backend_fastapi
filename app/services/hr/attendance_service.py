from datetime import date, time
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import redis.asyncio as redis
import pytz



from app.core.time_check import _is_early, _is_late
from app.core.timezone import cambodia_now, format_time_for_message
from app.repositories.hr.attendance_repository import AttendanceRepository
from app.repositories.hr.attendance_settings_repository import AttendanceSettingsRepository
from app.repositories.hr.staff_repository import StaffRepository
from app.repositories.communication.notifications_repository import NotificationRepository
from app.services.communication.notifications_service import NotificationService
from app.utils.helper import _get_office_open_time
from app.utils.qr_utils import (create_office_qr_token, decode_office_qr_token, generate_qr_image_base64, validate_gps_at_office)
from app.core.security import decode_scan_token
from app.core.config import settings
from app.dependencies import get_db, get_redis_client


class AttendanceService:
    def __init__(
        self,
        db:           AsyncSession,
        repo:         AttendanceRepository,
        settings_repo: AttendanceSettingsRepository,
        staff_repo:   StaffRepository,
        redis_client: redis.Redis,        
    ):
        self.repo       = repo
        self.staff_repo = staff_repo
        self.settings_repo = settings_repo
        self.notif      = NotificationService(  
            db           = db,
            redis_client = redis_client,
        )

    # -----------------------------------------------------------------------
    # Generate office QR
    # -----------------------------------------------------------------------

    async def generate_office_qr(self) -> dict:
        token    = create_office_qr_token()
        qr_image = generate_qr_image_base64(token)
        return {
            "office_id":  settings.OFFICE_ID,
            "qr_token":   token,
            "qr_image":   qr_image,
            "expires_in": "1 year",
            "note":       "Print and stick on office wall. Staff scan this QR after entering password.",
        }

    # -----------------------------------------------------------------------
    # CHECK-IN — notify staff + notify managers if late
    # -----------------------------------------------------------------------
  



    async def check_in(
        self,
        scan_token: str,
        office_qr_token: str,
        latitude: str,
        longitude: str,
        company_id: int,
    ) -> dict:
        staff_id = decode_scan_token(scan_token)
        if not office_qr_token:
           raise HTTPException(status_code=422, detail="office_qr_token is required")
        decode_office_qr_token(office_qr_token)
        att_settings  = await self.settings_repo.get_by_company_id(company_id)
        distance = validate_gps_at_office(
            latitude,
            longitude,
            float(att_settings .office_latitude),
            float(att_settings .office_longitude),
            att_settings .allowed_radius_meters,
        )
        now =  cambodia_now()
        today    = now.date()  
        existing = await self.repo.get_today_record(staff_id, company_id, today)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Already checked in today at {existing.check_in_time}.",
            )
        record = await self.repo.create_check_in(
            staff_id   = staff_id,
            company_id = company_id,
            today      = today,
            latitude   = str(latitude),
            longitude  = str(longitude),
        )
        staff      = await self.staff_repo.get_by_id(staff_id, company_id)
        staff_name = staff.name if staff else "Staff"
        formatted_time = format_time_for_message(record.check_in_time)
        if staff:
            await self.notif.send(
                company_id     = company_id,
                user_id        = staff.user_id,
                title          = "Check-in recorded",
                message        = f"You checked in at {formatted_time}. Have a great day!",
                notif_type     = "success",
                reference_id   = record.attendance_id,
                reference_type = "attendance",
            )
        if _is_late(
            record.check_in_time, 
            att_settings.office_open_time, 
            att_settings.late_threshold_minutes
            ) and staff:
            await self.notif.send(
                company_id=company_id, user_id=staff.user_id,
                title="Late check-in",
                message=f"You checked in late at {record.check_in_time}. Expected by {att_settings.office_open_time}.",
                notif_type="warning", reference_id=record.attendance_id, reference_type="attendance",
            )


            managers = await self.staff_repo.get_managers(company_id)
            
            for manager in managers:
                await self.notif.send(
                    company_id=company_id, user_id=manager.user_id,
                    title="Late check-in alert",
                    message=f"{staff_name} checked in late at {record.check_in_time}. Expected by {att_settings.office_open_time}.",
                    notif_type="warning", reference_id=record.attendance_id, reference_type="attendance",
                )

        return {
            "attendance":      record,
            "staff_name":      staff_name,
            "distance_meters": round(distance, 1),
            "message":         f"Check-in successful! Welcome {staff_name}. ({distance:.0f}m from office)",
        }
    



    # -----------------------------------------------------------------------
    # CHECK-OUT — notify staff
    # -----------------------------------------------------------------------

    async def check_out(self, scan_token, office_qr_token, latitude, longitude, company_id):

        staff_id = decode_scan_token(scan_token)
        decode_office_qr_token(office_qr_token)
        att_settings = await self.settings_repo.get_by_company_id(company_id) 

        distance = validate_gps_at_office(
            latitude, longitude,
            float(att_settings.office_latitude),
            float(att_settings.office_longitude),
            att_settings.allowed_radius_meters,
        )
        now   = cambodia_now()
        today = now.date()
        record = await self.repo.get_today_record(staff_id, company_id, today)

        if not record:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="You have not checked in today.")
        if record.check_out_time:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Already checked out today at {record.check_out_time}.")
        record     = await self.repo.update_check_out(record=record, latitude=str(latitude),
                                                      longitude=str(longitude), company_id=company_id)
        staff      = await self.staff_repo.get_by_id(staff_id, company_id)
        staff_name = staff.name if staff else "Staff"
        formatted_time = format_time_for_message(record.check_in_time)

        if staff:
            await self.notif.send(
                company_id=company_id, user_id=staff.user_id,
                title="Check-out recorded",
                message=f"You checked out at {formatted_time}. See you tomorrow!",
                notif_type="success", reference_id=record.attendance_id, reference_type="attendance",
            )

        if _is_early(record.check_out_time, att_settings.office_close_time) and staff:
            await self.notif.send(
                company_id=company_id, user_id=staff.user_id,
                title="Early check-out",
                message=f"You left at {record.check_out_time}, before closing time {att_settings.office_close_time}.",
                notif_type="warning", reference_id=record.attendance_id, reference_type="attendance",
            )
            managers = await self.staff_repo.get_managers(company_id)
            for manager in managers:
                await self.notif.send(
                    company_id=company_id, user_id=manager.user_id,
                    title="Early check-out alert",
                    message=f"{staff_name} left early at {record.check_out_time}. Office closes at {att_settings.office_close_time}.",
                    notif_type="warning", reference_id=record.attendance_id, reference_type="attendance",
                )

        return {
            "attendance":      record,
            "distance_meters": round(distance, 1),
            "message":         f"Check-out successful! ({distance:.0f}m from office)",
        }

    # -----------------------------------------------------------------------
    # GET MY ATTENDANCE
    # -----------------------------------------------------------------------

    async def get_my_attendance(
        self,
        staff_id:   int,
        company_id: int,
        month:      Optional[int] = None,
        year:       Optional[int] = None,
    ) -> list:
        return await self.repo.get_by_staff_id(
            staff_id   = staff_id,
            company_id = company_id,
            month      = month,
            year       = year,
        )

    # -----------------------------------------------------------------------
    # GET ALL
    # -----------------------------------------------------------------------



    async def get_all_attendance(
        self,
        company_id:  int,
        filter_date: Optional[date] = None,
        month:       Optional[int]  = None,  # ← add
        year:        Optional[int]  = None,  # ← add
        staff_id:    Optional[int]  = None,  # ← add
    ) -> list:
        return await self.repo.get_all(
            company_id  = company_id,
            filter_date = filter_date,
            month       = month,     # ← add
            year        = year,      # ← add
            staff_id    = staff_id,  # ← add
        )
    
    # -----------------------------------------------------------------------
    # GET ONE
    # -----------------------------------------------------------------------

    async def get_by_id(self, attendance_id: int, company_id: int):
        record = await self.repo.get_by_id(attendance_id, company_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance record id={attendance_id} not found.",
            )
        return record

    # -----------------------------------------------------------------------
    # TODAY SUMMARY
    # -----------------------------------------------------------------------

    async def get_today_summary(self, company_id: int) -> dict:
        return await self.repo.get_today_summary(
            company_id = company_id,
            today      = date.today(),
        )

    # -----------------------------------------------------------------------
    # GET BY DATE RANGE
    # -----------------------------------------------------------------------

    async def get_by_date_range(
        self,
        company_id:  int,
        start_date:  date,
        end_date:    date,
        staff_id:    Optional[int] = None,
    ) -> list:
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before end_date.",
            )
        return await self.repo.get_by_date_range(
            company_id = company_id,
            start_date = start_date,
            end_date   = end_date,
            staff_id   = staff_id,
        )

    # -----------------------------------------------------------------------
    # MONTHLY STATS
    # -----------------------------------------------------------------------

    async def get_monthly_stats(
        self,
        staff_id:   int,
        company_id: int,
        month:      int,
        year:       int,
    ) -> dict:
        return await self.repo.get_monthly_stats(
            staff_id   = staff_id,
            company_id = company_id,
            month      = month,
            year       = year,
        )


# =============================================================================
# FACTORY
# =============================================================================




async def get_attendance_service(
    db:           AsyncSession = Depends(get_db),
    redis_client: redis.Redis  = Depends(get_redis_client),
) -> AttendanceService:
    return AttendanceService(
        db           = db,
        repo         = AttendanceRepository(db),
        staff_repo   = StaffRepository(db),
        settings_repo= AttendanceSettingsRepository(db),
        redis_client = redis_client,
    )