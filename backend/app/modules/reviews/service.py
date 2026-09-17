import math
from typing import Any, Dict, List, Optional
from app.core import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.products.models import Product, ProductStatus
from app.modules.reviews.models import Review, ReviewStatus
from app.modules.reviews.repository import ReviewRepository
from app.modules.reviews.schemas import (
    MyReviewResponse,
    ReviewAdminRead,
    ReviewCreate,
    ReviewListResponse,
    ReviewRead,
    ReviewSummaryResponse,
    ReviewUpdate,
)
from app.modules.users.models import User, UserRole


class ReviewService:
    """
    Business logic and authorization enforcement for the Reviews domain.
    Enforces verified purchaser requirements, customer ownership, and moderation rules.
    """

    @classmethod
    def create_review(
        cls,
        db: Session,
        user: User,
        product_id: int,
        payload: ReviewCreate,
    ) -> ReviewRead:
        """
        Creates a verified purchaser review.
        Enforces:
        - Product existence & active status
        - Authoritative purchase verification from customer's non-cancelled orders
        - Uniqueness constraint (1 review per customer per product)
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product or product.status == ProductStatus.ARCHIVED.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or is no longer available for reviews.",
            )

        # Enforce server-side purchase verification
        has_purchased = ReviewRepository.has_customer_purchased_product(
            db, user_id=user.id, product_id=product_id
        )
        if not has_purchased:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only verified purchasers who have an active, non-cancelled order for this product can submit a review.",
            )

        # Enforce one review per product per customer
        existing = ReviewRepository.get_by_user_and_product(
            db, user_id=user.id, product_id=product_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted a review for this product. You can update your existing review instead.",
            )

        review = Review(
            user_id=user.id,
            product_id=product_id,
            rating=payload.rating,
            title=payload.title.strip(),
            comment=payload.comment.strip(),
            is_verified_purchase=True,
            status=ReviewStatus.PUBLISHED.value,
        )

        try:
            db.add(review)
            db.commit()
            db.refresh(review)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already reviewed this product.",
            ) from exc

        return ReviewRead(
            id=review.id,
            product_id=review.product_id,
            rating=review.rating,
            title=review.title,
            comment=review.comment,
            is_verified_purchase=review.is_verified_purchase,
            author_name=review.author_name,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )

    @classmethod
    def update_review(
        cls,
        db: Session,
        user: User,
        review_id: int,
        payload: ReviewUpdate,
    ) -> ReviewRead:
        """
        Updates an existing review owned by the authenticated customer.
        """
        review = ReviewRepository.get_by_id(db, review_id)
        if not review or review.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found or does not belong to your account.",
            )

        if payload.rating is not None:
            review.rating = payload.rating
        if payload.title is not None:
            review.title = payload.title.strip()
        if payload.comment is not None:
            review.comment = payload.comment.strip()

        db.commit()
        db.refresh(review)

        return ReviewRead(
            id=review.id,
            product_id=review.product_id,
            rating=review.rating,
            title=review.title,
            comment=review.comment,
            is_verified_purchase=review.is_verified_purchase,
            author_name=review.author_name,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )

    @classmethod
    def delete_review(
        cls,
        db: Session,
        user: User,
        review_id: int,
    ) -> None:
        """
        Deletes a review owned by the authenticated customer.
        """
        review = ReviewRepository.get_by_id(db, review_id)
        if not review or review.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found or does not belong to your account.",
            )

        db.delete(review)
        db.commit()

    @classmethod
    def get_product_reviews(
        cls,
        db: Session,
        product_id: int,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "newest",
    ) -> ReviewListResponse:
        """
        Returns paginated published reviews and SQL-aggregated summary statistics for a product.
        """
        product = db.query(Product.id).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product #{product_id} not found.",
            )

        items, total = ReviewRepository.list_product_reviews(
            db=db,
            product_id=product_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            include_hidden=False,
        )

        read_items = [
            ReviewRead(
                id=r.id,
                product_id=r.product_id,
                rating=r.rating,
                title=r.title,
                comment=r.comment,
                is_verified_purchase=r.is_verified_purchase,
                author_name=r.author_name,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in items
        ]

        summary_data = ReviewRepository.get_product_review_summary(db, product_id)
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return ReviewListResponse(
            items=read_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            summary=ReviewSummaryResponse(**summary_data),
        )

    @classmethod
    def get_product_review_summary(
        cls,
        db: Session,
        product_id: int,
    ) -> ReviewSummaryResponse:
        """
        Retrieves rating statistics and distribution for a product.
        """
        product = db.query(Product.id).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product #{product_id} not found.",
            )

        summary_data = ReviewRepository.get_product_review_summary(db, product_id)
        return ReviewSummaryResponse(**summary_data)

    @classmethod
    def get_my_product_review(
        cls,
        db: Session,
        user: User,
        product_id: int,
    ) -> MyReviewResponse:
        """
        Checks customer's review eligibility and returns their existing review if present.
        """
        has_purchased = ReviewRepository.has_customer_purchased_product(
            db, user_id=user.id, product_id=product_id
        )
        existing = ReviewRepository.get_by_user_and_product(
            db, user_id=user.id, product_id=product_id
        )

        review_read = None
        if existing:
            review_read = ReviewRead(
                id=existing.id,
                product_id=existing.product_id,
                rating=existing.rating,
                title=existing.title,
                comment=existing.comment,
                is_verified_purchase=existing.is_verified_purchase,
                author_name=existing.author_name,
                created_at=existing.created_at,
                updated_at=existing.updated_at,
            )

        return MyReviewResponse(
            can_review=has_purchased and (existing is None),
            has_reviewed=existing is not None,
            review=review_read,
        )

    @classmethod
    def admin_list_reviews(
        cls,
        db: Session,
        page: int = 1,
        page_size: int = 10,
        product_id: Optional[int] = None,
        rating: Optional[int] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Administrative review management list with filtering, searching, and pagination.
        """
        items, total = ReviewRepository.list_admin_reviews(
            db=db,
            page=page,
            page_size=page_size,
            product_id=product_id,
            rating=rating,
            status=status_filter,
            search=search,
        )

        read_items = [
            ReviewAdminRead(
                id=r.id,
                product_id=r.product_id,
                user_id=r.user_id,
                user_email=r.user.email if r.user else None,
                product_name=r.product.name if r.product else None,
                product_sku=r.product.sku if r.product else None,
                rating=r.rating,
                title=r.title,
                comment=r.comment,
                is_verified_purchase=r.is_verified_purchase,
                author_name=r.author_name,
                status=r.status,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in items
        ]

        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return {
            "items": read_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @classmethod
    def admin_get_review(cls, db: Session, review_id: int) -> ReviewAdminRead:
        review = ReviewRepository.get_by_id(db, review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review #{review_id} not found.",
            )

        return ReviewAdminRead(
            id=review.id,
            product_id=review.product_id,
            user_id=review.user_id,
            user_email=review.user.email if review.user else None,
            product_name=review.product.name if review.product else None,
            product_sku=review.product.sku if review.product else None,
            rating=review.rating,
            title=review.title,
            comment=review.comment,
            is_verified_purchase=review.is_verified_purchase,
            author_name=review.author_name,
            status=review.status,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )

    @classmethod
    def admin_moderate_review(
        cls,
        db: Session,
        admin_user: User,
        review_id: int,
        target_status: ReviewStatus,
    ) -> ReviewAdminRead:
        """
        Moderates a review status (PUBLISHED <-> HIDDEN).
        """
        if admin_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can moderate reviews.",
            )

        review = ReviewRepository.get_by_id(db, review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review #{review_id} not found.",
            )

        review.status = target_status.value
        db.commit()
        db.refresh(review)
        return cls.admin_get_review(db, review.id)

    @classmethod
    def admin_delete_review(
        cls,
        db: Session,
        admin_user: User,
        review_id: int,
    ) -> None:
        """
        Permanently removes a review from administrative dashboard.
        """
        if admin_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can delete reviews.",
            )

        review = ReviewRepository.get_by_id(db, review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review #{review_id} not found.",
            )

        db.delete(review)
        db.commit()
