from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from .quotation_item import QuotationItem


class QuotationItemPriceTier(Base):
    __tablename__ = "quotation_item_price_tiers"

    tier_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quotation_items.item_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    item: Mapped["QuotationItem"] = relationship(
        "QuotationItem", back_populates="price_tiers"
    )