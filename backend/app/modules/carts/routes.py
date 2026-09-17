from app.core import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_customer
from app.modules.carts.schemas import (
    CartItemAddRequest,
    CartItemUpdateRequest,
    CartResponse,
)
from app.modules.carts.service import CartService
from app.modules.users.models import User

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])


@router.get(
    "",
    response_model=CartResponse,
    summary="Get authenticated customer's cart",
)
def get_customer_cart(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):

    """
    Retrieves the current customer's active shopping cart, with live availability validation
    and calculated Decimal subtotals. Lazily initializes an empty cart if not already existing.
    """
    return CartService.get_cart(db=db, user=current_user)


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Add an active product to cart",
)
def add_product_to_cart(
    payload: CartItemAddRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Adds an active product to the customer's cart. If the product is already present,
    increases its quantity. Strictly validates available inventory without reserving stock.
    """
    return CartService.add_item(
        db=db,
        user=current_user,
        product_id=payload.product_id,
        quantity=payload.quantity,
    )


@router.patch(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Update cart item quantity",
)
def update_cart_item(
    item_id: int,
    payload: CartItemUpdateRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Updates the quantity of a specific item in the customer's cart.
    Enforces customer ownership and inventory availability validation.
    """
    return CartService.update_item(
        db=db,
        user=current_user,
        item_id=item_id,
        quantity=payload.quantity,
    )


@router.delete(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Remove an item from cart",
)
def remove_cart_item(
    item_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Removes an item from the customer's cart and recalculates cart totals.
    Enforces ownership isolation.
    """
    return CartService.remove_item(
        db=db,
        user=current_user,
        item_id=item_id,
    )


@router.delete(
    "",
    response_model=CartResponse,
    summary="Clear all items from cart",
)
def clear_customer_cart(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Removes all items from the customer's cart while preserving the cart entity for reuse.
    """
    return CartService.clear_cart(db=db, user=current_user)

