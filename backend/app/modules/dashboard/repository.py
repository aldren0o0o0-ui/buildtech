from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import func, desc, case
from sqlalchemy.orm import Session, joinedload

from app.modules.orders.models import Order, OrderItem, OrderStatus, PaymentStatus
from app.modules.payment.models import Payment
from app.modules.users.models import User, UserRole
from app.modules.products.models import Product, ProductStatus
from app.modules.inventory.models import Inventory
from app.modules.catalog.category_model import Category


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_revenue_metrics(self) -> Dict[str, Any]:
        """
        Authoritative revenue and financial overview:
        - total_revenue: Total amount from orders/payments that are confirmed PAID
        - pending_payment: Total amount from active, non-cancelled orders awaiting payment (e.g. COD)
        - total_order_value: Gross value of all non-cancelled orders
        - total_orders: Total count of all placed orders
        """
        # Query orders for revenue metrics using single aggregate query
        rev_query = self.db.query(
            func.coalesce(
                func.sum(
                    case(
                        (Order.payment_status == PaymentStatus.PAID.value, Order.total_amount),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("total_revenue"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Order.payment_status == PaymentStatus.PENDING.value)
                            & (Order.status != OrderStatus.CANCELLED.value),
                            Order.total_amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("pending_payment"),
            func.coalesce(
                func.sum(
                    case(
                        (Order.status != OrderStatus.CANCELLED.value, Order.total_amount),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("total_order_value"),
            func.count(Order.id).label("total_orders"),
        ).first()

        total_revenue = rev_query.total_revenue if rev_query else Decimal("0.00")
        pending_payment = rev_query.pending_payment if rev_query else Decimal("0.00")
        total_order_value = rev_query.total_order_value if rev_query else Decimal("0.00")
        total_orders = rev_query.total_orders if rev_query else 0

        return {
            "total_revenue": f"{Decimal(total_revenue):.2f}",
            "pending_payment": f"{Decimal(pending_payment):.2f}",
            "total_order_value": f"{Decimal(total_order_value):.2f}",
            "total_orders": total_orders,
        }

    def get_order_status_counts(self) -> Dict[str, int]:
        """
        Aggregates orders grouped by their lifecycle status.
        """
        rows = (
            self.db.query(Order.status, func.count(Order.id))
            .group_by(Order.status)
            .all()
        )
        counts_by_status = {status: count for status, count in rows}

        pending = counts_by_status.get(OrderStatus.PENDING.value, 0)
        confirmed = counts_by_status.get(OrderStatus.CONFIRMED.value, 0)
        processing = counts_by_status.get(OrderStatus.PROCESSING.value, 0)
        shipped = counts_by_status.get(OrderStatus.SHIPPED.value, 0)
        delivered = counts_by_status.get(OrderStatus.DELIVERED.value, 0)
        ready_for_fulfillment = counts_by_status.get(OrderStatus.READY_FOR_FULFILLMENT.value, 0)
        completed = counts_by_status.get(OrderStatus.COMPLETED.value, 0)
        cancelled = counts_by_status.get(OrderStatus.CANCELLED.value, 0)
        total = sum(counts_by_status.values())

        return {
            "pending": pending,
            "confirmed": confirmed,
            "processing": processing,
            "shipped": shipped,
            "delivered": delivered,
            "ready_for_fulfillment": ready_for_fulfillment,
            "completed": completed,
            "cancelled": cancelled,
            "total": total,
        }

    def get_customer_metrics(self) -> Dict[str, int]:
        """
        Counts registered customer accounts (excluding administrators).
        """
        cust_query = self.db.query(
            func.count(User.id).label("total_customers"),
            func.coalesce(
                func.sum(
                    case(
                        (User.is_active == True, 1),
                        else_=0,
                    )
                ),
                0,
            ).label("active_customers"),
        ).filter(User.role == UserRole.CUSTOMER.value).first()

        total = cust_query.total_customers if cust_query else 0
        active = cust_query.active_customers if cust_query else 0
        return {
            "total_customers": total,
            "active_customers": active,
        }

    def get_product_metrics(self) -> Dict[str, int]:
        """
        Counts total products and active catalog products.
        """
        prod_query = self.db.query(
            func.count(Product.id).label("total_products"),
            func.coalesce(
                func.sum(
                    case(
                        (Product.status == ProductStatus.ACTIVE.value, 1),
                        else_=0,
                    )
                ),
                0,
            ).label("active_products"),
        ).first()

        total = prod_query.total_products if prod_query else 0
        active = prod_query.active_products if prod_query else 0
        return {
            "total_products": total,
            "active_products": active,
        }

    def get_low_stock_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves products where available stock (quantity - reserved_quantity)
        is less than or equal to their low_stock_threshold.
        """
        available_expr = Inventory.quantity - Inventory.reserved_quantity

        query = (
            self.db.query(Product, Inventory, Category)
            .join(Inventory, Inventory.product_id == Product.id)
            .outerjoin(Category, Category.id == Product.category_id)
            .filter(Product.status == ProductStatus.ACTIVE.value)
            .filter(available_expr <= Inventory.low_stock_threshold)
            .order_by(available_expr.asc(), Product.name.asc())
            .limit(limit)
        )

        results = []
        for product, inventory, category in query.all():
            available = max(0, inventory.quantity - inventory.reserved_quantity)
            status_str = "OUT_OF_STOCK" if available <= 0 else "LOW_STOCK"

            results.append({
                "product_id": product.id,
                "name": product.name,
                "sku": product.sku,
                "category_name": category.name if category else None,
                "quantity": inventory.quantity,
                "reserved_quantity": inventory.reserved_quantity,
                "available_quantity": available,
                "low_stock_threshold": inventory.low_stock_threshold,
                "availability_status": status_str,
            })

        return results

    def get_top_selling_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Aggregates units sold and total revenue per product from non-cancelled orders.
        """
        valid_statuses = [
            OrderStatus.CONFIRMED.value,
            OrderStatus.PROCESSING.value,
            OrderStatus.SHIPPED.value,
            OrderStatus.DELIVERED.value,
            OrderStatus.READY_FOR_FULFILLMENT.value,
            OrderStatus.COMPLETED.value,
        ]

        query = (
            self.db.query(
                OrderItem.product_id,
                OrderItem.product_name,
                OrderItem.product_sku,
                func.sum(OrderItem.quantity).label("units_sold"),
                func.sum(OrderItem.subtotal).label("total_sales"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.status.in_(valid_statuses))
            .group_by(
                OrderItem.product_id,
                OrderItem.product_name,
                OrderItem.product_sku,
            )
            .order_by(desc("units_sold"), desc("total_sales"))
            .limit(limit)
        )

        rows = query.all()
        results = []
        for row in rows:
            results.append({
                "product_id": row.product_id,
                "product_name": row.product_name,
                "product_sku": row.product_sku,
                "units_sold": int(row.units_sold or 0),
                "total_sales": f"{Decimal(row.total_sales or 0):.2f}",
            })

        return results

    def get_recent_orders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves the most recent customer orders with customer snapshot and payment state.
        """
        orders = (
            self.db.query(Order)
            .order_by(Order.created_at.desc(), Order.id.desc())
            .limit(limit)
            .all()
        )

        results = []
        for o in orders:
            results.append({
                "id": o.id,
                "order_number": o.order_number,
                "customer_name": o.customer_name,
                "customer_email": o.customer_email,
                "total_amount": f"{Decimal(o.total_amount):.2f}",
                "status": o.status,
                "payment_status": o.payment_status,
                "payment_method": o.payment_method,
                "created_at": o.created_at,
            })

        return results
