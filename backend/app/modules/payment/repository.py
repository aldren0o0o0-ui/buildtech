import math
from typing import List, Optional, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.modules.orders.models import Order
from app.modules.payment.models import Payment


class PaymentRepository:
    """
    Data access layer for payments.
    Encapsulates all SQL queries, filtering, and eager loading for payments.
    """

    @staticmethod
    def get_by_id(db: Session, payment_id: int) -> Optional[Payment]:
        return (
            db.query(Payment)
            .options(joinedload(Payment.order))
            .filter(Payment.id == payment_id)
            .first()
        )

    @staticmethod
    def get_by_order_id(db: Session, order_id: int) -> Optional[Payment]:
        return (
            db.query(Payment)
            .options(joinedload(Payment.order))
            .filter(Payment.order_id == order_id)
            .first()
        )

    @staticmethod
    def get_by_reference(db: Session, reference: str) -> Optional[Payment]:
        return (
            db.query(Payment)
            .options(joinedload(Payment.order))
            .filter(Payment.payment_reference == reference)
            .first()
        )

    @staticmethod
    def get_customer_payment(
        db: Session, user_id: int, order_identifier: str
    ) -> Optional[Payment]:
        """
        Retrieves the Payment record for an order owned by user_id.
        Accepts integer order ID or string order_number.
        Enforces strict customer isolation.
        """
        query = (
            db.query(Payment)
            .join(Order, Payment.order_id == Order.id)
            .options(joinedload(Payment.order))
            .filter(Order.user_id == user_id)
        )

        if order_identifier.isdigit():
            query = query.filter(
                or_(
                    Order.id == int(order_identifier),
                    Order.order_number == order_identifier,
                )
            )
        else:
            query = query.filter(Order.order_number == order_identifier)

        return query.first()

    @staticmethod
    def list_payments(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        method: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Payment], int]:
        """
        Retrieves paginated payments with optional status, method, and search filters.
        Search scans payment_reference, order_number, customer_name, and customer_email.
        """
        query = (
            db.query(Payment)
            .join(Order, Payment.order_id == Order.id)
            .options(joinedload(Payment.order))
        )

        if status:
            query = query.filter(Payment.status == status.strip().upper())

        if method:
            query = query.filter(Payment.method == method.strip().upper())

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Payment.payment_reference.ilike(term),
                    Order.order_number.ilike(term),
                    Order.customer_name.ilike(term),
                    Order.customer_email.ilike(term),
                )
            )

        total = query.count()
        offset = (page - 1) * page_size
        items = (
            query.order_by(Payment.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return items, total
