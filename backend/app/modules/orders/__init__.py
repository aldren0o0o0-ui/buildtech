"""
Orders & Checkout Feature Module (Module 7).
Handles customer checkout, atomic inventory deduction, immutable order snapshots,
order status transitions, cancellation, and administration.
"""

from app.modules.orders.models import (
    Order,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.modules.orders.routes import (
    admin_orders_router,
    checkout_router,
    customer_orders_router,
)

__all__ = [
    "Order",
    "OrderItem",
    "OrderStatus",
    "PaymentStatus",
    "PaymentMethod",
    "checkout_router",
    "customer_orders_router",
    "admin_orders_router",
]
