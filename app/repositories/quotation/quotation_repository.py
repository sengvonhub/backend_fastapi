from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from decimal import Decimal

from app.models.quotations.quotation import Quotation
from app.models.quotations.quotation_item import QuotationItem
from app.models.staffs.staff import Staff
from app.models.users.user import User


class QuotationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # Quotation queries
    # -----------------------------------------------------------------------

    async def get_all(
        self,
        company_id:  int,
        staff_id:    int | None = None,
        status:      str | None = None,
        customer_id: int | None = None,
    ) -> list[Quotation]:
        query = (
            select(Quotation)
            .where(Quotation.company_id == company_id)
            .options(
                selectinload(Quotation.items),
                selectinload(Quotation.customer),
            )
            .order_by(Quotation.created_at.desc())
        )
        if staff_id:
            query = query.where(Quotation.staff_id == staff_id)
        if status:
            query = query.where(Quotation.status == status)
        if customer_id:
            query = query.where(Quotation.customer_id == customer_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    # -----------------------------------------------------------------------
    # GET quotations by staff id
    # -----------------------------------------------------------------------
    async def get_quotations_by_staff(
        self, staff_id: int, company_id: int
    ) -> list[Quotation]:
        result = await self.db.execute(
            select(Quotation)
            .where(
                Quotation.staff_id   == staff_id,
                Quotation.company_id == company_id,
            )
            .options(
                selectinload(Quotation.items),
                selectinload(Quotation.customer),  
            )
            .order_by(Quotation.quotation_date.desc())
        )
        return result.scalars().all()

    # -----------------------------------------------------------------------
    # GROUP quotations by staff + user
    # -----------------------------------------------------------------------
    async def get_group_by_staff(self, company_id: int):
        result = await self.db.execute(
            select(Quotation, Staff, User)
            .join(Staff, Quotation.staff_id == Staff.staff_id)
            .join(User, Staff.user_id == User.user_id)
            .where(Quotation.company_id == company_id)
            .options(selectinload(Quotation.items))
            .order_by(Staff.staff_id, Quotation.quotation_date.desc())
        )
        rows = result.all()
        grouped = {}
        for quotation, staff, user in rows:
            sid = staff.staff_id

            if sid not in grouped:
                grouped[sid] = {
                    "staff_id":   staff.staff_id,
                    "user_id":    user.user_id,
                    "username":   user.username,
                    "full_name":  user.full_name,
                    "quotations": [],
                }

            grouped[sid]["quotations"].append(quotation)
        return list(grouped.values())

    async def get_by_id(
        self, quotation_id: int, company_id: int
    ) -> Quotation | None:
        result = await self.db.execute(
        select(Quotation)
        .where(
            Quotation.quotation_id == quotation_id,
            Quotation.company_id   == company_id,
        )
        .options(
            selectinload(Quotation.items),
            selectinload(Quotation.customer),
        )
        )
        return result.scalar_one_or_none()



    async def get_my_quotations(
        self, staff_id: int, company_id: int
    ) -> list[Quotation]:
        result = await self.db.execute(
            select(Quotation)
            .where(
                Quotation.staff_id   == staff_id,
                Quotation.company_id == company_id,
            )
            .options(
                selectinload(Quotation.items),
                selectinload(Quotation.customer),   
            )
            .order_by(Quotation.quotation_date.desc())
        )
        return result.scalars().all()





    async def create(self, data: dict) -> Quotation:
        quotation = Quotation(**data)
        self.db.add(quotation)
        await self.db.commit()
        await self.db.refresh(quotation)
        return quotation

    async def update(self, quotation: Quotation, data: dict) -> Quotation:
        for key, value in data.items():
            if value is not None:
                setattr(quotation, key, value)
        await self.db.commit()
        await self.db.refresh(quotation)
        return quotation

    async def delete(self, quotation: Quotation) -> None:
        await self.db.delete(quotation)
        await self.db.commit()

    async def get_summary(self, company_id: int) -> dict:
        total = await self.db.execute(
            select(func.count()).select_from(Quotation)
            .where(Quotation.company_id == company_id)
        )
        draft = await self.db.execute(
            select(func.count()).select_from(Quotation)
            .where(
                Quotation.company_id == company_id,
                Quotation.status     == "draft",
            )
        )
        sent = await self.db.execute(
            select(func.count()).select_from(Quotation)
            .where(
                Quotation.company_id == company_id,
                Quotation.status     == "sent",
            )
        )
        accepted = await self.db.execute(
            select(func.count()).select_from(Quotation)
            .where(
                Quotation.company_id == company_id,
                Quotation.status     == "accepted",
            )
        )
        total_amount = await self.db.execute(
            select(func.sum(Quotation.total_amount))
            .where(Quotation.company_id == company_id)
        )
        return {
            "total_quotations": total.scalar()       or 0,
            "total_draft":      draft.scalar()        or 0,
            "total_sent":       sent.scalar()         or 0,
            "total_accepted":   accepted.scalar()     or 0,
            "total_amount":     total_amount.scalar() or Decimal("0"),
        }

    # -----------------------------------------------------------------------
    # Item queries
    # -----------------------------------------------------------------------

    async def get_items(
        self, quotation_id: int, company_id: int
    ) -> list[QuotationItem]:
        result = await self.db.execute(
            select(QuotationItem)
            .where(
                QuotationItem.quotation_id == quotation_id,
                QuotationItem.company_id   == company_id,
            )
            .order_by(QuotationItem.sort_order.asc())
        )
        return result.scalars().all()

    async def get_item_by_id(
        self, item_id: int, company_id: int
    ) -> QuotationItem | None:
        result = await self.db.execute(
            select(QuotationItem).where(
                QuotationItem.item_id    == item_id,
                QuotationItem.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_item(self, data: dict) -> QuotationItem:
        item = QuotationItem(**data)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update_item(self, item: QuotationItem, data: dict) -> QuotationItem:
        for key, value in data.items():
            if value is not None:
                setattr(item, key, value)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete_item(self, item: QuotationItem) -> None:
        await self.db.delete(item)
        await self.db.commit()