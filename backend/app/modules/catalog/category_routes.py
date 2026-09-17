from typing import List, Optional
from app.core import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.schemas import MessageResponse
from app.db.session import get_db
from app.modules.auth.dependencies import get_optional_current_user, require_admin
from app.modules.catalog.category_schemas import (
    CategoryCreateRequest,
    CategoryResponse,
    CategoryUpdateRequest,
)
from app.modules.catalog.category_service import (
    create_category,
    delete_category,
    get_category_by_id,
    list_categories,
    update_category,
)
from app.modules.users.models import User, UserRole

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    response_model=List[CategoryResponse],
    summary="List categories (active for public, all for admin)",
)
def get_categories(
    include_inactive: bool = Query(False, description="Include inactive categories (Admin only)"),
    search: Optional[str] = Query(None, description="Filter categories by name or description"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Public listing returns active categories only.
    Authenticated ADMIN users can request inactive categories via include_inactive=true.
    """
    if include_inactive:
        if not current_user or current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to view inactive categories.",
            )

    return list_categories(
        db=db,
        include_inactive=include_inactive,
        search=search,
    )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get category by ID",
)
def get_category(
    category_id: int,
    include_inactive: bool = Query(False, description="Include inactive category (Admin only)"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves category details. Public users can only retrieve active categories.
    """
    if include_inactive:
        if not current_user or current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to view inactive categories.",
            )

    category = get_category_by_id(
        db=db,
        category_id=category_id,
        include_inactive=include_inactive,
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )
    return category


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category (Admin only)",
)
def add_category(
    category_in: CategoryCreateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Creates a new category. Restricted to ADMIN users.
    Slug is deterministically generated on the backend.
    """
    return create_category(db=db, category_in=category_in)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update category (Admin only)",
)
def edit_category(
    category_id: int,
    category_in: CategoryUpdateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Updates an existing category. Restricted to ADMIN users.
    """
    return update_category(
        db=db,
        category_id=category_id,
        category_in=category_in,
    )


@router.delete(
    "/{category_id}",
    response_model=MessageResponse,
    summary="Delete category (Admin only)",
)
def remove_category(
    category_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Permanently deletes a category record. Restricted to ADMIN users.
    """
    delete_category(db=db, category_id=category_id)
    return MessageResponse(message="Category deleted successfully.")
