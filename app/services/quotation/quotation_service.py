from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
import redis.asyncio as redis

from app.repositories.inventory.inventory_repository import CustomerRepository
from app.repositories.quotation.quotation_repository import QuotationRepository
from app.repositories.hr.staff_repository import StaffRepository
from app.repositories.communication.notifications_repository import NotificationRepository
from app.services.communication.notifications_service import NotificationService
from app.schemas.quotation_Schema import (
    QuotationCreate,
    QuotationUpdate,
    QuotationItemCreate,
    QuotationItemUpdate,
    QuotationStatusUpdateRequest,
)
from app.dependencies import get_db, get_redis_client


class QuotationService:

    def __init__(
        self,
        db:           AsyncSession,
        redis_client: redis.Redis,
    ):
        self.repo       = QuotationRepository(db)
        self.staff_repo = StaffRepository(db)           # ✅ to get staff.user_id
        self.customer_repo = CustomerRepository(db)
        self.notif      = NotificationService(          # ✅ for real-time push
            db           = db,
            redis_client = redis_client,
        )

    # -----------------------------------------------------------------------
    # Calculate totals
    # -----------------------------------------------------------------------

    def _calc_total(
        self,
        subtotal: Decimal,
        discount: Decimal,
        tax:      Decimal,
    ) -> Decimal:
        return subtotal - discount + tax

    async def _recalc_quotation_totals(self, quotation_id: int, company_id: int):
        items     = await self.repo.get_items(quotation_id, company_id)
        subtotal  = sum((item.total_price for item in items), Decimal("0"))
        quotation = await self.repo.get_by_id(quotation_id, company_id)
        total     = self._calc_total(subtotal, quotation.discount, quotation.tax)

        return await self.repo.update(quotation, {
            "subtotal":     subtotal,
            "total_amount": total,
        })

    # -----------------------------------------------------------------------
    # GET all quotations (manager)
    # -----------------------------------------------------------------------

    async def get_all(
        self,
        company_id:  int,
        staff_id:    int | None = None,
        status:      str | None = None,
        customer_id: int | None = None,
    ) -> list:
        return await self.repo.get_all(
            company_id  = company_id,
            staff_id    = staff_id,
            status      = status,
            customer_id = customer_id,
        )






    async def get_group_by_staff(self, company_id: int):
        return await self.repo.get_group_by_staff(company_id)

    # -----------------------------------------------------------------------
    # GET quotations by staff (manager)
    # -----------------------------------------------------------------------
    async def get_quotations_by_staff(self, staff_id: int, company_id: int) -> list:
        quotations = await self.repo.get_quotations_by_staff(staff_id, company_id)

        if not quotations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No quotations found for staff id={staff_id}",
            )

        return quotations

    # -----------------------------------------------------------------------
    # GET my quotations (staff views own)
    # -----------------------------------------------------------------------

    async def get_my_quotations(self, staff_id: int, company_id: int) -> list:
        return await self.repo.get_my_quotations(staff_id, company_id)



    # -----------------------------------------------------------------------
    # GET one quotation
    # -----------------------------------------------------------------------

    async def get_by_id(self, quotation_id: int, company_id: int):
        quotation = await self.repo.get_by_id(quotation_id, company_id)
        if not quotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quotation id={quotation_id} not found.",
            )
        return quotation


     # -----------------------------------------------------------------------
    # CREATE quotation — notify assigned staff
    # -----------------------------------------------------------------------

    async def create(self, data: QuotationCreate, company_id: int, created_by: int):
        items_data = data.items or []
        subtotal   = sum((item.quantity * item.unit_price for item in items_data), Decimal("0"))
        total      = self._calc_total(subtotal, data.discount, data.tax)

        quotation = await self.repo.create({
            "company_id":       company_id,
            "customer_id":      data.customer_id,
            "staff_id":         data.staff_id,
            "ref_number":       data.ref_number,
            "quotation_date":   data.quotation_date,
            "expiry_date":      data.expiry_date,
            "production_days":  data.production_days,
            "artwork_status":   data.artwork_status,
            "payment_terms":    data.payment_terms,
            "delivery_method":  data.delivery_method,
            "subtotal":         subtotal,
            "discount":         data.discount,
            "tax":              data.tax,
            "total_amount":     total,
            "note":             data.note,
            "created_by":       created_by,
        })

        for item in items_data:
            created_item = await self.repo.create_item({
                "company_id":   company_id,
                "quotation_id": quotation.quotation_id,
                "sort_order":   item.sort_order,
                "item_name":    item.item_name,
                "size":         item.size,
                "pages":        item.pages,
                "print_side":   item.print_side,
                "color_spec":   item.color_spec,
                "paper_cover":  item.paper_cover,
                "paper_inside": item.paper_inside,
                "finishing":    item.finishing,
                "language":     item.language,
                "quantity":     item.quantity,
                "unit_price":   item.unit_price,
                "total_price":  item.quantity * item.unit_price,
                "note":         item.note,
            })

            # ── price tiers: optional alternative quantity/price options ──
            if item.price_tiers:
                await self.repo.replace_price_tiers(
                    created_item.item_id,
                    [
                        {
                            "quantity":    t.quantity,
                            "unit_price":  t.unit_price,
                            "total_price": t.quantity * t.unit_price,
                            "sort_order":  t.sort_order,
                        }
                        for t in item.price_tiers
                    ],
                )

        # ✅ notify assigned staff — quotation created
        if quotation.staff_id:
            staff = await self.staff_repo.get_by_id(quotation.staff_id, company_id)
            if staff:
                await self.notif.send(
                    company_id     = company_id,
                    user_id        = staff.user_id,
                    title          = "New quotation assigned",
                    message        = (
                        f"Quotation {quotation.ref_number} has been assigned to you. "
                        f"Total amount: {total}."
                    ),
                    notif_type     = "info",
                    reference_id   = quotation.quotation_id,
                    reference_type = "quotation",
                )

        return await self.get_by_id(quotation.quotation_id, company_id)
    # -----------------------------------------------------------------------
    # UPDATE quotation
    # -----------------------------------------------------------------------

    async def update(
        self, quotation_id: int, data: QuotationUpdate, company_id: int
    ):
        quotation   = await self.get_by_id(quotation_id, company_id)

        if quotation.invoice_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit a quotation that has already been converted to an invoice.",
            )



        update_data = data.model_dump(exclude_none=True)

        if "customer_id" in update_data:
            customer = await self.customer_repo.get_by_id(
                update_data["customer_id"], company_id
            )
            if not customer:
                raise HTTPException(
                    status_code=404,
                    detail=f"Customer {update_data['customer_id']} not found",
                )
        discount = update_data.get("discount", quotation.discount)
        tax      = update_data.get("tax",      quotation.tax)
        subtotal = update_data.get("subtotal", quotation.subtotal)
        update_data["total_amount"] = self._calc_total(subtotal, discount, tax)

        return await self.repo.update(quotation, update_data)




    # -----------------------------------------------------------------------
    # UPDATE status — notify staff on send / accept
    # -----------------------------------------------------------------------

    async def update_status(
        self, quotation_id: int, data: QuotationStatusUpdateRequest, company_id: int
    ):
        quotation = await self.get_by_id(quotation_id, company_id)

        if quotation.status == data.status:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Quotation is already '{data.status}'.",
            )

        updated = await self.repo.update(quotation, {
            "status": data.status,
            "note":   data.note if data.note else quotation.note,
        })

        # ✅ notify assigned staff — status changed
        if updated.staff_id:
            staff = await self.staff_repo.get_by_id(updated.staff_id, company_id)
            if staff:
                await self.notif.send(
                    company_id     = company_id,
                    user_id        = staff.user_id,
                    title          = f"Quotation {data.status}",
                    message        = f"Quotation {updated.ref_number} has been marked as {data.status}.",
                    notif_type     = "success" if data.status == "accepted" else "info",
                    reference_id   = quotation_id,
                    reference_type = "quotation",
                )

        return updated

    # -----------------------------------------------------------------------
    # DELETE quotation
    # -----------------------------------------------------------------------

    async def delete(self, quotation_id: int, company_id: int) -> dict:
        quotation = await self.get_by_id(quotation_id, company_id)
        if quotation.status == "accepted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete an accepted quotation.",
            )

        if quotation.invoice_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a quotation that has already been converted to an invoice.",
            )
        await self.repo.delete(quotation)
        return {"message": f"Quotation id={quotation_id} deleted."}

    # -----------------------------------------------------------------------
    # GET summary
    # -----------------------------------------------------------------------

    async def get_summary(self, company_id: int) -> dict:
        return await self.repo.get_summary(company_id)

    # -----------------------------------------------------------------------
    # GET items
    # -----------------------------------------------------------------------

    async def get_items(self, quotation_id: int, company_id: int) -> list:
        await self.get_by_id(quotation_id, company_id)
        return await self.repo.get_items(quotation_id, company_id)

    # -----------------------------------------------------------------------
    # ADD item — recalculates quotation totals
    # -----------------------------------------------------------------------


    async def add_item(
        self, quotation_id: int, data: QuotationItemCreate, company_id: int
    ):
        quotation = await self.get_by_id(quotation_id, company_id)

        if quotation.invoice_id is not None:
           raise HTTPException(400, "Cannot modify items on a converted quotation.")

        item = await self.repo.create_item({
            "company_id":   company_id,
            "quotation_id": quotation_id,
            "sort_order":   data.sort_order,
            "item_name":    data.item_name,
            "size":         data.size,
            "pages":        data.pages,
            "print_side":   data.print_side,
            "color_spec":   data.color_spec,
            "paper_cover":  data.paper_cover,
            "paper_inside": data.paper_inside,
            "finishing":    data.finishing,
            "language":     data.language,
            "quantity":     data.quantity,
            "unit_price":   data.unit_price,
            "total_price":  data.quantity * data.unit_price,
            "note":         data.note,
        })

        # ── price tiers: optional alternative quantity/price options ──────
        if data.price_tiers:
            await self.repo.replace_price_tiers(
                item.item_id,
                [
                    {
                        "quantity":    t.quantity,
                        "unit_price":  t.unit_price,
                        "total_price": t.quantity * t.unit_price,
                        "sort_order":  t.sort_order,
                    }
                    for t in data.price_tiers
                ],
            )

        await self._recalc_quotation_totals(quotation_id, company_id)
        return await self.repo.get_item_by_id(item.item_id, company_id)

    
    # -----------------------------------------------------------------------
    # UPDATE item — recalculates quotation totals
    # -----------------------------------------------------------------------

    async def update_item(
        self, quotation_id: int, item_id: int, data: QuotationItemUpdate, company_id: int
    ):
        await self.get_by_id(quotation_id, company_id)

        item = await self.repo.get_item_by_id(item_id, company_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quotation item id={item_id} not found.",
            )
        update_data = data.model_dump(exclude_none=True, exclude={"price_tiers"})   # ← exclude here

        quantity   = update_data.get("quantity",   item.quantity)
        unit_price = update_data.get("unit_price", item.unit_price)
        update_data["total_price"] = quantity * unit_price

        updated = await self.repo.update_item(item, update_data)

        # ── price tiers: replace-all if provided ──────────────────────────
        if data.price_tiers is not None:
            await self.repo.replace_price_tiers(
                item_id,
                [
                    {
                        "quantity":    t.quantity,
                        "unit_price":  t.unit_price,
                        "total_price": t.quantity * t.unit_price,
                        "sort_order":  t.sort_order,
                    }
                    for t in data.price_tiers
                ],
            )

        await self._recalc_quotation_totals(quotation_id, company_id)
        return await self.repo.get_item_by_id(item_id, company_id)

        

    # -----------------------------------------------------------------------
    # DELETE item — recalculates quotation totals
    # -----------------------------------------------------------------------

    async def delete_item(self, quotation_id: int, item_id: int, company_id: int) -> dict:
        await self.get_by_id(quotation_id, company_id)

        item = await self.repo.get_item_by_id(item_id, company_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quotation item id={item_id} not found.",
            )

        await self.repo.delete_item(item)
        await self._recalc_quotation_totals(quotation_id, company_id)
        return {"message": f"Quotation item id={item_id} deleted."}


# =============================================================================
# FACTORY
# =============================================================================

async def get_quotation_service(
    db:           AsyncSession = Depends(get_db),
    redis_client: redis.Redis  = Depends(get_redis_client),
) -> QuotationService:
    return QuotationService(
        db           = db,
        redis_client = redis_client,
    )