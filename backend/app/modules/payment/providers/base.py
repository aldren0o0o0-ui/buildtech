from abc import ABC, abstractmethod
from typing import Any
from sqlalchemy.orm import Session

from app.modules.payment.models import Payment, PaymentMethod


class PaymentProvider(ABC):
    """
    Abstract base interface for payment providers.
    Establishes an extensible contract for Module 11 (Cash on Delivery)
    and future online payment gateways (GCash, Maya, Card, PayPal, Stripe)
    without modifying the payment core domain or order lifecycle.
    """

    @property
    @abstractmethod
    def method(self) -> PaymentMethod:
        pass

    @abstractmethod
    def create_payment(
        self,
        db: Session,
        order: Any,
        **kwargs: Any,
    ) -> Payment:
        """
        Creates an authoritative Payment entity associated with the given Order.
        Must be executed within the active database transaction.
        """
        pass

    @abstractmethod
    def mark_as_paid(
        self,
        db: Session,
        payment: Payment,
        **kwargs: Any,
    ) -> Payment:
        """
        Transitions payment from PENDING to PAID upon verification.
        """
        pass

    @abstractmethod
    def cancel_payment(
        self,
        db: Session,
        payment: Payment,
        **kwargs: Any,
    ) -> Payment:
        """
        Transitions payment from PENDING to CANCELLED upon order cancellation.
        """
        pass
