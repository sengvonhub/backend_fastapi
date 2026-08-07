import enum
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, String, Text, Date, DateTime, Numeric, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base import Base

if TYPE_CHECKING:
    from ..customer import Customer
    from ..staffs import Staff
    from ..company import Company
    from ..invoices.invoice import Invoice
    from .quotation_item import QuotationItem


class QuotationStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    accepted = "accepted"


class ArtworkStatus(str, enum.Enum):
    not_provided = "not_provided"
    approved = "approved"
    needs_revision = "needs_revision"


class DeliveryMethod(str, enum.Enum):
    pickup = "pickup"
    delivery = "delivery"


class Quotation(Base):
    __tablename__ = "quotations"

    quotation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("customers.customer_id"), nullable=True, index=True)
    staff_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("staff.staff_id", ondelete="SET NULL"), nullable=True, index=True)

    ref_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    quotation_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    status: Mapped[QuotationStatus] = mapped_column(
        SAEnum(QuotationStatus, name="quotation_status"), nullable=False, default=QuotationStatus.draft
    )

    production_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    artwork_status: Mapped[Optional[ArtworkStatus]] = mapped_column(
        SAEnum(ArtworkStatus, name="artwork_status"), nullable=True, default=ArtworkStatus.not_provided
    )

    payment_terms: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    delivery_method: Mapped[Optional[DeliveryMethod]] = mapped_column(
        SAEnum(DeliveryMethod, name="delivery_method"), nullable=True
    )

    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    discount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    invoice_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("invoices.invoice_id"), nullable=True, index=True)

    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("staff.staff_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)





    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="quotations")
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="quotations")


    staff: Mapped[Optional["Staff"]] = relationship("Staff", foreign_keys=[staff_id], back_populates="quotations")
    creator: Mapped[Optional["Staff"]] = relationship("Staff", foreign_keys=[created_by])
    

    invoices: Mapped[Optional["Invoice"]] = relationship("Invoice", back_populates="quotations")
    items: Mapped[list["QuotationItem"]] = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")