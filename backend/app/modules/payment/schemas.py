from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.modules.payment.models import PaymentMethod, PaymentStatus


class PaymentRead(BaseModel):
    id: int
    order_id: int
    order_number: Optional[str] = None
    payment_reference: str
    method: str
    status: str
    amount: Decimal
    currency: str
    paid_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentAdminRead(PaymentRead):
    provider: str
    provider_payment_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus = Field(..., description="Target payment status transition")
    notes: Optional[str] = Field(None, max_length=500, description="Optional administrative notes")

    model_config = ConfigDict(extra="forbid")


class PaymentListResponse(BaseModel):
    items: List[PaymentAdminRead]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)
