from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Date, and_, cast, func, select, update
from app.exceptions.exceptions import NotFoundException
from sqlalchemy.orm import selectinload
from app.models.products.product_variant import ProductVariant
from app.models.supplier.supplier import Supplier
from app.models.customer import Customer
from app.models.category import Category
from app.models.products.product import Product
from app.models.products.product_image import ProductImage
from app.models.products.stock_movement import StockMovement
from app.models.invoices.invoice import Invoice
from app.models.invoices.invoice_item import InvoiceItem
from app.models.invoices.invoice_attachments import InvoiceAttachment
from app.schemas.schema import StockMovementReportBucket, StockMovementReportResponse


# ===========================================================================
# SUPPLIER
# ===========================================================================

class SupplierRepository:
    def __init__(self, db: AsyncSession):
        self.db = db




    async def get_all(self, company_id: int) -> list[Supplier]:
        r = await self.db.execute(
            select(Supplier)
            .where(Supplier.company_id == company_id)
            .order_by(Supplier.name)
        )
        return r.scalars().all()
    





    async def get_by_id(self, supplier_id: int, company_id: int) -> Supplier | None:
        r = await self.db.execute(
            select(Supplier).where(
                Supplier.supplier_id == supplier_id,
                Supplier.company_id  == company_id,
            )
        )
        return r.scalar_one_or_none()
    


    async def create(self, data: dict) -> Supplier:
        obj = Supplier(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj
    


    async def update(self, obj: Supplier, data: dict) -> Supplier:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj
    



    async def delete(self, obj: Supplier) -> None:
        await self.db.delete(obj)
        await self.db.commit()


# ===========================================================================
# CUSTOMER
# ===========================================================================

class CustomerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db




    async def get_all(self, company_id: int) -> list[Customer]:
        r = await self.db.execute(
            select(Customer)
            .where(Customer.company_id == company_id)
            .order_by(Customer.name)
        )
        return r.scalars().all()




    async def get_by_id(self, customer_id: int, company_id: int) -> Customer | None:
        r = await self.db.execute(
            select(Customer).where(
                Customer.customer_id == customer_id,
                Customer.company_id  == company_id,
            )
        )
        return r.scalar_one_or_none()





    async def create(self, data: dict) -> Customer:
        obj = Customer(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj







    async def update(self, obj: Customer, data: dict) -> Customer:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj




    async def delete(self, obj: Customer) -> None:
        await self.db.delete(obj)
        await self.db.commit()





# ===========================================================================
# CATEGORY
# ===========================================================================



class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, company_id: int) -> list[Category]:
        r = await self.db.execute(
            select(Category)
            .where(Category.company_id == company_id)
            .order_by(Category.category_name)
        )
        return r.scalars().all()

    async def get_by_id(self, category_id: int, company_id: int) -> Category | None:
        r = await self.db.execute(
            select(Category).where(
                Category.category_id == category_id,
                Category.company_id  == company_id,
            )
        )
        return r.scalar_one_or_none()

    async def create(self, data: dict) -> Category:
        obj = Category(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: Category, data: dict) -> Category:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: Category) -> None:
        await self.db.delete(obj)
        await self.db.commit()


# ===========================================================================
# PRODUCT
# ===========================================================================





