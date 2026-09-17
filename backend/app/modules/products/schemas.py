from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.products.models import ProductStatus


class ProductCategoryNestedResponse(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class ProductBrandNestedResponse(BaseModel):
    id: int
    name: str
    slug: str
    logo_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductCreateRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    category_id: int = Field(..., gt=0)
    brand_id: int = Field(..., gt=0)
    price: Decimal = Field(..., ge=0, decimal_places=2, max_digits=10)
    image_url: Optional[str] = Field(None, max_length=500)
    status: Optional[ProductStatus] = ProductStatus.ACTIVE
    is_active: Optional[bool] = True

    @field_validator("sku", "name", mode="before")
    @classmethod
    def strip_required_strings(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty or whitespace only.")
        return v

    @field_validator("description", "image_url", mode="before")
    @classmethod
    def strip_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v = v.strip()
            if not v:
                return None
        return v

    model_config = ConfigDict(extra="forbid")


class ProductUpdateRequest(BaseModel):
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    category_id: Optional[int] = Field(None, gt=0)
    brand_id: Optional[int] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2, max_digits=10)
    image_url: Optional[str] = Field(None, max_length=500)
    status: Optional[ProductStatus] = None
    is_active: Optional[bool] = None

    @field_validator("sku", "name", mode="before")
    @classmethod
    def strip_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty or whitespace only.")
        return v

    @field_validator("description", "image_url", mode="before")
    @classmethod
    def strip_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v = v.strip()
            if not v:
                return None
        return v

    model_config = ConfigDict(extra="forbid")


class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    slug: str
    description: Optional[str] = None
    category_id: int
    brand_id: int
    price: Decimal
    image_url: Optional[str] = None
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[ProductCategoryNestedResponse] = None
    brand: Optional[ProductBrandNestedResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProductPaginationResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    pages: int

    model_config = ConfigDict(from_attributes=True)
