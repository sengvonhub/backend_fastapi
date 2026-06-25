from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.models.products.product import Product
from app.models.products.product_variant import ProductVariant
from app.models.supplier.supplier_product_price import SupplierProductPrice
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload


class SupplierProductPriceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        company_id:  int,
        supplier_id: int | None = None,
        variant_id:  int | None = None,
    ) -> list[SupplierProductPrice]:
        q = (
            select(SupplierProductPrice)
            .join(SupplierProductPrice.supplier)
            .where(SupplierProductPrice.supplier.has(company_id=company_id))
            .options(
                joinedload(SupplierProductPrice.variant)
                .joinedload(ProductVariant.product),
                joinedload(SupplierProductPrice.supplier),
            )
        )
        if supplier_id:
            q = q.where(SupplierProductPrice.supplier_id == supplier_id)
        if variant_id:
            q = q.where(SupplierProductPrice.variant_id == variant_id)
        r = await self.db.execute(q.order_by(SupplierProductPrice.price_id))
        return r.scalars().all()



    async def get_by_id(self, price_id: int, company_id: int) -> SupplierProductPrice | None:
        r = await self.db.execute(
            select(SupplierProductPrice)
            .join(SupplierProductPrice.supplier)
            .where(
                SupplierProductPrice.price_id == price_id,
                SupplierProductPrice.supplier.has(company_id=company_id),
            )
            .options(
                joinedload(SupplierProductPrice.variant)
                .joinedload(ProductVariant.product),
                joinedload(SupplierProductPrice.supplier),
            )
        )
        return r.unique().scalar_one_or_none()


# /////////////////////////////////////////////////////////////
# 
# ////////////////////////////////////////////////////////////

    async def get_categories_by_supplier(self, supplier_id: int, company_id: int) -> list[Category]:
            q = (
                select(Category)
                .distinct()
                .join(Product, Product.category_id == Category.category_id)
                .join(ProductVariant, ProductVariant.product_id == Product.product_id)
                .join(SupplierProductPrice, SupplierProductPrice.variant_id == ProductVariant.variant_id)
                .where(
                    SupplierProductPrice.supplier_id == supplier_id,
                    Category.company_id == company_id,
                )
            )
            r = await self.db.execute(q)
            return r.scalars().all()
# /////////////////////////////////////////////////////////////
# 
# ////////////////////////////////////////////////////////////


    async def get_by_supplier_variant(
        self,
        supplier_id: int,
        variant_id:  int,
    ) -> SupplierProductPrice | None:
        r = await self.db.execute(
            select(SupplierProductPrice).where(
                SupplierProductPrice.supplier_id == supplier_id,
                SupplierProductPrice.variant_id  == variant_id,
            )
        )
        return r.scalar_one_or_none()


    async def create(self, data: dict, company_id:int) -> SupplierProductPrice:
        obj = SupplierProductPrice(**data)
        self.db.add(obj)
        await self.db.commit()
        return await  self.get_by_id(obj.price_id, company_id)
    

    

    async def update(self, obj: SupplierProductPrice, data: dict) -> SupplierProductPrice:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: SupplierProductPrice) -> None:
        await self.db.delete(obj)
        await self.db.commit()