from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from app.schemas.schema import (
    ProductImageResponse,
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductVariantResponse,
)
from app.services.inventory.product_variant_service import ProductVariantService, get_product_variant_service
from app.utils.auth import require_login, require_manager

variant_router = APIRouter(prefix="/products/{product_id}/variants",tags=["Product Variants"],)


@variant_router.get("/", response_model=list[ProductVariantResponse])



async def list_variants(
    product_id:   int,
    current_user: dict                  = Depends(require_login),
    service:      ProductVariantService = Depends(get_product_variant_service),
):
    return await service.get_all(product_id, int(current_user["company_id"]))


@variant_router.get(
    "/{variant_id}", 
    response_model=ProductVariantResponse
)
async def get_variant(
    product_id:   int,
    variant_id:   int,
    current_user: dict                  = Depends(require_login),
    service:      ProductVariantService = Depends(get_product_variant_service),
):
    return await service.get_by_id(variant_id, product_id, int(current_user["company_id"]))






@variant_router.post(
        "/", 
        response_model=ProductVariantResponse, 
        status_code=status.HTTP_201_CREATED
    )
async def create_variant(
    product_id:   int,
    data:         ProductVariantCreate,
    current_user: dict                  = Depends(require_manager),
    service:      ProductVariantService = Depends(get_product_variant_service),
):
    return await service.create(product_id, data, int(current_user["company_id"]))






@variant_router.patch("/{variant_id}", response_model=ProductVariantResponse)
async def update_variant(
    product_id:   int,
    variant_id:   int,
    data:         ProductVariantUpdate,
    current_user: dict                  = Depends(require_manager),
    service:      ProductVariantService = Depends(get_product_variant_service),
):
    return await service.update(variant_id, product_id, data, int(current_user["company_id"]))






@variant_router.delete("/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(
    product_id:   int,
    variant_id:   int,
    current_user: dict                  = Depends(require_manager),
    service:      ProductVariantService = Depends(get_product_variant_service),
):
    await service.delete(variant_id, product_id, int(current_user["company_id"]))




# --- Variant Images ---

@variant_router.post(
    "/{variant_id}/images",
    response_model=ProductImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload variant image",
)
async def add_variant_image(
    product_id:   int,
    variant_id:   int,
    image:        UploadFile            = File(...),
    is_primary:   bool                  = Form(False),
    sort_order:   int                   = Form(0),
    current_user: dict                  = Depends(require_manager),
    service:      ProductVariantService = Depends(get_product_variant_service),
):
    return await service.add_image(
        variant_id, product_id, int(current_user["company_id"]), image, is_primary, sort_order
    )


    


@variant_router.patch(
    "/{variant_id}/images/{images_id}/set-primary",
    response_model=ProductImageResponse,
    summary="Set primary variant image",
)
async def set_primary_variant_image(
    product_id:   int,
    variant_id:   int,
    images_id:    int,
    current_user: dict                  = Depends(require_manager),
    service:      ProductVariantService = Depends(get_product_variant_service),
):
    return await service.set_primary_image(
        images_id, variant_id, product_id, int(current_user["company_id"])
    )


@variant_router.delete(
    "/{variant_id}/images/{images_id}",
    summary="Delete variant image",
)
async def delete_variant_image(
    product_id:   int,
    variant_id:   int,
    images_id:    int,
    current_user: dict                  = Depends(require_manager),
    service:      ProductVariantService = Depends(get_product_variant_service),
):
    return await service.delete_image(
        images_id, variant_id, product_id, int(current_user["company_id"])
    )