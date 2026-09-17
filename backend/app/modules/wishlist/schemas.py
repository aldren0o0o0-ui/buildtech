from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class WishlistProductBrand(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class WishlistProductCategory(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class WishlistProductResponse(BaseModel):
    id: int
    name: str
    slug: str
    sku: str
    price: Decimal
    image_url: Optional[str] = None
    status: str
    is_active: bool
    brand: Optional[WishlistProductBrand] = None
    category: Optional[WishlistProductCategory] = None
    availability_status: str  # "IN_STOCK", "OUT_OF_STOCK", "UNAVAILABLE"
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class WishlistItemResponse(BaseModel):
    id: int
    product_id: int
    product: WishlistProductResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WishlistResponse(BaseModel):
    id: int
    user_id: int
    items: List[WishlistItemResponse]
    item_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WishlistAddRequest(BaseModel):
    product_id: int = Field(..., description="ID of the published/active product to add to wishlist")

    model_config = ConfigDict(extra="forbid")


class WishlistCheckResponse(BaseModel):
    product_id: int
    is_wishlisted: bool
    wishlist_item_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
