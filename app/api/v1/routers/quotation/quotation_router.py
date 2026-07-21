from fastapi import APIRouter, Depends, status, Query
from typing import Optional

from app.schemas.quotation_Schema import (
    QuotationCreate,
    QuotationUpdate,
    QuotationResponse,
    QuotationStaffGroupResponse,
    QuotationSummaryResponse,
    QuotationStatusUpdateRequest,
    QuotationItemCreate,
    QuotationItemUpdate,
    QuotationItemResponse,
)
from app.services.quotation.quotation_service import get_quotation_service, QuotationService
from app.dependencies import get_db
from app.utils.auth import require_staff, require_manager

quotation_router = APIRouter(prefix="/quotations", tags=["Quotations"])

# ===========================================================================
# STAFF — view own assigned quotations
# ===========================================================================

@quotation_router.get(
    "/my",
    response_model=list[QuotationResponse],
    summary="Staff: view my assigned quotations",
)
async def get_my_quotations(
    current_user: dict = Depends(require_staff),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.get_my_quotations(
        staff_id   = current_user["staff_id"],
        company_id = current_user["company_id"],
    )



# =================================================
# by staff
# =================================================

@quotation_router.get(
    "/staff/{staff_id}",
    response_model=list[QuotationResponse],
    summary="[Manager] Get all quotations of a staff",
)
async def get_quotations_by_staff(
    staff_id:     int,
    current_user: dict = Depends(require_manager),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.get_quotations_by_staff(
        staff_id   = staff_id,
        company_id = current_user["company_id"],
    )

# ===========================================================================
# MANAGER — Group quotations by staff + user
# ===========================================================================

@quotation_router.get(
    "/group/staff",
    response_model=list[QuotationStaffGroupResponse],
    summary="[Manager] Group quotations by staff",
)
async def group_quotations_by_staff(
    current_user: dict = Depends(require_manager),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.get_group_by_staff(
        company_id=current_user["company_id"]
    )

# ===========================================================================
# MANAGER — manage all quotations
# ===========================================================================

@quotation_router.get(
    "/",
    response_model=list[QuotationResponse],
    summary="[Manager] List all quotations",
)
async def get_all_quotations(
    staff_id:     Optional[int] = Query(None, description="Filter by staff"),
    customer_id:  Optional[int] = Query(None, description="Filter by customer"),
    quo_status:   Optional[str] = Query(None, description="draft | sent | accepted"),
    current_user: dict = Depends(require_manager),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.get_all(
        company_id  = current_user["company_id"],
        staff_id    = staff_id,
        status      = quo_status,
        customer_id = customer_id,
    )

# ==============================================================================
#
# ==============================================================================

@quotation_router.get(
    "/summary",
    response_model=QuotationSummaryResponse,
    summary="[Manager] Quotation summary stats",
)
async def get_summary(
    current_user: dict = Depends(require_manager),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.get_summary(
        company_id=current_user["company_id"]
    )

# ======================================================================
#
# ======================================================================

@quotation_router.get(
    "/{quotation_id}",
    response_model=QuotationResponse,
    summary="[Manager] Get quotation by id",
)
async def get_quotation(
    quotation_id: int,
    current_user: dict = Depends(require_manager),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.get_by_id(
        quotation_id = quotation_id,
        company_id   = current_user["company_id"],
    )

# ======================================================================
#
# ======================================================================

@quotation_router.post(
    "/",
    response_model=QuotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Manager] Create quotation",
)
async def create_quotation(
    data:         QuotationCreate,
    current_user: dict = Depends(require_manager),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.create(
        data       = data,
        company_id = current_user["company_id"],
        created_by = current_user["staff_id"],
    )

# ======================================================================
#
# ======================================================================

@quotation_router.patch(
    "/{quotation_id}",
    response_model=QuotationResponse,
    summary="[Manager] Update quotation",
)
async def update_quotation(
    quotation_id: int,
    data:         QuotationUpdate,
    current_user: dict = Depends(require_manager),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.update(
        quotation_id = quotation_id,
        data         = data,
        company_id   = current_user["company_id"],
    )

# ======================================================================
#
# ======================================================================

@quotation_router.patch(
    "/{quotation_id}/status",
    response_model=QuotationResponse,
    summary="[Manager] Update quotation status (send / accept)",
)
async def update_quotation_status(
    quotation_id: int,
    data:         QuotationStatusUpdateRequest,
    current_user: dict = Depends(require_manager),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.update_status(
        quotation_id = quotation_id,
        data         = data,
        company_id   = current_user["company_id"],
    )

# ======================================================================
#
# ======================================================================

@quotation_router.delete(
    "/{quotation_id}",
    summary="[Manager] Delete quotation (only if not accepted)",
)
async def delete_quotation(
    quotation_id: int,
    current_user: dict = Depends(require_manager),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.delete(
        quotation_id = quotation_id,
        company_id   = current_user["company_id"],
    )


# ===========================================================================
# ITEMS
# ===========================================================================

@quotation_router.get(
    "/{quotation_id}/items",
    response_model=list[QuotationItemResponse],
    summary="[Manager] Get items for a quotation",
)
async def get_items(
    quotation_id: int,
    current_user: dict = Depends(require_manager),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.get_items(
        quotation_id = quotation_id,
        company_id   = current_user["company_id"],
    )

# ======================================================================
#
# ======================================================================

@quotation_router.post(
    "/{quotation_id}/items",
    response_model=QuotationItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Manager] Add item to quotation — recalculates totals",
)
async def add_item(
    quotation_id: int,
    data:         QuotationItemCreate,
    current_user: dict = Depends(require_manager),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.add_item(
        quotation_id = quotation_id,
        data         = data,
        company_id   = current_user["company_id"],
    )

# ======================================================================
#
# ======================================================================

@quotation_router.patch(
    "/{quotation_id}/items/{item_id}",
    response_model=QuotationItemResponse,
    summary="[Manager] Update quotation item — recalculates totals",
)
async def update_item(
    quotation_id: int,
    item_id:      int,
    data:         QuotationItemUpdate,
    current_user: dict = Depends(require_manager),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.update_item(
        quotation_id = quotation_id,
        item_id      = item_id,
        data         = data,
        company_id   = current_user["company_id"],
    )

# ======================================================================
#
# ======================================================================

@quotation_router.delete(
    "/{quotation_id}/items/{item_id}",
    summary="[Manager] Delete quotation item — recalculates totals",
)
async def delete_item(
    quotation_id: int,
    item_id:      int,
    current_user: dict = Depends(require_manager),
    service:      QuotationService = Depends(get_quotation_service),
):
    return await service.delete_item(
        quotation_id = quotation_id,
        item_id      = item_id,
        company_id   = current_user["company_id"],
    )