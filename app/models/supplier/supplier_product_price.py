from sqlalchemy import Integer, Numeric, ForeignKey, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.db.base import Base

if TYPE_CHECKING:
    from .supplier import Supplier
    from ..products.product_variant import ProductVariant


class SupplierProductPrice(Base):
    __tablename__ = "supplier_product_prices"
    __table_args__ = (
        UniqueConstraint("supplier_id", "variant_id", name="uq_supplier_variant"),
    )

    price_id:    Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int]           = mapped_column(Integer, ForeignKey("suppliers.supplier_id"), nullable=False, index=True)
    variant_id:  Mapped[int]           = mapped_column(Integer, ForeignKey("product_variants.variant_id", ondelete='CASCADE'), nullable=False, index=True)
    unit_price:  Mapped[float]         = mapped_column(Numeric(12, 2), nullable=False)
    note:        Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at:  Mapped[datetime]      = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at:  Mapped[datetime]      = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    supplier: Mapped["Supplier"]       = relationship("Supplier", back_populates="product_prices")
    variant:  Mapped["ProductVariant"] = relationship("ProductVariant", back_populates="supplier_prices")