from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.modules.addresses.schemas import AddressResponse


class CheckoutValidationRequest(BaseModel):
    address_id: int = Field(..., gt=0, description="Customer-owned shipping address ID")


class CheckoutIssue(BaseModel):
    code: str = Field(
        ...,
        description="Error or status code: EMPTY_CART, INSUFFICIENT_STOCK, OUT_OF_STOCK, PRODUCT_UNAVAILABLE, PRODUCT_NOT_FOUND",
    )
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    requested_quantity: Optional[int] = None
    available_quantity: Optional[int] = None
    message: str


class CheckoutItemPreview(BaseModel):
    cart_item_id: int
    product_id: int
    product_name: str
    sku: str
    quantity: int
    unit_price: Decimal
    item_subtotal: Decimal
    available_quantity: int
    is_available: bool
    status: str  # "AVAILABLE", "INSUFFICIENT_STOCK", "OUT_OF_STOCK", "PRODUCT_UNAVAILABLE"

    model_config = ConfigDict(from_attributes=True)


class CheckoutValidationResponse(BaseModel):
    valid: bool
    address: Optional[AddressResponse] = None
    items: List[CheckoutItemPreview] = []
    subtotal: Decimal = Decimal("0.00")
    shipping_fee: Decimal = Decimal("0.00")
    tax: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")
    issues: List[CheckoutIssue] = []

    model_config = ConfigDict(from_attributes=True)
