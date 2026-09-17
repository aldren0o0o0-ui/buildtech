from typing import List, Optional
from app.core import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.schemas import MessageResponse
from app.db.session import get_db
from app.modules.auth.dependencies import get_optional_current_user, require_admin
from app.modules.catalog.brand_schemas import (
    BrandCreateRequest,
    BrandResponse,
    BrandUpdateRequest,
)
from app.modules.catalog.brand_service import (
    create_brand,
    delete_brand,
    get_brand_by_id,
    list_brands,
    update_brand,
)
from app.modules.users.models import User, UserRole

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get(
    "",
    response_model=List[BrandResponse],
    summary="List brands (active for public, all for admin)",
)
def get_brands(
    include_inactive: bool = Query(False, description="Include inactive brands (Admin only)"),
    search: Optional[str] = Query(None, description="Filter brands by name or description"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Public listing returns active brands only.
    Authenticated ADMIN users can request inactive brands via include_inactive=true.
    """
    if include_inactive:
        if not current_user or current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to view inactive brands.",
            )

    return list_brands(
        db=db,
        include_inactive=include_inactive,
        search=search,
    )


@router.get(
    "/{brand_id}",
    response_model=BrandResponse,
    summary="Get brand by ID",
)
def get_brand(
    brand_id: int,
    include_inactive: bool = Query(False, description="Include inactive brand (Admin only)"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves brand details. Public users can only retrieve active brands.
    """
    if include_inactive:
        if not current_user or current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to view inactive brands.",
            )

    brand = get_brand_by_id(
        db=db,
        brand_id=brand_id,
        include_inactive=include_inactive,
    )
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found.",
        )
    return brand


@router.post(
    "",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new brand (Admin only)",
)
def add_brand(
    brand_in: BrandCreateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Creates a new brand. Restricted to ADMIN users.
    Slug is deterministically generated on the backend.
    """
    return create_brand(db=db, brand_in=brand_in)


@router.patch(
    "/{brand_id}",
    response_model=BrandResponse,
    summary="Update brand (Admin only)",
)
def edit_brand(
    brand_id: int,
    brand_in: BrandUpdateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Updates an existing brand. Restricted to ADMIN users.
    """
    return update_brand(
        db=db,
        brand_id=brand_id,
        brand_in=brand_in,
    )


@router.delete(
    "/{brand_id}",
    response_model=MessageResponse,
    summary="Delete brand (Admin only)",
)
def remove_brand(
    brand_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Permanently deletes a brand record. Restricted to ADMIN users.
    """
    delete_brand(db=db, brand_id=brand_id)
    return MessageResponse(message="Brand deleted successfully.")
