from fastapi import Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.repositories.inventory.product_variant_repo import ProductVariantRepository
from app.schemas.schema import ProductVariantCreate, ProductVariantUpdate
from app.models.products.product_variant import ProductVariant
from app.models.products.product_image import ProductImage
from app.services.storage import CloudinaryStorage

storage = CloudinaryStorage()


class ProductVariantService:
    def __init__(self, db: AsyncSession, repo: ProductVariantRepository):
        self.db = db
        self.repo = repo

    async def get_all(self, product_id: int, company_id: int) -> list[ProductVariant]:
        return await self.repo.get_all(product_id, company_id)

    async def get_by_id(
        self, variant_id: int, product_id: int, company_id: int
    ) -> ProductVariant:
        obj = await self.repo.get_by_id(variant_id, product_id, company_id)
        if not obj:
            raise HTTPException(404, f"Variant id={variant_id} not found.")
        return obj




    async def create(
        self, product_id: int,
        data: ProductVariantCreate, 
        company_id: int
    ) -> ProductVariant:
        # guard duplicate SKU
        if data.sku:
            existing = await self.repo.get_by_sku(product_id, data.sku)
            if existing:
                raise HTTPException(409, f"SKU '{data.sku}' already exists for this product.")
        return await self.repo.create({
            **data.model_dump(),
            "product_id": product_id,
        })





    async def update(
        self,
        variant_id: int,
        product_id: int,
        data:       ProductVariantUpdate,
        company_id: int,
    ) -> ProductVariant:
        obj = await self.get_by_id(variant_id, product_id, company_id)
        # guard duplicate SKU on update
        if data.sku and data.sku != obj.sku:
            existing = await self.repo.get_by_sku(product_id, data.sku)
            if existing:
                raise HTTPException(409, f"SKU '{data.sku}' already exists for this product.")
        return await self.repo.update(obj, data.model_dump(exclude_none=True))





    async def delete(self, variant_id: int, product_id: int, company_id: int) -> None:
        obj = await self.get_by_id(variant_id, product_id, company_id)
        # delete all variant images from Cloudinary
        images = await self.repo.get_all_images(variant_id)
        for img in images:
            if img.image_public_id:
                await storage.delete_asset(img.image_public_id)
        await self.repo.delete(obj)




    # ── Variant Images ──────────────────────────────────────────────────────



    async def add_image(
        self,
        variant_id:  int,
        product_id:  int,
        company_id:  int,
        image:       UploadFile,
        is_primary:  bool = False,
        sort_order:  int  = 0,
    ) -> ProductImage:
        await self.get_by_id(variant_id, product_id, company_id)
        result = await storage.upload_image(
            image, folder=f"products/{company_id}/{product_id}/{variant_id}"
        )
        return await self.repo.create_image({
            "product_id":      product_id,
            "company_id":      company_id,
            "variant_id":      variant_id,
            "image_url":       result["secure_url"],
            "image_public_id": result["public_id"],
            "is_primary":      is_primary,
            "sort_order":      sort_order,
        })
    



    

    async def set_primary_image(
        self,
        images_id:  int,
        variant_id: int,
        product_id: int,
        company_id: int,
    ) -> ProductImage:
        img = await self.repo.get_image_by_id(images_id, variant_id, company_id)
        if not img:
            raise HTTPException(404, f"Image id={images_id} not found.")
        await self.repo.clear_primary_flags(variant_id, company_id)
        return await self.repo.update_image(img, {"is_primary": True})




    async def delete_image(
        self,
        images_id:  int,
        variant_id: int,
        product_id: int,
        company_id: int,
    ) -> dict:
        img = await self.repo.get_image_by_id(images_id, variant_id, company_id)
        if not img:
            raise HTTPException(404, f"Image id={images_id} not found.")
        if img.image_public_id:
            await storage.delete_asset(img.image_public_id)
        await self.repo.delete_image(img)
        return {"message": f"Variant image id={images_id} deleted."}


async def get_product_variant_service(
    db: AsyncSession = Depends(get_db),
) -> ProductVariantService:
    return ProductVariantService(
        db=db,
        repo=ProductVariantRepository(db),
    )