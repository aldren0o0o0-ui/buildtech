from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.modules.orders.models import Order, OrderItem, OrderStatus
from app.modules.products.models import Product
from app.modules.reviews.models import Review, ReviewStatus
from app.modules.users.models import User

QUALIFYING_REVIEW_ORDER_STATUSES = {
    OrderStatus.CONFIRMED.value,
    OrderStatus.PROCESSING.value,
    OrderStatus.SHIPPED.value,
    OrderStatus.DELIVERED.value,
    OrderStatus.READY_FOR_FULFILLMENT.value,
    OrderStatus.COMPLETED.value,
}


class ReviewRepository:
    """
    Data access layer for Reviews domain.
    Executes database queries, SQL aggregations, and eager-loading optimizations.
    """

    @staticmethod
    def get_by_id(db: Session, review_id: int) -> Optional[Review]:
        return (
            db.query(Review)
            .options(joinedload(Review.user), joinedload(Review.product))
            .filter(Review.id == review_id)
            .first()
        )

    @staticmethod
    def get_by_user_and_product(
        db: Session, user_id: int, product_id: int
    ) -> Optional[Review]:
        return (
            db.query(Review)
            .options(joinedload(Review.user), joinedload(Review.product))
            .filter(
                Review.user_id == user_id,
                Review.product_id == product_id,
            )
            .first()
        )

    @staticmethod
    def has_customer_purchased_product(
        db: Session, user_id: int, product_id: int
    ) -> bool:
        """
        Verifies if customer has an active, non-cancelled order containing the product.
        """
        match = (
            db.query(OrderItem.id)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(
                Order.user_id == user_id,
                OrderItem.product_id == product_id,
                Order.status.in_(QUALIFYING_REVIEW_ORDER_STATUSES),
            )
            .first()
        )
        return match is not None

    @staticmethod
    def list_product_reviews(
        db: Session,
        product_id: int,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "newest",
        include_hidden: bool = False,
    ) -> Tuple[List[Review], int]:
        """
        Retrieves paginated public reviews for a product with deterministic sorting.
        Avoids N+1 queries by eager-loading Review.user.
        """
        query = (
            db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.product_id == product_id)
        )

        if not include_hidden:
            query = query.filter(Review.status == ReviewStatus.PUBLISHED.value)

        # Deterministic sorting
        if sort_by == "highest_rating":
            query = query.order_by(Review.rating.desc(), Review.created_at.desc(), Review.id.desc())
        elif sort_by == "lowest_rating":
            query = query.order_by(Review.rating.asc(), Review.created_at.desc(), Review.id.desc())
        elif sort_by == "oldest":
            query = query.order_by(Review.created_at.asc(), Review.id.asc())
        else:  # newest default
            query = query.order_by(Review.created_at.desc(), Review.id.desc())

        total = query.count()
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    @staticmethod
    def get_product_review_summary(db: Session, product_id: int) -> Dict[str, Any]:
        """
        Calculates review summary statistics via server-side SQL aggregation.
        Only counts PUBLISHED reviews.
        """
        stats = (
            db.query(
                func.avg(Review.rating),
                func.count(Review.id),
            )
            .filter(
                Review.product_id == product_id,
                Review.status == ReviewStatus.PUBLISHED.value,
            )
            .first()
        )

        raw_avg, raw_count = stats if stats else (None, 0)
        avg_rating = round(float(raw_avg), 1) if raw_avg is not None else 0.0
        total_reviews = int(raw_count) if raw_count is not None else 0

        # Distribution breakdown by star rating (1 to 5)
        dist_query = (
            db.query(
                Review.rating,
                func.count(Review.id),
            )
            .filter(
                Review.product_id == product_id,
                Review.status == ReviewStatus.PUBLISHED.value,
            )
            .group_by(Review.rating)
            .all()
        )

        distribution = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
        for star_rating, star_count in dist_query:
            if 1 <= star_rating <= 5:
                distribution[str(star_rating)] = star_count

        return {
            "average_rating": avg_rating,
            "total_reviews": total_reviews,
            "rating_distribution": distribution,
        }

    @staticmethod
    def list_admin_reviews(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        product_id: Optional[int] = None,
        rating: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Review], int]:
        """
        Paginated administrative retrieval of all reviews with filtering and search.
        """
        query = (
            db.query(Review)
            .join(User, Review.user_id == User.id)
            .join(Product, Review.product_id == Product.id)
            .options(joinedload(Review.user), joinedload(Review.product))
        )

        if product_id is not None:
            query = query.filter(Review.product_id == product_id)

        if rating is not None:
            query = query.filter(Review.rating == rating)

        if status:
            query = query.filter(Review.status == status.strip().upper())

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Review.title.ilike(term),
                    Review.comment.ilike(term),
                    User.email.ilike(term),
                    User.first_name.ilike(term),
                    User.last_name.ilike(term),
                    Product.name.ilike(term),
                    Product.sku.ilike(term),
                )
            )

        total = query.count()
        offset = (page - 1) * page_size
        items = (
            query.order_by(Review.created_at.desc(), Review.id.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return items, total
