from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DashboardOverviewMetrics(BaseModel):
    total_revenue: str
    pending_payment: str
    total_order_value: str
    total_orders: int
    total_customers: int
    active_customers: int
    total_products: int
    active_products: int

    model_config = ConfigDict(from_attributes=True)


class OrderStatusCounts(BaseModel):
    pending: int = 0
    confirmed: int = 0
    processing: int = 0
    shipped: int = 0
    delivered: int = 0
    ready_for_fulfillment: int = 0
    completed: int = 0
    cancelled: int = 0
    total: int = 0

    model_config = ConfigDict(from_attributes=True)


class LowStockProductItem(BaseModel):
    product_id: int
    name: str
    sku: str
    category_name: Optional[str] = None
    quantity: int
    reserved_quantity: int
    available_quantity: int
    low_stock_threshold: int
    availability_status: str

    model_config = ConfigDict(from_attributes=True)


class TopSellingProductItem(BaseModel):
    product_id: int
    product_name: str
    product_sku: str
    units_sold: int
    total_sales: str

    model_config = ConfigDict(from_attributes=True)


class RecentOrderItem(BaseModel):
    id: int
    order_number: str
    customer_name: str
    customer_email: str
    total_amount: str
    status: str
    payment_status: str
    payment_method: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminDashboardResponse(BaseModel):
    overview: DashboardOverviewMetrics
    orders_by_status: OrderStatusCounts
    low_stock_products: List[LowStockProductItem]
    top_selling_products: List[TopSellingProductItem]
    recent_orders: List[RecentOrderItem]

    model_config = ConfigDict(from_attributes=True)
