from typing import Optional
from app.core import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.payment.schemas import (
    PaymentAdminRead,
    PaymentListResponse,
    PaymentRead,
    PaymentStatusUpdate,
)
from app.modules.payment.service import PaymentService
from app.modules.users.models import User, UserRole


def require_customer(current_user: User = Depends(get_current_user)) -> User:
    """Ensures the authenticated user has customer privileges."""
    if current_user.role != UserRole.CUSTOMER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Customer privileges required.",
        )
    return current_user


# Customer payment endpoints (scoped under /api/v1/orders/{order_id}/payment)
customer_payments_router = APIRouter(prefix="/orders", tags=["Customer Payments"])

# Administrative payment endpoints (/api/v1/admin/payments)
admin_payments_router = APIRouter(prefix="/admin/payments", tags=["Admin Payments"])


# ---------------------------------------------------------------------------
# Customer Endpoints
# ---------------------------------------------------------------------------

@customer_payments_router.get(
    "/{order_identifier}/payment",
    response_model=PaymentRead,
    summary="Get payment details for customer order",
)
def get_order_payment(
    order_identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    """
    Returns payment details for an order owned by the authenticated customer.
    Returns 404 if the order does not exist or belongs to another user.
    """
    return PaymentService.get_customer_payment(
        db=db,
        user=current_user,
        order_identifier=order_identifier,
    )


# ---------------------------------------------------------------------------
# Administrative Endpoints
# ---------------------------------------------------------------------------

@admin_payments_router.get(
    "",
    response_model=PaymentListResponse,
    summary="List all payments with filters and pagination",
)
def admin_list_payments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by payment status"),
    method: Optional[str] = Query(None, description="Filter by payment method"),
    search: Optional[str] = Query(None, description="Search reference, order, or customer"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Lists paginated payment records for administrative auditing and reconciliation.
    """
    return PaymentService.admin_list_payments(
        db=db,
        page=page,
        page_size=page_size,
        status_filter=status,
        method_filter=method,
        search=search,
    )


@admin_payments_router.get(
    "/{payment_id}",
    response_model=PaymentAdminRead,
    summary="Get administrative payment details",
)
def admin_get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Retrieves full payment record including provider metadata.
    """
    return PaymentService.admin_get_payment(db=db, payment_id=payment_id)


@admin_payments_router.post(
    "/{payment_id}/mark-paid",
    response_model=PaymentAdminRead,
    summary="Mark COD payment as collected and paid",
)
def admin_mark_cod_paid(
    payment_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Explicit action for administrators to mark a Cash on Delivery payment as collected.
    Transitions payment status from PENDING to PAID and records paid_at.
    """
    return PaymentService.admin_mark_cod_paid(
        db=db,
        admin_user=current_admin,
        payment_id=payment_id,
    )


@admin_payments_router.patch(
    "/{payment_id}/status",
    response_model=PaymentAdminRead,
    summary="Update payment status via state machine",
)
def admin_update_payment_status(
    payment_id: int,
    payload: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Applies validated state machine transition to a payment.
    Rejects illegal transitions with 400 Bad Request.
    """
    return PaymentService.admin_update_payment_status(
        db=db,
        admin_user=current_admin,
        payment_id=payment_id,
        target_status=payload.status,
    )
