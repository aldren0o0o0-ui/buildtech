from typing import List, Optional, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.modules.orders.models import Order, OrderItem


class OrderRepository:
    """
    Database persistence and query abstraction for Orders and OrderItems.
    Separates SQL queries from business logic.
    """

    @staticmethod
    def get_by_id(db: Session, order_id: int) -> Optional[Order]:
        return (
            db.query(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.payment),
            )
            .filter(Order.id == order_id)
            .first()
        )

    @staticmethod
    def get_by_order_number(db: Session, order_number: str) -> Optional[Order]:
        return (
            db.query(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.payment),
            )
            .filter(Order.order_number == order_number)
            .first()
        )

    @staticmethod
    def get_customer_order(
        db: Session, user_id: int, order_identifier: str
    ) -> Optional[Order]:
        """
        Retrieves an order owned by a specific customer using either its
        numeric database ID or alphanumeric order number.
        """
        query = (
            db.query(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.payment),
            )
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
    def get_by_idempotency_key(
        db: Session, user_id: int, idempotency_key: str
    ) -> Optional[Order]:
        return (
            db.query(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.payment),
            )
            .filter(
                Order.user_id == user_id,
                Order.idempotency_key == idempotency_key,
            )
            .first()
        )

    @staticmethod
    def list_customer_orders(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
    ) -> Tuple[List[Order], int]:
        query = (
            db.query(Order)
            .options(joinedload(Order.items))
            .filter(Order.user_id == user_id)
        )

        if status:
            query = query.filter(Order.status == status.strip().upper())

        total = query.count()
        orders = (
            query.order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return orders, total

    @staticmethod
    def list_admin_orders(
        db: Session,
        search: Optional[str] = None,
        status: Optional[str] = None,
        payment_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Order], int]:
        query = db.query(Order).options(joinedload(Order.items))

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Order.order_number.ilike(search_term),
                    Order.customer_name.ilike(search_term),
                    Order.customer_email.ilike(search_term),
                )
            )

        if status:
            query = query.filter(Order.status == status.strip().upper())

        if payment_status:
            query = query.filter(Order.payment_status == payment_status.strip().upper())

        total = query.count()
        orders = (
            query.order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return orders, total
