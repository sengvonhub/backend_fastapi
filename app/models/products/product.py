from sqlalchemy import Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.db.base import Base

if TYPE_CHECKING:
    from ..category import Category
    from ..invoices.invoice_item import InvoiceItem
    from ..company import Company
    from .product_image import ProductImage
    from .product_variant import ProductVariant

class Product(Base):
    __tablename__ = "products"
    product_id:   Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id:   Mapped[int]           = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    category_id:  Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.category_id"), nullable=True)
    name:         Mapped[str]           = mapped_column(String(200), nullable=False)
    descriptions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at:   Mapped[datetime]      = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at:   Mapped[datetime]      = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # price, stock_quantity, unit, length_width → moved to ProductVariant

    company:   Mapped["Company"]               = relationship("Company", back_populates="products")
    category:  Mapped[Optional["Category"]]    = relationship("Category", back_populates="products")
    variants:  Mapped[list["ProductVariant"]]  = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    images:    Mapped[list["ProductImage"]]    = relationship(
        "ProductImage",
        primaryjoin="and_(ProductImage.product_id == Product.product_id, ProductImage.variant_id == None)",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    invoice_items: Mapped[list["InvoiceItem"]] = relationship("InvoiceItem", back_populates="product")