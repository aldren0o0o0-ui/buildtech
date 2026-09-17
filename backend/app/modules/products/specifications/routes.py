from typing import Any, Dict, Optional
from app.core import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.schemas import MessageResponse
from app.db.session import get_db
from app.modules.auth.dependencies import get_optional_current_user, require_admin
from app.modules.products.specifications.schemas import ProductSpecificationResponse
from app.modules.products.specifications.service import (
    delete_product_specifications,
    get_product_specifications,
    upsert_product_specifications,
)
from app.modules.users.models import User, UserRole

router = APIRouter(prefix="/products/{product_id}/specifications", tags=["Product Specifications"])


@router.get(
    "",
    response_model=ProductSpecificationResponse,
    summary="Get product technical specifications",
)
def get_specifications(
    product_id: int,
    include_inactive: bool = Query(False, description="Include inactive/draft product specifications (Admin only)"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Public users can view specifications for published, active products.
    Admins can view specifications for draft and inactive products.
    """
    if include_inactive:
        if not current_user or current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to view specifications for inactive products.",
            )

    is_admin = bool(current_user and current_user.role == UserRole.ADMIN.value)
    return get_product_specifications(
        db=db,
        product_id=product_id,
        include_inactive=is_admin or include_inactive,
    )


@router.put(
    "",
    response_model=ProductSpecificationResponse,
    summary="Create or update product specifications (Admin only)",
)
def update_specifications(
    product_id: int,
    payload: Dict[str, Any] = Body(...),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Creates or updates the technical specifications for a product.
    Validates that the provided fields match the Product's Category. Restricted to ADMIN users.
    """
    return upsert_product_specifications(
        db=db,
        product_id=product_id,
        payload=payload,
    )


@router.delete(
    "",
    response_model=MessageResponse,
    summary="Delete product specifications (Admin only)",
)
def remove_specifications(
    product_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Deletes the technical specification record for a product.
    Does not delete the product itself. Restricted to ADMIN users.
    """
    delete_product_specifications(
        db=db,
        product_id=product_id,
    )
    return MessageResponse(message="Product specifications deleted successfully.")
