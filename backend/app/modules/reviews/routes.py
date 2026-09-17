from typing import Any, Dict, Optional
from app.core import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.reviews.schemas import (
    MyReviewResponse,
    ReviewAdminRead,
    ReviewCreate,
    ReviewListResponse,
    ReviewRead,
    ReviewStatusUpdate,
    ReviewSummaryResponse,
    ReviewUpdate,
)
from app.modules.reviews.service import ReviewService
from app.modules.users.models import User, UserRole


def require_customer(current_user: User = Depends(get_current_user)) -> User:
    """Ensures the authenticated user has customer privileges."""
    if current_user.role != UserRole.CUSTOMER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Customer privileges required.",
        )
    return current_user


# Storefront review routers
product_reviews_router = APIRouter(prefix="/products", tags=["Reviews"])
reviews_router = APIRouter(prefix="/reviews", tags=["Reviews"])

# Administrative review router
admin_reviews_router = APIRouter(prefix="/admin/reviews", tags=["Admin Reviews"])


# ---------------------------------------------------------------------------
# Storefront Customer Review Endpoints
# ---------------------------------------------------------------------------

@product_reviews_router.get(
    "/{product_id}/reviews",
    response_model=ReviewListResponse,
    summary="List published reviews for a product",
)
def get_product_reviews(
    product_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Reviews per page"),
    sort_by: str = Query("newest", pattern="^(newest|oldest|highest_rating|lowest_rating)$", description="Sort order"),
    db: Session = Depends(get_db),
):
    """
    Public storefront endpoint returning paginated reviews and summary rating stats.
    """
    return ReviewService.get_product_reviews(
        db=db,
        product_id=product_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
    )


@product_reviews_router.get(
    "/{product_id}/reviews/summary",
    response_model=ReviewSummaryResponse,
    summary="Get rating statistics summary for a product",
)
def get_product_review_summary(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Public storefront endpoint returning average score, total count, and star distribution.
    """
    return ReviewService.get_product_review_summary(db=db, product_id=product_id)


@product_reviews_router.get(
    "/{product_id}/reviews/me",
    response_model=MyReviewResponse,
    summary="Get current customer's review for a product",
)
def get_my_product_review(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    """
    Returns the authenticated customer's review status and existing review (if submitted).
    """
    return ReviewService.get_my_product_review(
        db=db,
        user=current_user,
        product_id=product_id,
    )


@reviews_router.get(
    "/products/{product_id}/my-review",
    response_model=MyReviewResponse,
    summary="Get current customer's review for a product (alias)",
)
def get_my_product_review_alias(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    return ReviewService.get_my_product_review(
        db=db,
        user=current_user,
        product_id=product_id,
    )


@product_reviews_router.post(
    "/{product_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a verified purchaser review for a product",
)
def create_review(
    product_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    """
    Submits a product review.
    Enforces server-side purchase verification from customer's active non-cancelled orders.
    Enforces a unique constraint of one review per customer per product.
    """
    return ReviewService.create_review(
        db=db,
        user=current_user,
        product_id=product_id,
        payload=payload,
    )


@reviews_router.patch(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Update customer's own review",
)
@reviews_router.put(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Update customer's own review",
)
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    """
    Updates an existing review owned by the authenticated customer.
    """
    return ReviewService.update_review(
        db=db,
        user=current_user,
        review_id=review_id,
        payload=payload,
    )


@reviews_router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete customer's own review",
)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_customer),
):
    """
    Deletes an existing review owned by the authenticated customer.
    """
    ReviewService.delete_review(
        db=db,
        user=current_user,
        review_id=review_id,
    )
    return None


# ---------------------------------------------------------------------------
# Administrative Review Management Endpoints
# ---------------------------------------------------------------------------

@admin_reviews_router.get(
    "",
    summary="List all reviews for administration with search and filtering",
)
def admin_list_reviews(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by star rating"),
    status: Optional[str] = Query(None, description="Filter by review status (PUBLISHED or HIDDEN)"),
    search: Optional[str] = Query(None, description="Search review text, customer, or product"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Administrative listing of reviews for moderation, filtering, and inspection.
    """
    return ReviewService.admin_list_reviews(
        db=db,
        page=page,
        page_size=page_size,
        product_id=product_id,
        rating=rating,
        status_filter=status,
        search=search,
    )


@admin_reviews_router.get(
    "/{review_id}",
    response_model=ReviewAdminRead,
    summary="Get administrative review details",
)
def admin_get_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Retrieves full review details including user and product metadata.
    """
    return ReviewService.admin_get_review(db=db, review_id=review_id)


@admin_reviews_router.patch(
    "/{review_id}/status",
    response_model=ReviewAdminRead,
    summary="Moderate review status (publish or hide)",
)
def admin_moderate_review(
    review_id: int,
    payload: ReviewStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Administrative moderation action: toggles review visibility between PUBLISHED and HIDDEN.
    """
    return ReviewService.admin_moderate_review(
        db=db,
        admin_user=current_admin,
        review_id=review_id,
        target_status=payload.status,
    )


@admin_reviews_router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete inappropriate review",
)
def admin_delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Permanently deletes a review as an administrator.
    """
    ReviewService.admin_delete_review(
        db=db,
        admin_user=current_admin,
        review_id=review_id,
    )
    return None
