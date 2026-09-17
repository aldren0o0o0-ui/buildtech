from app.core import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_customer
from app.modules.users.models import User
from app.modules.wishlist.schemas import (
    WishlistAddRequest,
    WishlistCheckResponse,
    WishlistResponse,
)
from app.modules.wishlist.service import WishlistService

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


@router.get(
    "",
    response_model=WishlistResponse,
    summary="Get authenticated customer's wishlist",
)
def get_customer_wishlist(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Retrieves the current customer's wishlist with full product details and live availability.
    Lazily creates an empty wishlist if one does not exist yet.
    """
    return WishlistService.get_wishlist(db=db, user=current_user)


@router.post(
    "/items",
    response_model=WishlistResponse,
    status_code=status.HTTP_200_OK,
    summary="Add an active product to wishlist",
)
def add_product_to_wishlist(
    payload: WishlistAddRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Adds an active product to the customer's wishlist.
    Idempotent: if product is already in the wishlist, succeeds without duplicate creation.
    """
    return WishlistService.add_item(
        db=db,
        user=current_user,
        product_id=payload.product_id,
    )


@router.delete(
    "/items/{item_id}",
    response_model=WishlistResponse,
    summary="Remove an item from wishlist",
)
def remove_product_from_wishlist(
    item_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Removes a product from the customer's wishlist.
    Enforces customer ownership: returns 404 if item does not exist or belongs to another user.
    """
    return WishlistService.remove_item(
        db=db,
        user=current_user,
        item_id=item_id,
    )


@router.get(
    "/check/{product_id}",
    response_model=WishlistCheckResponse,
    summary="Check whether a product is wishlisted",
)
def check_product_wishlist_status(
    product_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Lightweight check returning whether a product is saved in the current customer's wishlist.
    Avoids loading full wishlist entities for product card checks.
    """
    return WishlistService.check_product(
        db=db,
        user=current_user,
        product_id=product_id,
    )
