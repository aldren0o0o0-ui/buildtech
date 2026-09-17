from datetime import datetime, timezone
import secrets
from typing import Any
from app.core import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.payment.models import Payment, PaymentMethod, PaymentStatus
from app.modules.payment.providers.base import PaymentProvider


def generate_unique_payment_reference(db: Session) -> str:
    """
    Generates a unique, server-controlled payment reference.
    Format: PAY-YYYYMMDD-XXXXXX (e.g. PAY-20260912-8F31A2).
    Checks database for uniqueness.
    """
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    for _ in range(10):
        suffix = secrets.token_hex(3).upper()
        reference = f"PAY-{date_str}-{suffix}"
        existing = (
            db.query(Payment.id)
            .filter(Payment.payment_reference == reference)
            .first()
        )
        if not existing:
            return reference

    # Fallback if high contention
    micro_suffix = datetime.now(timezone.utc).strftime("%H%M%S%f")[:6]
    return f"PAY-{date_str}-{micro_suffix}"


class CashOnDeliveryProvider(PaymentProvider):
    """
    Cash on Delivery (COD) payment provider.
    Payment is collected in physical cash upon parcel arrival.
    Initial status is strictly PENDING.
    Only authorized administrators can transition COD to PAID upon collection.
    No external network calls or artificial transaction IDs are generated.
    """

    @property
    def method(self) -> PaymentMethod:
        return PaymentMethod.CASH_ON_DELIVERY

    def create_payment(
        self,
        db: Session,
        order: Any,
        **kwargs: Any,
    ) -> Payment:
        # Check if payment already exists for this order (idempotency guard)
        existing = (
            db.query(Payment)
            .filter(Payment.order_id == order.id)
            .first()
        )
        if existing:
            return existing

        reference = generate_unique_payment_reference(db)

        payment = Payment(
            order_id=order.id,
            payment_reference=reference,
            method=PaymentMethod.CASH_ON_DELIVERY.value,
            status=PaymentStatus.PENDING.value,
            amount=order.total_amount,
            currency="PHP",
            provider="COD",
            provider_payment_id=None,
        )
        db.add(payment)
        db.flush()
        return payment

    def mark_as_paid(
        self,
        db: Session,
        payment: Payment,
        **kwargs: Any,
    ) -> Payment:
        if payment.status != PaymentStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot mark payment as paid from status '{payment.status}'. Only PENDING payments can be marked as paid.",
            )

        payment.status = PaymentStatus.PAID.value
        payment.paid_at = datetime.now(timezone.utc)
        return payment

    def cancel_payment(
        self,
        db: Session,
        payment: Payment,
        **kwargs: Any,
    ) -> Payment:
        if payment.status != PaymentStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel payment in status '{payment.status}'. Only PENDING payments can be cancelled.",
            )

        payment.status = PaymentStatus.CANCELLED.value
        payment.cancelled_at = datetime.now(timezone.utc)
        return payment
