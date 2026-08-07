from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.products.product import Product
from app.models.products.product_variant import ProductVariant
from app.models.products.product_image import ProductImage


class ProductVariantRepository:
    def __init__(self, db: AsyncSession):
        self.db = db




    async def get_all(self, product_id: int, company_id: int) -> list[ProductVariant]:
        r = await self.db.execute(
            select(ProductVariant)
            .options(selectinload(ProductVariant.images))
            .where(ProductVariant.product_id == product_id)
            .order_by(ProductVariant.variant_id)
        )
        return r.scalars().all()




    async def get_by_id(
     self, variant_id: int, product_id: int, company_id: int
     ) -> ProductVariant | None:
        r = await self.db.execute(
            select(ProductVariant)
            .options(selectinload(ProductVariant.images))
            .join(Product, ProductVariant.product_id == Product.product_id) 
            .where(
                ProductVariant.variant_id == variant_id,
                ProductVariant.product_id == product_id,
                Product.company_id        == company_id,  # ADD
            )
        )
        return r.scalar_one_or_none()
    



    
    async def get_by_id_only(self, variant_id: int) -> ProductVariant | None:
        r = await self.db.execute(
            select(ProductVariant)
            .where(ProductVariant.variant_id == variant_id)
        )
        return r.scalar_one_or_none()





    async def get_by_sku(self, product_id: int, sku: str) -> ProductVariant | None:
        r = await self.db.execute(
            select(ProductVariant).where(
                ProductVariant.product_id == product_id,
                ProductVariant.sku        == sku,
            )
        )
        return r.scalar_one_or_none()




    async def create(self, data: dict) -> ProductVariant:
        obj = ProductVariant(**data)
        self.db.add(obj)
        await self.db.commit()
        result = await self.db.execute(
            select(ProductVariant)
            .options(selectinload(ProductVariant.images))
            .where(ProductVariant.variant_id == obj.variant_id)
        )
        return result.scalar_one()




    async def update(self, obj: ProductVariant, data: dict) -> ProductVariant:
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj




    async def delete(self, obj: ProductVariant) -> None:
        await self.db.delete(obj)
        await self.db.commit()




    # ── Variant Images ──────────────────────────────────────────────────────

    async def get_all_images(self, variant_id: int) -> list[ProductImage]:
        r = await self.db.execute(
            select(ProductImage)
            .where(ProductImage.variant_id == variant_id)
            .order_by(ProductImage.sort_order)
        )
        return r.scalars().all()
    



    async def get_image_by_id(
        self, images_id: int, variant_id: int, company_id: int
    ) -> ProductImage | None:
        r = await self.db.execute(
            select(ProductImage).where(
                ProductImage.images_id  == images_id,
                ProductImage.variant_id == variant_id,
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
    



    async def clear_primary_flags(self, variant_id: int, company_id: int) -> None:
        await self.db.execute(
            update(ProductImage)
            .where(
                ProductImage.variant_id == variant_id,
                ProductImage.company_id == company_id,
            )
            .values(is_primary=False)
        )
        await self.db.commit()



    async def delete_image(self, obj: ProductImage) -> None:
        await self.db.delete(obj)
        await self.db.commit()