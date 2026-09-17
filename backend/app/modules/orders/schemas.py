from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.orders.models import OrderStatus, PaymentMethod, PaymentStatus


class OrderCreateRequest(BaseModel):
    address_id: Optional[int] = Field(
        None, description="ID of a saved customer shipping address from Module 9"
    )

    # Direct address fields (optional if address_id is provided)
    customer_name: Optional[str] = Field(
        None, min_length=2, max_length=200, description="Full name of customer / recipient"
    )
    customer_email: Optional[EmailStr] = Field(
        None, description="Email address for order confirmation"
    )
    customer_phone: Optional[str] = Field(
        None, min_length=7, max_length=50, description="Contact phone number"
    )

    shipping_address_line1: Optional[str] = Field(
        None, min_length=3, max_length=255, description="Street address"
    )
    shipping_address_line2: Optional[str] = Field(
        None, max_length=255, description="Apartment, suite, unit, etc."
    )
    shipping_barangay: Optional[str] = Field(
        None, max_length=100, description="Barangay / District"
    )
    shipping_city: Optional[str] = Field(
        None, min_length=2, max_length=100, description="City / Municipality"
    )
    shipping_province: Optional[str] = Field(
        None, min_length=2, max_length=100, description="Province / State / Region"
    )
    shipping_postal_code: Optional[str] = Field(
        None, min_length=2, max_length=20, description="Postal code"
    )
    shipping_country: Optional[str] = Field(
        "Philippines", min_length=2, max_length=100, description="Destination country"
    )

    notes: Optional[str] = Field(
        None, max_length=1000, description="Optional customer delivery instructions"
    )
    payment_method: PaymentMethod = Field(
        default=PaymentMethod.COD, description="Payment method"
    )
    idempotency_key: Optional[str] = Field(
        None, max_length=100, description="Optional client idempotency key"
    )

    model_config = ConfigDict(extra="forbid")


class CheckoutRequest(OrderCreateRequest):
    pass


class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_id: Optional[int] = None
    product_name: str
    product_sku: str
    sku: Optional[str] = None
    product_slug: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: Optional[int] = None

    status: str
    payment_method: str
    payment_status: str

    subtotal: Decimal
    shipping_fee: Decimal
    total_amount: Decimal

    customer_name: str
    customer_email: str
    customer_phone: str

    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None

    shipping_address_line1: str
    shipping_address_line2: Optional[str] = None
    shipping_barangay: Optional[str] = None
    shipping_city: str
    shipping_province: str
    shipping_postal_code: str
    shipping_country: str

    notes: Optional[str] = None
    idempotency_key: Optional[str] = None

    items: List[OrderItemResponse]
    payment: Optional["PaymentRead"] = None

    created_at: datetime
    updated_at: datetime
    cancelled_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


from app.modules.payment.schemas import PaymentRead
OrderResponse.model_rebuild()


class CheckoutResponse(OrderResponse):
    pass


class OrderListResponse(BaseModel):
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatus = Field(..., description="Target status transition")

    model_config = ConfigDict(extra="forbid")

