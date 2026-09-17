from sqlalchemy.orm import Session

from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schemas import (
    AdminDashboardResponse,
    DashboardOverviewMetrics,
    LowStockProductItem,
    OrderStatusCounts,
    RecentOrderItem,
    TopSellingProductItem,
)


class DashboardService:
    @staticmethod
    def get_dashboard_data(db: Session) -> AdminDashboardResponse:
        """
        Gathers and aggregates authoritative operational metrics for the Admin Dashboard.
        """
        repo = DashboardRepository(db)

        # 1. Overview metrics (financials, counts)
        revenue_metrics = repo.get_revenue_metrics()
        customer_metrics = repo.get_customer_metrics()
        product_metrics = repo.get_product_metrics()

        overview = DashboardOverviewMetrics(
            total_revenue=revenue_metrics["total_revenue"],
            pending_payment=revenue_metrics["pending_payment"],
            total_order_value=revenue_metrics["total_order_value"],
            total_orders=revenue_metrics["total_orders"],
            total_customers=customer_metrics["total_customers"],
            active_customers=customer_metrics["active_customers"],
            total_products=product_metrics["total_products"],
            active_products=product_metrics["active_products"],
        )

        # 2. Order breakdown by lifecycle status
        status_counts = repo.get_order_status_counts()
        orders_by_status = OrderStatusCounts(**status_counts)

        # 3. Inventory low-stock products
        low_stock_raw = repo.get_low_stock_products(limit=10)
        low_stock_products = [LowStockProductItem(**item) for item in low_stock_raw]

        # 4. Top-selling products
        top_selling_raw = repo.get_top_selling_products(limit=10)
        top_selling_products = [TopSellingProductItem(**item) for item in top_selling_raw]

        # 5. Recent orders
        recent_orders_raw = repo.get_recent_orders(limit=10)
        recent_orders = [RecentOrderItem(**item) for item in recent_orders_raw]

        return AdminDashboardResponse(
            overview=overview,
            orders_by_status=orders_by_status,
            low_stock_products=low_stock_products,
            top_selling_products=top_selling_products,
            recent_orders=recent_orders,
        )
