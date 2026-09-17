from datetime import datetime, timezone
from decimal import Decimal
import math
from typing import Any, Dict, List, Optional
from app.core import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.orders.models import Order, PaymentStatus as OrderPaymentStatus
from app.modules.payment.models import Payment, PaymentMethod, PaymentStatus
from app.modules.payment.providers.base import PaymentProvider
from app.modules.payment.providers.cod import CashOnDeliveryProvider
from app.modules.payment.repository import PaymentRepository
from app.modules.payment.schemas import PaymentAdminRead, PaymentListResponse, PaymentRead
from app.modules.users.models import User, UserRole


ALLOWED_PAYMENT_TRANSITIONS: Dict[str, set] = {
    PaymentStatus.PENDING.value: {
        PaymentStatus.PAID.value,
        PaymentStatus.FAILED.value,
        PaymentStatus.CANCELLED.value,
    },
    PaymentStatus.FAILED.value: {
        PaymentStatus.PENDING.value,
    },
    PaymentStatus.PAID.value: {
        PaymentStatus.REFUNDED.value,
    },
    PaymentStatus.CANCELLED.value: {
        PaymentStatus.PENDING.value,
    },
    PaymentStatus.REFUNDED.value: set(),
}


class PaymentService:
    """
    Core business logic and state machine enforcement for the Payment domain.
    Coordinates between providers, order synchronization, and administrative workflows.
    """

    _providers: Dict[str, PaymentProvider] = {
        PaymentMethod.CASH_ON_DELIVERY.value: CashOnDeliveryProvider(),
        PaymentMethod.COD.value: CashOnDeliveryProvider(),
    }

    @classmethod
    def get_provider(cls, method_name: str) -> PaymentProvider:
        normalized = method_name.strip().upper() if method_name else ""
        provider = cls._providers.get(normalized)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported payment method: '{method_name}'. Supported method in Module 11: CASH_ON_DELIVERY.",
            )
        return provider

    @classmethod
    def create_payment_for_order(
        cls,
        db: Session,
        order: Order,
        method: Any = PaymentMethod.CASH_ON_DELIVERY,
    ) -> Payment:
        """
        Creates an authoritative payment record atomically inside the order checkout transaction.
        Amount is strictly derived from order.total_amount.
        """
        method_str = method.value if hasattr(method, "value") else str(method)
        provider = cls.get_provider(method_str)
        return provider.create_payment(db, order)

    @classmethod
    def get_customer_payment(
        cls,
        db: Session,
        user: User,
        order_identifier: str,
    ) -> PaymentRead:
        """
        Returns payment details for an order owned by the authenticated customer.
        Returns 404 if the order does not exist or belongs to another user.
        """
        payment = PaymentRepository.get_customer_payment(db, user.id, order_identifier)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found for the specified order.",
            )

        return PaymentRead(
            id=payment.id,
            order_id=payment.order_id,
            order_number=payment.order.order_number if payment.order else None,
            payment_reference=payment.payment_reference,
            method=payment.method,
            status=payment.status,
            amount=payment.amount,
            currency=payment.currency,
            paid_at=payment.paid_at,
            failed_at=payment.failed_at,
            cancelled_at=payment.cancelled_at,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )

    @classmethod
    def admin_list_payments(
        cls,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[str] = None,
        method_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaymentListResponse:
        """
        Administrative paginated listing of all payments with search and filtering.
        """
        items, total = PaymentRepository.list_payments(
            db,
            page=page,
            page_size=page_size,
            status=status_filter,
            method=method_filter,
            search=search,
        )

        read_items = [
            PaymentAdminRead(
                id=p.id,
                order_id=p.order_id,
                order_number=p.order.order_number if p.order else None,
                payment_reference=p.payment_reference,
                method=p.method,
                status=p.status,
                amount=p.amount,
                currency=p.currency,
                provider=p.provider,
                provider_payment_id=p.provider_payment_id,
                customer_name=p.order.customer_name if p.order else None,
                customer_email=p.order.customer_email if p.order else None,
                paid_at=p.paid_at,
                failed_at=p.failed_at,
                cancelled_at=p.cancelled_at,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in items
        ]

        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return PaymentListResponse(
            items=read_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @classmethod
    def admin_get_payment(
        cls,
        db: Session,
        payment_id: int,
    ) -> PaymentAdminRead:
        """
        Administrative retrieval of payment record with full provider metadata.
        """
        payment = PaymentRepository.get_by_id(db, payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment #{payment_id} not found.",
            )

        return PaymentAdminRead(
            id=payment.id,
            order_id=payment.order_id,
            order_number=payment.order.order_number if payment.order else None,
            payment_reference=payment.payment_reference,
            method=payment.method,
            status=payment.status,
            amount=payment.amount,
            currency=payment.currency,
            provider=payment.provider,
            provider_payment_id=payment.provider_payment_id,
            customer_name=payment.order.customer_name if payment.order else None,
            customer_email=payment.order.customer_email if payment.order else None,
            paid_at=payment.paid_at,
            failed_at=payment.failed_at,
            cancelled_at=payment.cancelled_at,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )

    @classmethod
    def admin_mark_cod_paid(
        cls,
        db: Session,
        admin_user: User,
        payment_id: int,
    ) -> PaymentAdminRead:
        """
        Explicit administrative action to record physical cash collection for COD orders.
        Requires ADMIN role, PENDING status, and CASH_ON_DELIVERY method.
        Sets paid_at and synchronizes order.payment_status to PAID.
        """
        if admin_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can mark payments as paid.",
            )

        payment = PaymentRepository.get_by_id(db, payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment #{payment_id} not found.",
            )

        if payment.method not in (
            PaymentMethod.CASH_ON_DELIVERY.value,
            PaymentMethod.COD.value,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mark as Paid endpoint is only for Cash on Delivery. Current method is '{payment.method}'.",
            )

        if payment.status != PaymentStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment is already in status '{payment.status}'. Only PENDING payments can be marked as paid.",
            )

        provider = cls.get_provider(payment.method)
        provider.mark_as_paid(db, payment)

        # Synchronize order payment status for backward compatibility
        if payment.order:
            payment.order.payment_status = OrderPaymentStatus.PAID.value

        db.commit()
        db.refresh(payment)
        return cls.admin_get_payment(db, payment.id)

    @classmethod
    def admin_update_payment_status(
        cls,
        db: Session,
        admin_user: User,
        payment_id: int,
        target_status: PaymentStatus,
    ) -> PaymentAdminRead:
        """
        Administrative state machine transition with strict validation.
        Rejects invalid transitions (e.g. PAID -> PENDING, REFUNDED -> PAID).
        """
        if admin_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can update payment status.",
            )

        payment = PaymentRepository.get_by_id(db, payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment #{payment_id} not found.",
            )

        current_status = payment.status
        desired_status = target_status.value

        if current_status == desired_status:
            return cls.admin_get_payment(db, payment.id)

        allowed = ALLOWED_PAYMENT_TRANSITIONS.get(current_status, set())
        if desired_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid payment status transition: '{current_status}' -> '{desired_status}'. "
                    f"Allowed transitions from '{current_status}': {sorted(list(allowed))}."
                ),
            )

        payment.status = desired_status
        now = datetime.now(timezone.utc)

        if desired_status == PaymentStatus.PAID.value:
            payment.paid_at = now
        elif desired_status == PaymentStatus.CANCELLED.value:
            payment.cancelled_at = now
        elif desired_status == PaymentStatus.FAILED.value:
            payment.failed_at = now

        # Synchronize order payment status
        if payment.order:
            if hasattr(OrderPaymentStatus, desired_status):
                payment.order.payment_status = desired_status

        db.commit()
        db.refresh(payment)
        return cls.admin_get_payment(db, payment.id)
