from typing import Optional
from app.core import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.orders.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    OrderCreateRequest,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdateRequest,
)
from app.modules.orders.service import OrderService
from app.modules.users.models import User, UserRole


def require_customer(current_user: User = Depends(get_current_user)) -> User:
    """Ensures the authenticated user has the CUSTOMER role."""
    if current_user.role != UserRole.CUSTOMER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Customer privileges required.",
        )
    return current_user


# Checkout Router (/api/v1/checkout)
checkout_router = APIRouter(prefix="/checkout", tags=["Checkout"])

# Customer Orders Router (/api/v1/orders)
customer_orders_router = APIRouter(prefix="/orders", tags=["Customer Orders"])

# Admin Orders Router (/api/v1/admin/orders)
admin_orders_router = APIRouter(prefix="/admin/orders", tags=["Admin Orders"])


# -------------------------------------------------------------------------
# Checkout Endpoints
# -------------------------------------------------------------------------

@checkout_router.post(
    "",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout customer cart and create order",
)
def checkout(
    payload: CheckoutRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Executes an atomic checkout of the customer's current shopping cart:
    - Row-locks relevant inventory rows
    - Validates product active status and stock
    - Computes authoritative price snapshots
    - Creates Order and OrderItem records
    - Deducts stock and logs SALE inventory transactions
    - Clears cart items
    - Commits in one transaction
    """
    return OrderService.checkout(
        db=db,
        user=current_user,
        checkout_data=payload,
        header_idempotency_key=idempotency_key,
    )


# -------------------------------------------------------------------------
# Customer Order Endpoints
# -------------------------------------------------------------------------

@customer_orders_router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create customer order",
)
def create_order(
    payload: OrderCreateRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Authoritative Module 10 Order Creation endpoint:
    - Supports referencing a saved address_id (Module 9) or explicit address fields
    - Locks inventory rows deterministically to prevent overselling
    - Authoritatively calculates subtotals, shipping fee, and grand total
    - Preserves immutable product and shipping destination snapshots
    - Atomically deducts inventory stock and logs SALE audit transaction
    - Clears cart items upon successful commitment
    """
    return OrderService.create_order(
        db=db,
        user=current_user,
        checkout_data=payload,
        header_idempotency_key=idempotency_key,
    )


@customer_orders_router.get(
    "",
    response_model=OrderListResponse,
    summary="List authenticated customer's orders",
)
def list_my_orders(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Returns a paginated list of orders placed by the current customer,
    sorted newest first.
    """
    return OrderService.list_customer_orders(
        db=db,
        user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )


@customer_orders_router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get customer order detail",
)
def get_my_order_detail(
    order_id: str,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Retrieves full details for an order owned by the authenticated customer.
    Supports either the integer ID or alphanumeric order number.
    Returns 404 if the order does not belong to this customer.
    """
    return OrderService.get_customer_order(
        db=db,
        user=current_user,
        order_identifier=order_id,
    )


@customer_orders_router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel customer order",
)
def cancel_my_order(
    order_id: str,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Allows a customer to cancel an order if it is still in PENDING or CONFIRMED status.
    Atomically restores inventory stock and logs a SALE_REVERSAL audit record.
    """
    return OrderService.cancel_order(
        db=db,
        user=current_user,
        order_identifier=order_id,
        is_admin=False,
    )


# -------------------------------------------------------------------------
# Admin Order Endpoints
# -------------------------------------------------------------------------

@admin_orders_router.get(
    "",
    response_model=OrderListResponse,
    summary="List all orders for administration",
)
def list_admin_orders(
    search: Optional[str] = Query(None, description="Search by order number or customer"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Lists orders across all customers with support for keyword search,
    order status filtering, payment status filtering, and pagination.
    """
    return OrderService.list_admin_orders(
        db=db,
        search=search,
        status_filter=status_filter,
        payment_status_filter=payment_status,
        page=page,
        page_size=page_size,
    )


@admin_orders_router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order detail for administration",
)
def get_admin_order_detail(
    order_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Retrieves full details of any order for administrative review.
    """
    return OrderService.get_admin_order(db=db, order_id=order_id)


@admin_orders_router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status (admin)",
)
def update_admin_order_status(
    order_id: int,
    payload: OrderStatusUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Transitions an order to a new status following strict business rules.
    If transitioned to CANCELLED, restores inventory and creates SALE_REVERSAL records.
    """
    return OrderService.update_order_status(
        db=db,
        admin_user=current_user,
        order_id=order_id,
        target_status=payload.status,
    )


@admin_orders_router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel order as administrator",
)
def cancel_admin_order(
    order_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Administrative order cancellation with full inventory recovery.
    """
    return OrderService.cancel_order(
        db=db,
        user=current_user,
        order_identifier=str(order_id),
        is_admin=True,
    )
