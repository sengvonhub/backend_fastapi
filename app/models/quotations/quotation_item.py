from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from ..company import Company
    from .quotation import Quotation
    from .quotation_item_price_tier import QuotationItemPriceTier


class QuotationItem(Base):
    __tablename__ = "quotation_items"

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    quotation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("quotations.quotation_id", ondelete="CASCADE"), nullable=True, index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    print_side: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    color_spec: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    paper_cover: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    paper_inside: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    finishing: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="quotation_items")
    quotation: Mapped[Optional["Quotation"]] = relationship("Quotation", back_populates="items")
    price_tiers: Mapped[list["QuotationItemPriceTier"]] = relationship(
        "QuotationItemPriceTier",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="QuotationItemPriceTier.sort_order",
    )