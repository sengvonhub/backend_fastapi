from sqlalchemy import Integer, Numeric, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from .invoice import Invoice
    from ..products import Product
    from ..company import Company
    from ..products.product_variant import ProductVariant
class InvoiceItem(Base):
        __tablename__ = "invoice_items"

        item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
        invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("invoices.invoice_id"), nullable=False)

        # now optional — only set for inventory-backed lines
        product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("products.product_id"), nullable=True)
        variant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("product_variants.variant_id"), nullable=True, index=True)

        # new — only set for quotation/print-job-derived lines
        item_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
        size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
        pages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
        print_side: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
        color_spec: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
        paper_cover: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
        paper_inside: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
        finishing: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

        quantity: Mapped[int] = mapped_column(Integer, nullable=False)
        unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
        total_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

        company: Mapped["Company"] = relationship("Company", back_populates="invoice_items")
        invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")
        product: Mapped[Optional["Product"]] = relationship("Product", back_populates="invoice_items")
        variant: Mapped[Optional["ProductVariant"]] = relationship("ProductVariant", back_populates="invoice_items")