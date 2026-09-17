from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CartItemAddRequest(BaseModel):
    product_id: int = Field(..., description="ID of the active product to add")
    quantity: int = Field(1, ge=1, description="Quantity of units to add (must be at least 1)")

    model_config = ConfigDict(extra="forbid")


class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(..., ge=1, description="New quantity for this cart item (must be at least 1)")

    model_config = ConfigDict(extra="forbid")


class CartProductBrand(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CartProductResponse(BaseModel):
    id: int
    name: str
    slug: str
    sku: str
    price: Decimal
    image_url: Optional[str] = None
    brand: Optional[CartProductBrand] = None

    model_config = ConfigDict(from_attributes=True)


class CartItemResponse(BaseModel):
    id: int
    product: CartProductResponse
    quantity: int
    available_quantity: int
    is_available: bool
    availability_status: str
    availability_reason: Optional[str] = None
    item_subtotal: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: int
    items: List[CartItemResponse]
    subtotal: Decimal
    item_count: int
    total_quantity: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
