from sqlalchemy import Integer, String, Numeric, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.db.base import Base
if TYPE_CHECKING:
    from .product import Product
    from .product_image import ProductImage
    from .stock_movement import StockMovement
    from ..invoices.invoice_item import InvoiceItem
    from ..supplier.supplier_product_price import SupplierProductPrice





class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("product_id", "sku", name="uq_variant_product_sku"),)

    variant_id:     Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)


    product_id:     Mapped[int]           = mapped_column(Integer, ForeignKey("products.product_id"), nullable=False, index=True)
    sku:            Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    specs:          Mapped[dict]          = mapped_column(JSONB, nullable=False, default=dict)
    price:          Mapped[float]         = mapped_column(Numeric(12, 2), nullable=False)
    stock_quantity: Mapped[int]           = mapped_column(Integer, default=0, nullable=False)
    created_at:     Mapped[datetime]      = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at:     Mapped[datetime]      = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    product:          Mapped["Product"]                     = relationship("Product", back_populates="variants")
    images:           Mapped[list["ProductImage"]]          = relationship("ProductImage", back_populates="variant", cascade="all, delete-orphan")
    stock_movements:  Mapped[list["StockMovement"]]         = relationship("StockMovement", back_populates="variant", cascade="all, delete-orphan", passive_deletes=True)
    invoice_items:    Mapped[list["InvoiceItem"]]           = relationship("InvoiceItem", back_populates="variant")
    supplier_prices:  Mapped[list["SupplierProductPrice"]]  = relationship("SupplierProductPrice", back_populates="variant", cascade="all, delete-orphan", passive_deletes=True)