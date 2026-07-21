from datetime import datetime, timedelta
import json

from fastapi import HTTPException, UploadFile, status, Depends
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from app.dependencies import get_db, get_redis_client
import redis.asyncio as redis
from app.models.products.product import Product
from app.repositories.inventory.product_variant_repo import ProductVariantRepository
from app.services.communication.notifications_service import NotificationService
from app.repositories.inventory.inventory_repository import (
    DashboardRepository,
    SupplierRepository,
    CustomerRepository,
    CategoryRepository,
    ProductRepository,
    StockMovementRepository,
    InvoiceRepository,
    InvoiceAttachmentRepository,
)
from app.models.invoices import Invoice
from app.schemas.schema import (
    SupplierCreate, SupplierUpdate,
    CustomerCreate, CustomerUpdate,
    CategoryCreate, CategoryUpdate,
    ProductCreate, ProductUpdate,
    StockMovementCreate,
    InvoiceCreate, InvoiceUpdate,
)
from app.models.supplier.supplier import Supplier

from app.services.storage import CloudinaryStorage
from app.websockets import ws_manager
storage = CloudinaryStorage()

# ===========================================================================
# SUPPLIER SERVICE Encapsulation  class
# ===========================================================================









class SupplierService:
    def __init__(
        self, 
        db: AsyncSession,
        repo = SupplierRepository
    ):
        self.db = db
        self.repo = repo

    async def get_all(self, company_id: int):
        return await self.repo.get_all(company_id)
    






    async def get_by_id(self, supplier_id: int, company_id: int) -> Supplier:
        obj = await self.repo.get_by_id(supplier_id, company_id)
        if not obj:
            raise HTTPException(404, f"Supplier id={supplier_id} not found.")
        return obj





    async def create(
            self, 
            data: SupplierCreate, 
            company_id: int, 
            avatar: UploadFile | None = None
        ):
        payload = {**data.model_dump(), "company_id": company_id}

        if avatar:
            result = await storage.upload_image(avatar, folder=f"suppliers/{company_id}")
            payload["avatar_url"]       = result["secure_url"]
            payload["avatar_public_id"] = result["public_id"]

        return await self.repo.create(payload)

    




    


    
    async def update(
        self,
        supplier_id: int,
        data: SupplierUpdate,
        company_id: int,
        avatar: UploadFile | None = None,
    ) -> Supplier:
        obj = await self.get_by_id(supplier_id, company_id)
        payload = data.model_dump(exclude_none=True)
        if avatar:
            if obj.avatar_public_id:
                await storage.delete_asset(obj.avatar_public_id)
            result = await storage.upload_image(avatar, folder=f"suppliers/{company_id}")
            payload["avatar_url"]       = result["secure_url"]
            payload["avatar_public_id"] = result["public_id"]   

        return await self.repo.update(obj, payload)






    async def delete_avatar(
            self, 
            supplier_id: int, 
            company_id: int
        ):
        """Remove avatar from Cloudinary and clear DB fields."""
        obj = await self.get_by_id(supplier_id, company_id)
        if not obj.avatar_public_id:
            raise HTTPException(404, "Supplier has no avatar.")
        await storage.delete_asset(obj.avatar_public_id)
        return await self.repo.update(obj, {"avatar_url": None, "avatar_public_id": None})




    async def delete(self, supplier_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(supplier_id, company_id)
        # Clean up Cloudinary avatar before deleting the record
        if obj.avatar_public_id:
            await storage.delete_asset(obj.avatar_public_id)

        await self.repo.delete(obj)
        return {"message": f"Supplier '{obj.name}' deleted."}











# ===========================================================================
# FACTORY
# ===========================================================================


async def get_supplier_service(
    db: AsyncSession = Depends(get_db)
) -> SupplierService:
    return SupplierService(
        db = db,
        repo = SupplierRepository(db),
    )





# ===========================================================================
# CUSTOMER SERVICE
# ===========================================================================

class CustomerService:
    def __init__(
        self, 
        db: AsyncSession,
        custom_repo: CustomerRepository,
        ):
        self.custom_repo = custom_repo




    async def get_all(self, company_id: int):
        return await self.custom_repo.get_all(company_id)
    




    async def get_by_id(self, customer_id: int, company_id: int):
        obj = await self.custom_repo.get_by_id(customer_id, company_id)
        if not obj:
            raise HTTPException(404, f"Customer id={customer_id} not found.")
        return obj
    


    async def create(
            self,
            data: CustomerCreate, 
            company_id: int, 
            avatar: UploadFile | None = None
        ):
        payload = {
            "name": data.name,
            "email": data.email,
            "phone": data.phone,
            "company_id": company_id,
        }
        if avatar:
            result = await storage.upload_image(avatar, folder=f"customers/{company_id}")
            payload["avatar_url"] = result["secure_url"]
            payload["avatar_public_id"] = result["public_id"]

        return await self.custom_repo.create(payload)




    async def update(
        self,
        customer_id: int,
        data: CustomerUpdate,
        company_id: int,
        avatar: UploadFile | None = None,
    ):
        obj = await self.get_by_id(customer_id, company_id)
        payload = data.model_dump(exclude_none=True)

        if avatar:
            if obj.avatar_public_id:
                await storage.delete_asset(obj.avatar_public_id)

            result = await storage.upload_image(avatar, folder=f"customers/{company_id}")
            payload["avatar_url"]       = result["secure_url"]
            payload["avatar_public_id"] = result["public_id"]

        return await self.custom_repo.update(obj, payload)
    









    async def delete_avatar(self, customer_id: int, company_id: int):
        obj = await self.get_by_id(customer_id, company_id)
        if not obj.avatar_public_id:
            raise HTTPException(404, "Customer has no avatar.")

        await storage.delete_asset(obj.avatar_public_id)
        return await self.custom_repo.update(obj, {"avatar_url": None, "avatar_public_id": None})





    async def delete(self, customer_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(customer_id, company_id)


        if obj.avatar_public_id:
            await storage.delete_asset(obj.avatar_public_id)





        await self.custom_repo.delete(obj)
        return {"message": f"Customer '{obj.name}' deleted."}


# ===========================================================================
# FACTORY
# ===========================================================================

async def get_customer_service(
        db:  AsyncSession = Depends(get_db)
) -> CustomerService:
    return CustomerService(
        db = db,
        custom_repo = CustomerRepository(db)
    )


# ===========================================================================
# CATEGORY SERVICE
# ===========================================================================
class CategoryService:
    def __init__(
        self,
        db: AsyncSession, 
        cate_repo: CategoryRepository
        ):
        self.cate_repo = cate_repo



    async def get_all(self, company_id: int):
        return await self.cate_repo.get_all(company_id)




    async def get_by_id(self, category_id: int, company_id: int):
        obj = await self.cate_repo.get_by_id(category_id, company_id)
        if not obj:
            raise HTTPException(404, f"Category id={category_id} not found.")
        return obj


    async def create(self, data: CategoryCreate, company_id: int, image: UploadFile | None = None):
        payload = {**data.model_dump(), "company_id": company_id}

        if image:
            result = await storage.upload_image(image, folder=f"categories/{company_id}")
            payload["image_url"]       = result["secure_url"]
            payload["image_public_id"] = result["public_id"]

        return await self.cate_repo.create(payload)
    

    

    async def update(
        self,
        category_id: int,
        data: CategoryUpdate,
        company_id: int,
        image: UploadFile | None = None,
    ):
        obj = await self.get_by_id(category_id, company_id)
        payload = data.model_dump(exclude_none=True)

        if image:
            if obj.image_public_id:
                await storage.delete_asset(obj.image_public_id)

            result = await storage.upload_image(image, folder=f"categories/{company_id}")
            payload["image_url"]       = result["secure_url"]
            payload["image_public_id"] = result["public_id"]

        return await self.cate_repo.update(obj, payload)







    async def delete_image(self, category_id: int, company_id: int):
        obj = await self.get_by_id(category_id, company_id)
        if not obj.image_public_id:
            raise HTTPException(404, "Category has no image.")
        try: 
             await storage.delete_asset(obj.image_public_id)
        except Exception as e:
              print(f"Warning: Cloudinary delete failed: {e}")
        return await self.cate_repo.update(obj, {"image_url": None, "image_public_id": None})




    async def delete(self, category_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(category_id, company_id)
        
        if obj.image_public_id:
            try:
                await storage.delete_asset(obj.image_public_id)
            except Exception as e:
                print(f"Warning: Cloudinary cleanup failed for {obj.image_public_id}: {e}")
        
        await self.cate_repo.delete(obj)
        return {"message": f"Category '{obj.category_name}' deleted."}
    



# ===========================================================================
# FACTORY
# ===========================================================================

async def get_category_service(
        db: AsyncSession = Depends(get_db)
) -> CategoryService:
    return CategoryService(
        db = db,
        cate_repo=CategoryRepository(db)
    )




# ===========================================================================
# PRODUCT SERVICE
# ===========================================================================




class ProductService:



    def __init__(
        self, 
        db: AsyncSession,
        redis_client: redis.Redis,
        product_repo: ProductRepository,
        ):
        self.db = db
        self.redis_client = redis_client
        self.product_repo=product_repo


    async def get_all(
            self, 
            company_id: int, 
            category_id: int | None = None
        ):
        return await self.product_repo.get_all(company_id, category_id)



    async def get_by_id(
            self, 
            product_id: int, 
            company_id: int
        ):
        obj = await self.product_repo.get_by_id(product_id, company_id)
        if not obj:
            raise HTTPException(404, f"Product id={product_id} not found.")
        return obj
    



    async def create(
            self, 
            data: ProductCreate, 
            company_id: int
        ):
        return await self.product_repo.create(
            {
                **data.model_dump(), 
                "company_id": company_id
            })



    async def update(
            self, 
            product_id: int, 
            data: ProductUpdate, 
            company_id: int
        ):
        obj = await self.get_by_id(product_id, company_id)
        return await self.product_repo.update(obj, data.model_dump(exclude_none=True))





    # -------------------------------------------------------------------------
    # Product Images  (product_images table — multi-image)
    # -------------------------------------------------------------------------
    async def add_image(
        self,
        product_id: int,
        company_id: int,
        image: UploadFile,
        is_primary: bool = False,
        sort_order: int = 0,
    ):
        """Upload a new image and attach it to the product."""
        await self.get_by_id(product_id, company_id)   # ensure product exists

        result = await storage.upload_image(image, folder=f"products/{company_id}/{product_id}")

        return await self.product_repo.create_image({
        "company_id":      company_id,
        "product_id":      product_id,
        "image_url":       result["secure_url"],
        "image_public_id": result["public_id"], 
        "is_primary":      is_primary,
        "sort_order":      sort_order,
    })



    

    async def set_primary_image(self, product_id: int, images_id: int, company_id: int):
        """
        Mark one image as primary and demote all others.
        Raises 404 if the image doesn't belong to this product/company.
        """
        img = await self.product_repo.get_image_by_id(images_id, product_id, company_id)
        if not img:
            raise HTTPException(404, f"Product image id={images_id} not found.")

        await self.product_repo.clear_primary_flags(product_id, company_id)
        return await self.product_repo.update_image(img, {"is_primary": True})

    async def delete_image(self, product_id: int, images_id: int, company_id: int) -> dict:
        """Delete a single product image from Cloudinary and the DB."""
        img = await self.product_repo.get_image_by_id(images_id, product_id, company_id)
        if not img:
            raise HTTPException(404, f"Product image id={images_id} not found.")
        

        await storage.delete_asset(img.image_public_id)
        await self.product_repo.delete_image(img)
        return {"message": f"Product image id={images_id} deleted."}

    async def delete(self, product_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(product_id, company_id)

        images = await self.product_repo.get_all_images(product_id, company_id)
        for img in images:
            if img.image_public_id:
                await storage.delete_asset(img.image_public_id)
        await self.product_repo.delete(obj)
        return {"message": f"Product '{obj.name}' deleted."}
    



# ===========================================================================
# FACTORY
# ===========================================================================

async def get_product_service(
    db:  AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
)-> ProductService:
    return ProductService(
        db     = db,
        product_repo  =   ProductRepository(db),
        redis_client  = redis_client
    )





# ===========================================================================
# STOCK MOVEMENT SERVICE
# ===========================================================================

class StockMovementService:
    def __init__(
        self, 
        db: AsyncSession,
        repo_stock: StockMovementRepository,
        variant_repo: ProductVariantRepository,
        redis_client: redis.Redis,
    ):
        self.repo_stock = repo_stock  
        self.variant_repo = variant_repo
        self.notify = NotificationService(db=db, redis_client=redis_client)





    async def get_all(
            self, 
            company_id: int, 
            variant_id: int | None = None
        ):
        return await self.repo_stock.get_all(company_id, variant_id)
    


    async def get_by_id(
            self, 
            movement_id: int, 
            company_id: int
        ):
        obj = await self.repo_stock.get_by_id(movement_id, company_id)
        if not obj:
            raise HTTPException(404, f"Movement id={movement_id} not found.")
        return obj
    

    
    async def create(
            self, 
            data: StockMovementCreate, 
            company_id: int
        ):
        variant  = await self.variant_repo.get_by_id(
            data.variant_id, 
            data.product_id, 
            company_id
        ) 
        if not variant :
            raise HTTPException(404, f"Variant id={data.variant_id} not found.")
        opening_balance = variant.stock_quantity
        new_balance     = opening_balance + data.qty_in - data.qty_out



        if new_balance < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock. Current balance: {opening_balance}",
            )

        movement = await self.repo_stock.create({
            **data.model_dump(exclude={"product_id", "opening_balance", "balance_quantity"}),
            "company_id":       company_id,
            "opening_balance":  opening_balance,
            "balance_quantity": new_balance,
        })
        # await self.variant_repo.update(variant, data.qty_in - data.qty_out)
        await self.variant_repo.update(variant, {"stock_quantity": new_balance})
        return movement
    

    async def deletes(self, movement_id: int, company_id: int) -> dict:
        obj = await self.get_by_id(movement_id, company_id)
        variant = await self.variant_repo.get_by_id_only(obj.variant_id)
        if not variant:
            raise  HTTPException(404, f'Variant d={obj.variant_id} not found')
        
        reversed_balance = variant.stock_quantity - obj.qty_in + obj.qty_out

        if  reversed_balance < 0 :
             raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete movement. Reversing it would result in negative stock ({reversed_balance}).",
           )
    
        await self.repo_stock.update(obj, {
            "is_deleted": True,
            "deleted_at": datetime.utcnow(),
        })
        await self.variant_repo.update(variant, {"stock_quantity": reversed_balance})


        return {"message": f"Movement id={movement_id} deleted and stock reversed."}
    



# ===========================================================================
# FACTORY
# ===========================================================================

async def get_stock_service(
    db:       AsyncSession =  Depends(get_db),
    redis_client:  redis.Redis = Depends(get_redis_client),

    ) -> StockMovementService:
    return StockMovementService(
        db            = db,
        repo_stock    = StockMovementRepository(db),
        variant_repo  =   ProductVariantRepository(db),
        redis_client  = redis_client,
    )

# ===========================================================================
# INVOICE SERVICE
# ===========================================================================

class InvoiceService:
    def __init__(
            self, 
            db: AsyncSession,
            repo:     InvoiceRepository,
            variant_repo: ProductVariantRepository,
            invoice_attach_repo: InvoiceAttachmentRepository,
            redis_client: redis.Redis,
            ):
            self.repo         = repo
            self.variant_repo = variant_repo
            self.invoice_attach_repo = invoice_attach_repo
            self.notify       = NotificationService(
                db             = db,
                redis_client  = redis_client,
            )
  
    # -----------------------------------------------------------------------
    # GET all
    # -----------------------------------------------------------------------


    async def get_all(self, company_id: int, customer_id: int) -> list[Invoice]:
        return await self.repo.get_all(company_id, customer_id)
    


    # -----------------------------------------------------------------------
    # GET by id
    # -----------------------------------------------------------------------


    async def get_by_id(self, invoice_id: int, company_id: int) -> Invoice:
        obj = await self.repo.get_by_id(invoice_id, company_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Invoice id={invoice_id} not found.',
            )
        return obj
    

    # -----------------------------------------------------------------------
    # GET by user_id
    # -----------------------------------------------------------------------
    async def create(self, data: InvoiceCreate, company_id: int):
        invoice = await self.repo.create({
            "company_id":   company_id,
            "customer_id":  data.customer_id,
            "staff_id":     data.staff_id,
            "total_amount": data.total_amount,
            "discount":     data.discount,
            "tax":          data.tax,
            "payment_type": data.payment_type,
        })

        for item in data.items:
            await self.repo.create_item({
                "company_id":  company_id,
                "invoice_id":  invoice.invoice_id,
                "product_id":  item.product_id,
                "variant_id":  item.variant_id,
                "quantity":    item.quantity,
                "unit_price":  item.unit_price,
                "total_price": Decimal(str(item.quantity)) * item.unit_price,
            })
            variant = await self.variant_repo.get_by_id_only(item.variant_id)

            if variant:
                await self.variant_repo.update(
                    variant,
                    {"stock_quantity": variant.stock_quantity - item.quantity}
                )

        return await self.repo.commit_and_refresh(invoice)





    async def update(
            self, 
            invoice_id: int, 
            data: InvoiceUpdate, 
            company_id: int
        ):
        obj = await self.get_by_id(invoice_id, company_id)
        return await self.repo.update(obj, data.model_dump(exclude_none=True))

    # -------------------------------------------------------------------------
    # Invoice Attachments  (invoice_attachments table)
    # -------------------------------------------------------------------------

    async def add_attachment(
        self,
        invoice_id: int,
        company_id: int,
        file: UploadFile,
        file_type: str | None = None,
    ):
        """Upload a file attachment and link it to the invoice."""
        await self.get_by_id(invoice_id, company_id)   

        result = await storage.upload_image(file, folder=f"invoices/{company_id}/{invoice_id}")

        return await self.invoice_attach_repo.create({
            "company_id":  company_id,
            "invoice_id":  invoice_id,
            "file_url":    result["secure_url"],
            "public_id":   result["public_id"],
            "file_name":   file.filename,
            "file_type":   file_type or file.content_type,
        })
    



    async def delete_attachment(
            self, 
            invoice_id: int, 
            attachment_id: int, 
            company_id: int
        ) -> dict:
        """Delete a single invoice attachment from Cloudinary and the DB."""
        att = await self.invoice_attach_repo.get_by_id(attachment_id, invoice_id, company_id)
        if not att:
            raise HTTPException(404, f"Attachment id={attachment_id} not found.")

        await storage.delete_asset(att.public_id)

        await self.invoice_attach_repo.delete(att)

        return {"message": f"Attachment id={attachment_id} deleted."}
    


    async def delete(
            self, 
            invoice_id: int, 
            company_id: int
        ) -> dict:
        obj = await self.get_by_id(invoice_id, company_id)

        # Delete all Cloudinary attachments for this invoice
        attachments = await self.invoice_attach_repo.get_all(invoice_id, company_id)
        for att in attachments:
            await storage.delete_asset(att.public_id)

        await self.repo.delete(obj)
        return {"message": f"Invoice id={invoice_id} deleted."}

# ===============
# 
# 
# ============================================================
# FACTORY
# ===========================================================================

async def get_Invoice_service(
        db:       AsyncSession =  Depends(get_db),
        redis_client:  redis.Redis = Depends(get_redis_client),
)-> InvoiceService:
    return InvoiceService(
        db           = db,
        repo         = InvoiceRepository(db),
        variant_repo = ProductVariantRepository(db),
        invoice_attach_repo = InvoiceAttachmentRepository(db),
        redis_client = redis_client,
    )



# ========================================================================
#  HELPER  
# ========================================================================



def _fill_series(rows: list[dict], key: str, value_key: str, days: int) -> list[float]:
    """Fill in zero-value days so the frontend always gets `days` points, even with no activity."""
    today = datetime.utcnow().date()
    by_day = {r[key]: r[value_key] for r in rows}
    series = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        series.append(by_day.get(d, 0.0))
    return series




def _pct_change(series: list[float]) -> float:
    if len(series) < 2 or series[0] == 0:
        return 0.0
    return round(((series[-1] - series[0]) / abs(series[0])) * 100, 1)










# /////////////////////////
#  Report Service
# ////////////////////////


class  ReportPeriod(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    year  = "year"

  
_PERIOD_CONFIG = {
    ReportPeriod.day:   {"since": timedelta(hours=24), "bucket": "hour",  "points": 24},
    ReportPeriod.week:  {"since": timedelta(days=7),   "bucket": "day",   "points": 7},
    ReportPeriod.month: {"since": timedelta(days=30),  "bucket": "day",   "points": 30},
    ReportPeriod.year:  {"since": timedelta(days=365), "bucket": "month", "points": 12},
}

def _truncate(dt: datetime, bucket: str) -> datetime:
    """"""
    if bucket == "hour":
        return dt.replace(minute=0, second=0, microsecond=0)
    if bucket == "day":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if bucket == "month":
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Unsupported bucket: {bucket}")


def _generate_labels(period: ReportPeriod) -> list[datetime]:
    """Full list of expected bucket start-times for a period, oldest -> newest."""
    cfg = _PERIOD_CONFIG[period]
    bucket, points = cfg["bucket"], cfg["points"]
    now = _truncate(datetime.utcnow(), bucket)
    if bucket == "month":
        labels, year, month = [], now.year, now.month
        for _ in range(points):
            labels.append(datetime(year, month, 1))
            month -= 1
            if month == 0:
                month, year = 12, year - 1
        labels.reverse()
        return labels

    step = timedelta(hours=1) if bucket == "hour" else timedelta(days=1)
    return [now - step * i for i in range(points - 1, -1, -1)]

def _fill_by_bucket(rows: list[dict], value_key: str, labels: list[datetime]) -> list[float]:
    by_bucket = {}
    for r in rows:
        b = r["bucket"]
        if b.tzinfo is not None:
            b = b.replace(tzinfo=None)
        by_bucket[b] = r[value_key]
    return [by_bucket.get(label, 0.0) for label in labels]

    


class DashboardService:
    def __init__(self, db: AsyncSession, repo: DashboardRepository, redis_client: redis.Redis | None = None):
        self.db=db
        self.repo = repo
        self.redis_client = redis_client
        


    async def get_state(self, company_id: int, days: int = 11) -> dict:

        revenue_rows = await self.repo.get_daily_revenue(company_id, days)
        stock_rows =  await self.repo.get_daily_stock_net(company_id, days)
        expense_rows = await self.repo.get_daily_expenses(company_id, days)
        stock_totals = await self.repo.get_stock_in_out_totals(company_id)
        current_stock = await self.repo.get_current_stock_total(company_id)
        stock_value   = await self.repo.get_total_stock_value(company_id)



        revenue_series = _fill_series(revenue_rows, "day", "total", days)
        stock_series = _fill_series(stock_rows, "day", "net", days)
        expense_series = _fill_series(expense_rows, "day", "total", days)


        return {
            "live_chat": {
                "value": ws_manager.ws_manager.get_company_online_count(company_id),
                "sub": "active now",
                "spark": [0.0] * days,
            },
            "stock": {
                "value": current_stock,
                "stock_in": stock_totals["total_in"],
                "stock_out": stock_totals["total_out"],
                "badge_pct": _pct_change(stock_series),
                "sub": "current units",
                "spark": stock_series,
            },
            "stock_value": {
                "value": stock_value,
                "badge_pct": None,
                "sub": "inventory worth",
                "spark": [0.0] * days,
            },
            "expenses": {
                "value": sum(expense_series),
                "badge_pct": _pct_change(expense_series),
                "sub": "vs last period",
                "spark": expense_series,
            },
            "revenue": {
                "value": sum(revenue_series),
                "badge_pct": _pct_change(revenue_series),
                "sub": "this period",
                "spark": revenue_series,
            },
        }

    
    async def get_report(self, company_id: int, period: ReportPeriod) -> dict:
        cache_key = f"dashboard:report:{company_id}:{period.value}"

        if self.redis_client:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

        cfg = _PERIOD_CONFIG[period]
        since  = datetime.utcnow() - cfg["since"]
        bucket = cfg["bucket"]
        labels = _generate_labels(period)

        revenue_rows  = await self.repo.get_revenue_by_bucket(company_id, since, bucket)
        stock_rows    = await self.repo.get_stock_net_by_bucket(company_id, since, bucket)
        stock_in_rows = await self.repo.get_stock_in_by_bucket(company_id, since, bucket)
        stock_out_rows= await self.repo.get_stock_out_by_bucket(company_id, since, bucket)
        expense_rows  = await self.repo.get_expenses_by_bucket(company_id, since, bucket)

        revenue_series   = _fill_by_bucket(revenue_rows, "total", labels)
        stock_series     = _fill_by_bucket(stock_rows, "net", labels)
        stock_in_series  = _fill_by_bucket(stock_in_rows, "total", labels)
        stock_out_series = _fill_by_bucket(stock_out_rows, "total", labels)
        expense_series   = _fill_by_bucket(expense_rows, "total", labels)

        result = {
            "period": period.value,
            "labels": [l.isoformat() for l in labels],
            "revenue": {
                "value": sum(revenue_series),
                "badge_pct": _pct_change(revenue_series),
                "spark": revenue_series,
            },
            "stock": {
                "value": sum(stock_series),
                "stock_in": sum(stock_in_series),
                "stock_out": sum(stock_out_series),
                "badge_pct": _pct_change(stock_series),
                "spark": stock_series,
                "spark_in": stock_in_series,
                "spark_out": stock_out_series,
            },
            "expenses": {
                "value": sum(expense_series),
                "badge_pct": _pct_change(expense_series),
                "spark": expense_series,
            },
        }

        if self.redis_client:
            ttl = 60 if period == ReportPeriod.day else 300
            await self.redis_client.set(cache_key, json.dumps(result), ex=ttl)

        return result



async def get_dashboard_service(
            db: AsyncSession = Depends(get_db),
            get_redis_client: redis.Redis = Depends(get_redis_client)
    )      -> DashboardService:
        return DashboardService(db=db, repo=DashboardRepository(db), redis_client=get_redis_client)



