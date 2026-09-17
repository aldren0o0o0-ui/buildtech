from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductAvailabilityResponse(BaseModel):
    product_id: int
    availability: str
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class InventoryCompactProduct(BaseModel):
    id: int
    name: str
    sku: str
    category_name: Optional[str] = None
    brand_name: Optional[str] = None
    status: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class InventoryResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    reserved_quantity: int
    available_quantity: int
    low_stock_threshold: int
    availability_status: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryAdminResponse(BaseModel):
    id: int
    product_id: int
    product: Optional[InventoryCompactProduct] = None
    quantity: int
    reserved_quantity: int
    available_quantity: int
    low_stock_threshold: int
    availability_status: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryStockInRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Positive number of stock units received")
    reason: Optional[str] = Field(None, max_length=255)

    @field_validator("reason", mode="before")
    @classmethod
    def strip_reason(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v = v.strip()
            if not v:
                return None
        return v

    model_config = ConfigDict(extra="forbid")


class InventoryAdjustmentRequest(BaseModel):
    type: str = Field(..., pattern="^(ADJUSTMENT_IN|ADJUSTMENT_OUT)$", description="Direction of adjustment")
    quantity: int = Field(..., gt=0, description="Positive count of units to adjust")
    reason: Optional[str] = Field(None, max_length=255)

    @field_validator("reason", mode="before")
    @classmethod
    def strip_reason(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v = v.strip()
            if not v:
                return None
        return v

    model_config = ConfigDict(extra="forbid")


class InventoryThresholdUpdateRequest(BaseModel):
    low_stock_threshold: int = Field(..., ge=0, description="Minimum available units before triggering LOW_STOCK alert")

    model_config = ConfigDict(extra="forbid")


class InventoryTransactionResponse(BaseModel):
    id: int
    product_id: int
    inventory_id: int
    type: str
    quantity_change: int
    quantity_before: int
    quantity_after: int
    reason: Optional[str] = None
    created_by_user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
