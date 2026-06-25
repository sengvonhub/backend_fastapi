from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, status
from app.schemas.schema import CategoryBrief, SupplierProductPriceCreate, SupplierProductPriceUpdate, SupplierProductPriceResponse
from app.services.inventory.supplier_product_price_service import SupplierProductPriceService, get_supplier_product_price_service
from app.utils.auth import require_manager
supplier_price_router = APIRouter(prefix="/supplier-prices", tags=["Supplier Product Prices"])


@supplier_price_router.get("/", response_model=list[SupplierProductPriceResponse])
async def list_prices(
    supplier_id:  Optional[int] = None,
    variant_id:   Optional[int] = None,
    current_user: dict = Depends(require_manager),
    service:      SupplierProductPriceService = Depends(get_supplier_product_price_service),
):
    return await service.get_all(int(current_user["company_id"]), supplier_id, variant_id)




@supplier_price_router.get("/{price_id}", response_model=SupplierProductPriceResponse)
async def get_price(
    price_id:     int,
    current_user: dict = Depends(require_manager),
    service:      SupplierProductPriceService = Depends(get_supplier_product_price_service),
):
    return await service.get_by_id(price_id, int(current_user["company_id"]))





@supplier_price_router.post("/", response_model=SupplierProductPriceResponse, status_code=status.HTTP_201_CREATED)
async def create_price(
    data:         SupplierProductPriceCreate,
    current_user: dict = Depends(require_manager),
    service:      SupplierProductPriceService = Depends(get_supplier_product_price_service),
):
    return await service.create(data, int(current_user["company_id"]))







@supplier_price_router.patch("/{price_id}", response_model=SupplierProductPriceResponse)
async def update_price(
    price_id:     int,
    data:         SupplierProductPriceUpdate,
    current_user: dict = Depends(require_manager),
    service:      SupplierProductPriceService = Depends(get_supplier_product_price_service),
):
    return await service.update(price_id, data, int(current_user["company_id"]))


@supplier_price_router.delete("/{price_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_price(
    price_id:     int,
    current_user: dict = Depends(require_manager),
    service:      SupplierProductPriceService = Depends(get_supplier_product_price_service),
):
    return await service.delete(price_id, int(current_user["company_id"]))




@supplier_price_router.get("/by-supplier/{supplier_id}/categories", response_model=list[CategoryBrief])
async def get_supplier_categories(
    supplier_id: int,
    company_id:  int = Depends(require_manager),
    service:     SupplierProductPriceService = Depends(get_supplier_product_price_service),
):
    return await service.get_categories_by_supplier(supplier_id, int(company_id["company_id"]))