from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.attendance_settings import (
    AttendanceSettingsResponse,
    AttendanceSettingsUpdate,
)
from fastapi import HTTPException
from app.models.staffs.attendance_settings import AttendanceSettings
from app.services.hr.attendance_setting_service import get_attendance_setting_service, AttendanceSettingService
from app.utils.auth import require_login, require_manager
attendance_settings_router = APIRouter(prefix="/attendance-settings", tags=["Attendance Settings"])

# ============================================================================
# get attendance settings
# ============================================================================



@attendance_settings_router.get(
    "/",
    response_model=AttendanceSettingsResponse,
    summary="Get attendance settings for the company of the manager",
)
async def get_attendance_settings(
    current_user: dict = Depends(require_manager),
    service: AttendanceSettingService = Depends(get_attendance_setting_service),
) -> AttendanceSettingsResponse:
    settings = await service.get_settings(
        company_id=current_user["company_id"],
    )
    if settings is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance settings not found",
        )
    return settings


# ============================================================================
# MANAGER — manage attendance settings
# ============================================================================

@attendance_settings_router.patch(
    "/",
    response_model=AttendanceSettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Manager: update attendance settings",
)
async def update_attendance_settings(
    data: AttendanceSettingsUpdate,
    current_user: dict = Depends(require_manager),
    service: AttendanceSettingService = Depends(get_attendance_setting_service),
):
    update_data = data.model_dump(exclude_unset=True)
    return await service.upsert_settings(
        company_id=current_user["company_id"],
        **update_data
    )