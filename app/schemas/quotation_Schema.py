from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.quotation_status import ArtworkStatus, DeliveryMethod, QuotationStatus



class QuotationItemPriceTierCreate(BaseModel):
    quantity: int
    unit_price: Decimal
    sort_order: int = 0


class QuotationItemPriceTierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)   
    tier_id: int
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    sort_order: int
# ===========================================================================
# QuotationItem
# ===========================================================================
class QuotationItemCreate(BaseModel):
    sort_order:   int
    item_name:    str
    size:         Optional[str] = None
    pages:        Optional[int] = None
    print_side:   Optional[str] = None
    color_spec:   Optional[str] = None
    paper_cover:  Optional[str] = None
    paper_inside: Optional[str] = None
    finishing:    Optional[str] = None
    language:     Optional[str] = None
    quantity:     int
    unit_price:   Decimal
    note:         Optional[str] = None
    price_tiers:  Optional[list["QuotationItemPriceTierCreate"]] = None


class QuotationItemUpdate(BaseModel):
    sort_order:   Optional[int] = None
    item_name:    Optional[str] = None
    size:         Optional[str] = None
    pages:        Optional[int] = None
    print_side:   Optional[str] = None
    color_spec:   Optional[str] = None
    paper_cover:  Optional[str] = None
    paper_inside: Optional[str] = None
    finishing:    Optional[str] = None
    language:     Optional[str] = None
    quantity:     Optional[int] = None
    unit_price:   Optional[Decimal] = None
    note:         Optional[str] = None
    price_tiers:  Optional[list["QuotationItemPriceTierCreate"]] = None


class QuotationItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id:      int
    company_id:   int
    quotation_id: Optional[int] = None
    sort_order:   int
    item_name:    str
    size:         Optional[str] = None
    pages:        Optional[int] = None
    print_side:   Optional[str] = None
    color_spec:   Optional[str] = None
    paper_cover:  Optional[str] = None
    paper_inside: Optional[str] = None
    finishing:    Optional[str] = None
    language:     Optional[str] = None
    quantity:     int
    unit_price:   Decimal
    total_price:  Decimal
    note:         Optional[str] = None
    price_tiers:  list["QuotationItemPriceTierResponse"] = []


# ===========================================================================
# Quotation
# ===========================================================================

class QuotationCreate(BaseModel):
    customer_id:     Optional[int] = None
    staff_id:        Optional[int] = None
    ref_number:      str
    quotation_date:  date
    expiry_date:     Optional[date] = None
    production_days: Optional[int] = None
    artwork_status:  Optional[ArtworkStatus] = None
    payment_terms:   Optional[str] = None
    delivery_method: Optional[DeliveryMethod] = None
    discount:        Decimal = Decimal("0")
    tax:             Decimal = Decimal("0")
    note:            Optional[str] = None
    items:           list[QuotationItemCreate] = []


class QuotationUpdate(BaseModel):
    customer_id:     Optional[int] = None
    staff_id:        Optional[int] = None
    ref_number:      Optional[str] = None
    quotation_date:  Optional[date] = None
    expiry_date:     Optional[date] = None
    production_days: Optional[int] = None
    artwork_status:  Optional[ArtworkStatus] = None
    payment_terms:   Optional[str] = None
    delivery_method: Optional[DeliveryMethod] = None
    subtotal:        Optional[Decimal] = None
    discount:        Optional[Decimal] = None
    tax:             Optional[Decimal] = None
    note:            Optional[str] = None


class QuotationStatusUpdateRequest(BaseModel):
    status: QuotationStatus   # "draft" | "sent" | "accepted"
    note:   Optional[str] = None



    


class QuotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    quotation_id:    int
    company_id:      int
    customer_name:   Optional[str] = None   # NEW
    customer_phone:  Optional[str] = None   # NEW
    customer_id:     Optional[int] = None
    staff_id:        Optional[int] = None
    ref_number:      str
    quotation_date:  date
    expiry_date:     Optional[date] = None
    status:          str
    production_days: Optional[int] = None
    artwork_status:  Optional[str] = None
    payment_terms:   Optional[str] = None
    delivery_method: Optional[str] = None
    subtotal:        Decimal
    discount:        Decimal
    tax:             Decimal
    total_amount:    Decimal
    invoice_id:      Optional[int] = None
    note:            Optional[str] = None
    created_by:      Optional[int] = None
    created_at:      datetime
    updated_at:      datetime
    items:           list[QuotationItemResponse] = []

    @model_validator(mode="before")
    @classmethod
    def _flatten_customer(cls, obj):

        customer = getattr(obj, "customer", None)
        if customer is None:
            return obj
        data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        data["items"] = obj.items
        data["customer_name"] = customer.name
        data["customer_phone"] = getattr(customer, "phone", None)
        return data


class QuotationStaffGroupResponse(BaseModel):
    staff_id:   int
    user_id:    int
    username:   str
    full_name:  str
    quotations: list[QuotationResponse]


class QuotationSummaryResponse(BaseModel):
    total_quotations: int
    total_draft:      int
    total_sent:       int
    total_accepted:   int
    total_amount:     Decimal

# //////////////////////////////////////////////////////////
# 
# //////////////////////////////////////////////////////////

