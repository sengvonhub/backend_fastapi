import calendar
from datetime import date
from io import BytesIO

from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
import redis.asyncio as redis

from app.repositories.hr.salaries_repository import SalaryRepository
from app.repositories.hr.staff_repository import StaffRepository
from app.repositories.communication.notifications_repository import NotificationRepository
from app.services.communication.notifications_service import NotificationService
from app.schemas.schema import (
    SalaryCreate,
    SalaryUpdate,
    SalaryAdjustmentCreate,
    MarkPaidRequest,
)
from app.dependencies import get_db, get_redis_client
from reportlab.lib.pagesizes import letter

from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet








class SalaryService:

    def __init__(
        self,
        db:           AsyncSession,
        redis_client: redis.Redis,
    ):
        self.repo       = SalaryRepository(db)
        self.staff_repo = StaffRepository(db)         
        self.notif      = NotificationService(   
            db           = db,
            redis_client = redis_client,
        )

    # -----------------------------------------------------------------------
    # Calculate net salary
    # -----------------------------------------------------------------------

    def _calc_net(
        self,
        base:       Decimal,
        bonus:      Decimal,
        deductions: Decimal,
    ) -> Decimal:
        return base + bonus - deductions

    # -----------------------------------------------------------------------
    # GET all salaries (manager)
    # -----------------------------------------------------------------------

    async def get_all(
        self,
        company_id: int,
        staff_id:   int | None = None,
        status:     str | None = None,
    ) -> list:
        return await self.repo.get_all(
            company_id = company_id,
            staff_id   = staff_id,
            status     = status,
        )
    
    async def get_group_by_staff(self, company_id: int):
        return await self.repo.get_group_by_staff(company_id)
    
    # -----------------------------------------------------------------------
    # GET salaries by staff (manager)
    # -----------------------------------------------------------------------
    async def get_salaries_by_staff(self, staff_id: int, company_id: int) -> list:
        salaries = await self.repo.get_salaries_by_staff(staff_id, company_id)

        if not salaries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No salaries found for staff id={staff_id}",
            )

        return salaries

        # -----------------------------------------------------------------------
    # GET my salaries (staff views own)
    # -----------------------------------------------------------------------

    async def get_my_salaries(self, staff_id: int, company_id: int) -> list:
        return await self.repo.get_my_salaries(staff_id, company_id)


    # -----------------------------------------------------------------------
    # GET one salary
    # -----------------------------------------------------------------------

    async def get_by_id(self, salary_id: int, company_id: int):
        salary = await self.repo.get_by_id(salary_id, company_id)
        if not salary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Salary id={salary_id} not found.",
            )
        return salary


    # -----------------------------------------------------------------------
    # CREATE salary — notify staff
    # -----------------------------------------------------------------------

    async def create(self, data: SalaryCreate, company_id: int):
        net    = self._calc_net(data.base_salary, data.bonus, data.deductions)
        salary = await self.repo.create({
            "company_id":       company_id,
            "staff_id":         data.staff_id,
            "managed_by":       data.managed_by,
            "base_salary":      data.base_salary,
            "bonus":            data.bonus,
            "deductions":       data.deductions,
            "net_salary":       net,
            "pay_period_start": data.pay_period_start,
            "pay_period_end":   data.pay_period_end,
            "payment_status":   data.payment_status,
            "payment_date":     data.payment_date,
        })

        # ✅ notify staff — salary record created
        staff = await self.staff_repo.get_by_id(data.staff_id, company_id)
        if staff:
            await self.notif.send(
                company_id     = company_id,
                user_id        = staff.user_id,
                title          = "Salary record created",
                message        = (
                    f"Your salary record for {data.pay_period_start} to "
                    f"{data.pay_period_end} has been created. "
                    f"Net salary: {net}."
                ),
                notif_type     = "info",
                reference_id   = salary.salary_id,
                reference_type = "salary",
            )

        return salary






    # -----------------------------------------------------------------------
    # UPDATE salary
    # -----------------------------------------------------------------------

    async def update(
        self, salary_id: int, data: SalaryUpdate, company_id: int
    ):
        salary      = await self.get_by_id(salary_id, company_id)
        update_data = data.model_dump(exclude_none=True)

        base       = update_data.get("base_salary",  salary.base_salary)
        bonus      = update_data.get("bonus",        salary.bonus)
        deductions = update_data.get("deductions",   salary.deductions)
        update_data["net_salary"] = self._calc_net(base, bonus, deductions)

        return await self.repo.update(salary, update_data)

    # -----------------------------------------------------------------------
    # MARK as paid — notify staff
    # -----------------------------------------------------------------------

    async def mark_paid(
        self, salary_id: int, data: MarkPaidRequest, company_id: int
    ):
        salary = await self.get_by_id(salary_id, company_id)

        if salary.payment_status == "paid":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Salary is already marked as paid.",
            )

        updated = await self.repo.update(salary, {
            "payment_status": "paid",
            "payment_date":   data.payment_date,
        })

        # ✅ notify staff — salary paid
        staff = await self.staff_repo.get_by_id(salary.staff_id, company_id)
        if staff:
            await self.notif.send(
                company_id     = company_id,
                user_id        = staff.user_id,
                title          = "Salary paid",
                message        = (
                    f"Your salary of {salary.net_salary} for "
                    f"{salary.pay_period_start} to {salary.pay_period_end} "
                    f"has been paid on {data.payment_date}."
                ),
                notif_type     = "success",
                reference_id   = salary_id,
                reference_type = "salary",
            )

        return updated

    # -----------------------------------------------------------------------
    # DELETE salary
    # -----------------------------------------------------------------------

    async def delete(self, salary_id: int, company_id: int) -> dict:
        salary = await self.get_by_id(salary_id, company_id)
        if salary.payment_status == "paid":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a paid salary record.",
            )
        await self.repo.delete(salary)
        return {"message": f"Salary id={salary_id} deleted."}




    # -----------------------------------------------------------------------
    # GET summary
    # -----------------------------------------------------------------------

    async def get_summary(self, company_id: int) -> dict:
        return await self.repo.get_summary(company_id)

    # -----------------------------------------------------------------------
    # GET adjustments
    # -----------------------------------------------------------------------



    async def get_adjustments(
        self, salary_id: int, company_id: int
    ) -> list:
        await self.get_by_id(salary_id, company_id)
        return await self.repo.get_adjustments(salary_id, company_id)

    # -----------------------------------------------------------------------
    # CREATE adjustment — notify staff bonus or deduction
    # -----------------------------------------------------------------------

    async def create_adjustment(
        self,
        data:             SalaryAdjustmentCreate,
        company_id:       int,
        manager_staff_id: int,
    ):
        salary = await self.get_by_id(data.salary_id, company_id)
        adjustment = await self.repo.create_adjustment({
            "company_id":      company_id,
            "salary_id":       data.salary_id,
            "adjusted_by":     manager_staff_id,
            "adjustment_type": data.adjustment_type,
            "amount":          data.amount,
            "reason":          data.reason,
        })

        # Recalculate net salary
        if data.adjustment_type == "bonus":
            new_bonus = salary.bonus + data.amount
            await self.repo.update(salary, {
                "bonus":      new_bonus,
                "net_salary": self._calc_net(
                    salary.base_salary, new_bonus, salary.deductions
                ),
            })
        else:
            new_deductions = salary.deductions + data.amount
            await self.repo.update(salary, {
                "deductions": new_deductions,
                "net_salary": self._calc_net(
                    salary.base_salary, salary.bonus, new_deductions
                ),
            })

        # ✅ notify staff — bonus or deduction applied
        staff = await self.staff_repo.get_by_id(salary.staff_id, company_id)
        if staff:
            if data.adjustment_type == "bonus":
                await self.notif.send(
                    company_id     = company_id,
                    user_id        = staff.user_id,
                    title          = "Bonus added",
                    message        = (
                        f"A bonus of {data.amount} has been added to your salary. "
                        f"Reason: {data.reason or 'No reason provided'}."
                    ),
                    notif_type     = "success",
                    reference_id   = adjustment.adjustment_id,
                    reference_type = "salary_adjustment",
                )
            else:
                await self.notif.send(
                    company_id     = company_id,
                    user_id        = staff.user_id,
                    title          = "Deduction applied",
                    message        = (
                        f"A deduction of {data.amount} has been applied to your salary. "
                        f"Reason: {data.reason or 'No reason provided'}."
                    ),
                    notif_type     = "warning",
                    reference_id   = adjustment.adjustment_id,
                    reference_type = "salary_adjustment",
                )

        return adjustment


    async def generate_monthly_report(
        self, company_id: int, year: int, month: int
        ) -> bytes:
        if not (1 <= month <= 12):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="month must be between 1 and 12.",
            )

        start = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end = date(year, month, last_day)

        rows = await self.repo.get_by_period(company_id, start, end)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = [
            Paragraph(f"Payroll Report — {start.strftime('%B %Y')}", styles["Title"]),
            Spacer(1, 12),
        ]

        table_data = [["Staff", "Period", "Base", "Bonus", "Deductions", "Net", "Status"]]
        total_net = Decimal("0")
        for salary, staff, user in rows:
            table_data.append([
                user.full_name,
                f"{salary.pay_period_start} – {salary.pay_period_end}",
                f"{salary.base_salary:,.2f}",
                f"{salary.bonus:,.2f}",
                f"{salary.deductions:,.2f}",
                f"{salary.net_salary:,.2f}",
                salary.payment_status.value,
            ])
            total_net += salary.net_salary

        if len(table_data) == 1:
            elements.append(Paragraph("No salary records found for this period.", styles["Normal"]))
        else:
            table_data.append(["", "", "", "", "Total:", f"{total_net:,.2f}", ""])
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ]))
            elements.append(table)

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes



    
    
    




    # -----------------------------------------------------------------------
    # DELETE adjustment — notify staff reversal
    # -----------------------------------------------------------------------

    async def delete_adjustment(
        self, adjustment_id: int, company_id: int
    ) -> dict:
        adjustment = await self.repo.get_adjustment_by_id(
            adjustment_id, company_id
        )
        if not adjustment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Adjustment id={adjustment_id} not found.",
            )

        # ✅ notify staff — adjustment removed
        salary = await self.repo.get_by_id(adjustment.salary_id, company_id)
        if salary:
            staff = await self.staff_repo.get_by_id(salary.staff_id, company_id)
            if staff:
                await self.notif.send(
                    company_id     = company_id,
                    user_id        = staff.user_id,
                    title          = "Salary adjustment removed",
                    message        = (
                        f"A {adjustment.adjustment_type} of {adjustment.amount} "
                        f"has been removed from your salary record."
                    ),
                    notif_type     = "info",
                    reference_id   = adjustment_id,
                    reference_type = "salary_adjustment",
                )

        await self.repo.delete_adjustment(adjustment)
        return {"message": f"Adjustment id={adjustment_id} deleted."}


# =============================================================================
# FACTORY
# =============================================================================

async def get_salary_service(
    db:           AsyncSession = Depends(get_db),
    redis_client: redis.Redis  = Depends(get_redis_client),  # ✅ inject redis
) -> SalaryService:
    return SalaryService(
        db           = db,
        redis_client = redis_client,
    )