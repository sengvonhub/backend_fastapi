from fastapi import APIRouter

from .quotation_router import quotation_router

quotations_route = APIRouter()
quotations_route.include_router(quotation_router,  tags=["Quotations"])