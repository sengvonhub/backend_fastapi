from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.models.category import Category
from app.repositories.inventory.supplier_product_price_repo import SupplierProductPriceRepository
from app.schemas.schema import SupplierProductPriceCreate, SupplierProductPriceUpdate
from app.models.supplier.supplier_product_price import SupplierProductPrice


class SupplierProductPriceService:
    def __init__(self, db: AsyncSession, repo: SupplierProductPriceRepository):
        self.db = db
        self.repo = repo

    async def get_all(
        self,
        company_id:  int,
        supplier_id: int | None = None,
        variant_id:  int | None = None,
    ) -> list[SupplierProductPrice]:
        return await self.repo.get_all(company_id, supplier_id, variant_id)

    async def get_by_id(self, price_id: int, company_id: int) -> SupplierProductPrice:
        obj = await self.repo.get_by_id(price_id, company_id)
        if not obj:
            raise HTTPException(404, f"Price id={price_id} not found.")
        return obj
    


    async def create(
        self,
        data: SupplierProductPriceCreate,
        company_id: int,
    ) -> SupplierProductPrice:
        existing = await self.repo.get_by_supplier_variant(
            data.supplier_id, data.variant_id
        )
        if existing:
            raise HTTPException(409, "Price for this supplier+variant already exists.")
        # return await self.repo.create({**data.model_dump(), "company_id": company_id})
        return await self.repo.create(data.model_dump(), company_id)




    async def update(
        self,
        price_id:   int,
        data:       SupplierProductPriceUpdate,
        company_id: int,
    ) -> SupplierProductPrice:
        obj = await self.get_by_id(price_id, company_id)
        return await self.repo.update(obj, data.model_dump(exclude_none=True))

    async def delete(self, price_id: int, company_id: int) -> None:
        obj = await self.get_by_id(price_id, company_id)
        await self.repo.delete(obj)


    async def get_categories_by_supplier(
        self,
        supplier_id: int,
        company_id:  int,
    ) -> list[Category]:
        return await self.repo.get_categories_by_supplier(supplier_id, company_id)

        

async def get_supplier_product_price_service(
    db: AsyncSession = Depends(get_db),
) -> SupplierProductPriceService:
    return SupplierProductPriceService(
        db=db,
        repo=SupplierProductPriceRepository(db),
    )