class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

        
    async def get_all(
            self, 
            company_id: int, 
            category_id: int | None = None
        ) -> list[Product]:
        query = (
            select(Product)
            .options(
                selectinload(Product.images),
                selectinload(Product.variants)
                  .selectinload(ProductVariant.images),
                )  
            .where(Product.company_id == company_id)
            .order_by(Product.name)
        )
        if category_id:
            query = query.where(Product.category_id == category_id)
        r = await self.db.execute(query)
        return r.scalars().all()
    




    async def get_by_id(
            self, 
            product_id: int, 
            company_id: int
        ) -> Product | None:
        r = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.images),
                selectinload(Product.variants)
                .selectinload(ProductVariant.images)
                ,
                ) 
            .where(
                Product.product_id == product_id,
                Product.company_id == company_id,
            )
        )
        return r.scalar_one_or_none()




    async def create(self, data: dict) -> Product:
        obj = Product(**data)
        self.db.add(obj)
        await self.db.commit()
        return await self.get_by_id(obj.product_id, obj.company_id) 






    async def update(self, obj: Product, data: dict) -> Product:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        return await self.get_by_id(obj.product_id, obj.company_id)  


    async def delete(self, obj: Product) -> None:
        await self.db.delete(obj)
        await self.db.commit()

    


    
    
    # --- product_images ---

    async def get_all_images(self, product_id: int, company_id: int) -> list[ProductImage]:
        r = await self.db.execute(
            select(ProductImage)
            .where(
                ProductImage.product_id == product_id,
                ProductImage.company_id == company_id,
            )
            .order_by(ProductImage.sort_order)
        )
        return r.scalars().all()

    async def get_image_by_id(self, images_id: int, product_id: int, company_id: int) -> ProductImage | None:
        r = await self.db.execute(
            select(ProductImage).where(
                ProductImage.images_id   == images_id,
                ProductImage.product_id == product_id,
                ProductImage.company_id == company_id,
            )
        )
        return r.scalar_one_or_none()

    async def create_image(self, data: dict) -> ProductImage:
        obj = ProductImage(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update_image(self, obj: ProductImage, data: dict) -> ProductImage:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def clear_primary_flags(self, product_id: int, company_id: int) -> None:
        """Set is_primary=False on all images for this product before promoting a new one."""
        await self.db.execute(
            update(ProductImage)
            .where(
                ProductImage.product_id == product_id,
                ProductImage.company_id == company_id,
            )
            .values(is_primary=False)
        )
        await self.db.commit()

    async def delete_image(self, obj: ProductImage) -> None:
        await self.db.delete(obj)
        await self.db.commit()


# ===========================================================================
# STOCK MOVEMENT
# ===========================================================================





class StockMovementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db





    async def get_all(
            self, 
            company_id: int, 
            variant_id: int | None = None,
            start_date: datetime | None = None,
            end_date: datetime | None = None,
        ):
        query = (
            select(StockMovement)
            .where(
                StockMovement.company_id == company_id,
                StockMovement.is_deleted == False,
            )
            .order_by(StockMovement.date.desc())
        )

        if variant_id:
            query = query.where(StockMovement.variant_id == variant_id)

        if start_date :
            query = query.where(StockMovement.date >= start_date)

        if end_date:
            query = query.where(StockMovement.date <= end_date)
        
        r = await self.db.execute(query)
        return r.scalars().all()



    async def get_report(
        self,
        company_id: int,
        period: str,
        category_id: int | None = None,
        variant_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        filters = [Product.company_id == company_id]

        if category_id is not None:
            filters.append(Product.category_id == category_id)
        if variant_id is not None:
            filters.append(ProductVariant.variant_id == variant_id)

        movement_filters = [
                StockMovement.variant_id == ProductVariant.variant_id,
                StockMovement.is_deleted == False,
            ]
        
        if start_date is not None:
            movement_filters.append(StockMovement.date >= start_date)
        if end_date is not None:
            movement_filters.append(StockMovement.date < end_date)
            




        base = (
            select(
                Product.category_id,
                Category.category_name,
                Product.product_id,
                Product.name,
                Product.descriptions,
                ProductVariant.variant_id,
                ProductVariant.sku,
                ProductVariant.specs,
                ProductVariant.price,
                func.coalesce(func.sum(StockMovement.qty_in), 0).label("qty_in"),
                func.coalesce(func.sum(StockMovement.qty_out), 0).label("qty_out"),
                func.count(StockMovement.movement_id).label("movement_count"),

                func.coalesce(func.sum(StockMovement.qty_in * func.coalesce(StockMovement.unit_price, ProductVariant.price)), 0).label("value_in"),
                func.coalesce(func.sum(StockMovement.qty_out * func.coalesce(StockMovement.unit_price, ProductVariant.price)), 0).label("value_out"),
                )

            .select_from(Product)
            .outerjoin(Category, Category.category_id == Product.category_id)
            .outerjoin(ProductVariant, ProductVariant.product_id == Product.product_id)
            .outerjoin(StockMovement,and_(*movement_filters))
            .where(*filters)
        )


        group_cols = [
            Product.category_id, Category.category_name,
            Product.product_id, Product.name, Product.descriptions,
            ProductVariant.variant_id, ProductVariant.sku,
            ProductVariant.specs, ProductVariant.price,
        ]
        if period == "all":
            query = base.group_by(*group_cols)
        else:
            trunc = func.date_trunc(period, StockMovement.date)
            query = (
                base.add_columns(trunc.label("bucket"))
                .group_by(trunc, *group_cols)
                .order_by(ProductVariant.variant_id, trunc)
            )

        r = await self.db.execute(query)
        return r.all()












    async def get_balance_by_bucket(
             self,
            company_id: int,
            period: str,
            variant_id: int | None = None,
            start_date: datetime | None = None,
            end_date: datetime | None = None,
    ): 
        trunc = func.date_trunc(period, StockMovement.date).label("bucket")
        row_num = (func.row_number()
            .over(
                partition_by=(StockMovement.variant_id, trunc),
                order_by=(StockMovement.date.desc(), StockMovement.movement_id.desc()),
            )
            .label("rn")
        )

        filters = [
        StockMovement.company_id == company_id,
        StockMovement.is_deleted == False,
       ]

        if variant_id is not None:
           filters.append(StockMovement.variant_id == variant_id)
        if start_date is not None:
            filters.append(StockMovement.date >= start_date)
        if end_date is not None:
            filters.append(StockMovement.date < end_date)
        subq = (
            select(
                StockMovement.variant_id,
                trunc,
                StockMovement.balance_quantity,
                row_num,
            )
            .where(*filters)
            .subquery()
        )
        query = (
            select(
                subq.c.variant_id,
                subq.c.bucket,
                subq.c.balance_quantity.label("closing_balance"),
            )
            .where(subq.c.rn == 1)
            .order_by(subq.c.variant_id, subq.c.bucket)
        )
        r = await self.db.execute(query)
        return r.all()


    async def get_opening_balance_before(
        self,
        company_id: int,
        variant_id: int,
        start_date: datetime,
    ) -> int:
        query = (
            select(StockMovement.balance_quantity)
            .where(
                StockMovement.company_id == company_id,
                StockMovement.variant_id == variant_id,
                StockMovement.date < start_date,
                StockMovement.is_deleted == False,
            )
            .order_by(StockMovement.date.desc(), StockMovement.movement_id.desc())
            .limit(1)
        )
        r = await self.db.execute(query)
        return r.scalar_one_or_none() or 0












    async def get_by_id(self, movement_id: int, company_id: int):
        r = await self.db.execute(
            select(StockMovement).where(
                StockMovement.movement_id == movement_id,
                StockMovement.company_id  == company_id,
                StockMovement.is_deleted  == False,
            )
        )
        return r.scalar_one_or_none()



    async def create(self, data: dict) -> StockMovement:
        obj = StockMovement(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj




    



    async def update(self, obj: StockMovement, data: dict) -> StockMovement:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: StockMovement) -> None:
        await self.db.delete(obj)
        await self.db.commit()











# ===========================================================================
# INVOICE
# ===========================================================================

class InvoiceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
            self, 
            company_id: int, 
            customer_id: int | None = None
        ) -> list[Invoice]:
        query = (
            select(Invoice)
            .options(
                selectinload(Invoice.items),
                selectinload(Invoice.attachments)
                )
            .where(Invoice.company_id == company_id)
            .order_by(Invoice.created_at.desc())
        )
        if customer_id:
            query = query.where(Invoice.customer_id == customer_id)
        r = await self.db.execute(query)
        return r.scalars().all()

        # =====================================================================
        # 
        # =====================================================================



    async def get_by_id(self, invoice_id: int, company_id: int) -> Invoice | None:
        r = await self.db.execute(
            select(Invoice)
            .options(
                selectinload(Invoice.items),
                selectinload(Invoice.attachments),
            )
            .where(
                Invoice.invoice_id == invoice_id,
                Invoice.company_id == company_id,
            )
        )
        return r.scalar_one_or_none()
    
        # =====================================================================
        # 
        # =====================================================================
    


    async def create(self, data: dict) -> Invoice:
        obj = Invoice(**data)
        self.db.add(obj)
        await self.db.flush()  
        return obj

    async def create_item(self, data: dict) -> InvoiceItem:
        obj = InvoiceItem(**data)
        self.db.add(obj)
        return obj           

    async def commit_and_refresh(self, obj: Invoice) -> Invoice:
        await self.db.commit()
        r = await self.db.execute(
            select(Invoice)
            .options(
                selectinload(Invoice.items),
                selectinload(Invoice.attachments),
            )
            .where(Invoice.invoice_id == obj.invoice_id)
        )
        return r.scalar_one()
    async def update(self, obj: Invoice, data: dict) -> Invoice:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        r = await self.db.execute(
            select(Invoice)
            .options(
                selectinload(Invoice.items),
                selectinload(Invoice.attachments),
            )
            .where(Invoice.invoice_id == obj.invoice_id)
        )
        return r.scalar_one()
    async def delete(self, obj: Invoice) -> None:
        await self.db.delete(obj)
        await self.db.commit()


# ===========================================================================
# INVOICE ATTACHMENT
# ===========================================================================

class InvoiceAttachmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_all(self, invoice_id: int, company_id: int) -> list[InvoiceAttachment]:
        r = await self.db.execute(
            select(InvoiceAttachment)
            .where(
                InvoiceAttachment.invoice_id == invoice_id,
                InvoiceAttachment.company_id == company_id,
            )
            .order_by(InvoiceAttachment.created_at.desc())
        )
        return r.scalars().all()


    async def get_by_id(
        self, attachment_id: int, invoice_id: int, company_id: int
    ) -> InvoiceAttachment | None:
        r = await self.db.execute(
            select(InvoiceAttachment).where(
                InvoiceAttachment.attachment_id == attachment_id,
                InvoiceAttachment.invoice_id    == invoice_id,
                InvoiceAttachment.company_id    == company_id,
            )
        )
        return r.scalar_one_or_none()
    


    async def create(self, data: dict) -> InvoiceAttachment:
        obj = InvoiceAttachment(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj




    async def delete(self, obj: InvoiceAttachment) -> None:
        await self.db.delete(obj)
        await self.db.commit()




    async def delete_all_by_invoice(
            self, 
            invoice_id: int, 
            company_id: int
        ) -> list[str]:
        """
        Fetches all public_ids for Cloudinary cleanup, then bulk-deletes all
        attachment rows. Called by the service before deleting an invoice.
        """
        attachments = await self.get_all(invoice_id, company_id)
        public_ids  = [a.public_id for a in attachments if a.public_id]
        for att in attachments:
            await self.db.delete(att)
        await self.db.commit()
        return public_ids
    

    
#===========================================================================
# 
# ==========================================================================

class DashboardRepository:
   
   
    def __init__(self, db: AsyncSession):
        self.db = db



    async def get_daily_revenue(self, company_id: int, days: int = 11) -> list[dict]:
        since = datetime.utcnow() - timedelta(days=days - 1)
        r = await self.db.execute(
            select(
                cast(Invoice.created_at, Date).label("day"),
                func.coalesce(func.sum(Invoice.total_amount), 0).label("total"),
            )
            .where(
                Invoice.company_id == company_id,
                Invoice.created_at >= since,
            )
            .group_by("day")
            .order_by("day")
        )
        return [{"day": row.day, "total": float(row.total)} for row in r.all()]


    async def get_daily_revenue_range(self, company_id: int, start: datetime, end: datetime) -> list[dict]:
        r = await self.db.execute(
            select(
                cast(Invoice.created_at, Date).label("day"),
                func.coalesce(func.sum(Invoice.total_amount), 0).label("total"),
            )
            .where(
                Invoice.company_id == company_id,
                Invoice.created_at >= start,
                Invoice.created_at < end,
            )
            .group_by("day")
            .order_by("day")
        )
        return [{"day": row.day, "total": float(row.total)} for row in r.all()]


    async def get_daily_expenses_range(self, company_id: int, start: datetime, end: datetime) -> list[dict]:
        r = await self.db.execute(
            select(
                cast(StockMovement.date, Date).label("day"),
                func.coalesce(
                    func.sum(StockMovement.qty_out * func.coalesce(StockMovement.unit_price, 0)), 0
                ).label("total"),
            )
            .where(
                StockMovement.company_id == company_id,
                StockMovement.is_deleted == False,
                StockMovement.date >= start,
                StockMovement.date < end,
            )
            .group_by("day")
            .order_by("day")
        )
        return [{"day": row.day, "total": float(row.total)} for row in r.all()]


    async def get_daily_stock_net_range(self, company_id: int, start: datetime, end: datetime) -> list[dict]:
            r = await self.db.execute(
                select(
                    cast(StockMovement.date, Date).label("day"),
                    func.coalesce(
                        func.sum(StockMovement.qty_in - StockMovement.qty_out), 0
                    ).label("net"),
                )
                .where(
                    StockMovement.company_id == company_id,
                    StockMovement.is_deleted == False,
                    StockMovement.date >= start,
                    StockMovement.date < end,
                )
                .group_by("day")
                .order_by("day")
            )
            return [{"day": row.day, "net": float(row.net)} for row in r.all()]
    




    async def get_daily_stock_net(self, company_id: int, days: int = 11) -> list[dict]:
        since = datetime.utcnow() - timedelta(days=days - 1)
        r = await self.db.execute(
            select(
                cast(StockMovement.date, Date).label("day"),
                func.coalesce(
                    func.sum(StockMovement.qty_in - StockMovement.qty_out), 0
                ).label("net"),
            )
            .where(
                StockMovement.company_id == company_id,
                StockMovement.is_deleted == False,
                StockMovement.date >= since,
            )
            .group_by("day")
            .order_by("day")
        )
        return [{"day": row.day, "net": float(row.net)} for row in r.all()]






    async def get_daily_stock_out(self, company_id: int, days: int = 11) -> list[dict]:
        """Per-day units shipped out — useful for its own chart, not for a running total."""
        since = datetime.utcnow() - timedelta(days=days - 1)
        r = await self.db.execute(
            select(
                cast(StockMovement.date, Date).label("day"),
                func.coalesce(func.sum(StockMovement.qty_out), 0).label("total"),
            ).where(
                StockMovement.company_id == company_id,
                StockMovement.is_deleted == False,
                StockMovement.date >= since,
            )
            .group_by("day")
            .order_by("day")
        )
        return [{"day": row.day, "total": float(row.total)} for row in r.all()]
    



    async def get_stock_in_out_totals(self, company_id: int) -> dict:
        r = await self.db.execute(
            select(
                func.coalesce(func.sum(StockMovement.qty_in), 0).label("total_in"),
                func.coalesce(func.sum(StockMovement.qty_out), 0).label("total_out"),
            ).where(
                StockMovement.company_id == company_id,
                StockMovement.is_deleted == False,
            )
        )
        row = r.one()
        return {"total_in": float(row.total_in), "total_out": float(row.total_out)}
        


    async def get_all_time_expenses(self, company_id: int) -> float:
        r = await self.db.execute(
            select(
                func.coalesce(
                    func.sum(StockMovement.qty_out * func.coalesce(StockMovement.unit_price, 0)), 0
                )
            ).where(
                StockMovement.company_id == company_id,
                StockMovement.is_deleted == False,
            )
        )
        return float(r.scalar() or 0)


    async def get_all_time_revenue(self, company_id: int) -> float:
        r = await self.db.execute(
            select(func.coalesce(func.sum(Invoice.total_amount), 0))
            .where(Invoice.company_id == company_id)
        )
        return float(r.scalar() or 0)


    async def get_all_time_stock_net(self, company_id: int) -> float:
        r = await self.db.execute(
            select(
                func.coalesce(func.sum(StockMovement.qty_in - StockMovement.qty_out), 0)
            ).where(
                StockMovement.company_id == company_id,
                StockMovement.is_deleted == False,
            )
        )
        return float(r.scalar() or 0)



    async def get_current_stock_total(self, company_id: int) -> float:
        r = await self.db.execute(
            select(
                func.coalesce(func.sum(StockMovement.qty_in - StockMovement.qty_out), 0)
            ).where(
                StockMovement.company_id == company_id,
                StockMovement.is_deleted == False,
            )
        )
        return float(r.scalar() or 0)
    


    #===========================================================================
    # 
    # =========================================================================
    

    async def get_daily_expenses(self, company_id: int, days: int = 11) -> list[dict]:
        """Sums qty_out × unit_price (cost of goods shipped out) as a stand-in for expense trend until a real Expense model exists."""
        since = datetime.utcnow() - timedelta(days=days - 1)
        r = await self.db.execute(
            select(
                cast(StockMovement.date, Date).label("day"),
                func.coalesce(
                    func.sum(StockMovement.qty_out * func.coalesce(StockMovement.unit_price, 0)), 0
                ).label("total"),
            )
            .where(
                StockMovement.company_id == company_id,
                StockMovement.is_deleted == False,
                StockMovement.date >= since,
            )
            .group_by("day")
            .order_by("day")
        )
        return [{"day": row.day, "total": float(row.total)} for row in r.all()]


    
    #===========================================================================
    # 
    # =========================================================================
    

    async def get_total_stock_value(self, company_id: int) -> float:
        r = await self.db.execute(
            select(
                func.coalesce(
                    func.sum(ProductVariant.price * ProductVariant.stock_quantity), 0
                )
            )
            .select_from(ProductVariant)
            .join(Product, ProductVariant.product_id == Product.product_id)
            .where(Product.company_id == company_id)
        )
        return float(r.scalar() or 0)
    

    
    # =====================================================================
    # 
    # =====================================================================
    async def get_revenue_by_bucket(self, company_id: int, since: datetime, bucket: str) -> list[dict]:
        trunc = func.date_trunc(bucket, Invoice.created_at).label("bucket")

        r = await self.db.execute(
            select(trunc, func.coalesce(func.sum(Invoice.total_amount),0).label("total"))
            .where(Invoice.company_id == company_id, Invoice.created_at >= since)
            .group_by("bucket")
            .order_by("bucket")
        )
        return [{"bucket": row.bucket, "total": float(row.total)} for row in r.all()]
    
    # =====
    # 
    # =====
    async def get_stock_net_by_bucket(self, company_id: int, since: datetime, bucket: str)  -> list[dict]:
        trunc = func.date_trunc(bucket, StockMovement.date).label("bucket")
        r = await self.db.execute(
            select(trunc, func.coalesce(func.sum(StockMovement.qty_in - StockMovement.qty_out), 0).label("net"))
            .where(
                StockMovement.company_id == company_id,
                StockMovement.is_deleted == False,
                StockMovement.date >= since,
            )
            .group_by("bucket")
            .order_by("bucket")
        )
        return [{"bucket": row.bucket, "net": float(row.net)} for row in r.all()]
    

    #  ==
    # 
    #  ==
   
    async def get_expenses_by_bucket(self, company_id: int, since: datetime, bucket: str) -> list[dict]:
        trunc = func.date_trunc(bucket, StockMovement.date).label("bucket")
        r = await self.db.execute(
           select(
               trunc, func.coalesce(
                   func.sum(
                       StockMovement.qty_out
                   ), 0
               ).label("total")
           ).where(
            StockMovement.company_id == company_id,
            StockMovement.is_deleted == False,
            StockMovement.date >= since,
           )
           .group_by("bucket")
           .order_by("bucket")
        )
        return [{"bucket": row.bucket, "total": float(row.total)} for row in r.all()]
    

    async def get_stock_in_by_bucket(self, company_id: int, since: datetime, bucket: str) -> list[dict]:
        trunc = func.date_trunc(bucket, StockMovement.date).label("bucket")
        r = await self.db.execute(
            select(trunc, func.coalesce(func.sum(StockMovement.qty_in), 0).label("total"))
            .where(
                StockMovement.company_id == company_id,
                StockMovement.is_deleted == False,
                StockMovement.date >= since,
            )
            .group_by("bucket")
            .order_by("bucket")
        )
        return [{"bucket": row.bucket, "total": float(row.total)} for row in r.all()]



    async def get_stock_out_by_bucket(self, company_id: int, since: datetime, bucket: str) -> list[dict]:
        trunc = func.date_trunc(bucket, StockMovement.date).label("bucket")
        r = await self.db.execute(
            select(trunc, func.coalesce(func.sum(StockMovement.qty_out), 0).label("total"))
            .where(
                StockMovement.company_id == company_id,
                StockMovement.is_deleted == False,
                StockMovement.date >= since,
            )
            .group_by("bucket")
            .order_by("bucket")
        )
        return [{"bucket": row.bucket, "total": float(row.total)} for row in r.all()]




    







        
        