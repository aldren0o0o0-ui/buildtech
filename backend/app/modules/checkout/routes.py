from app.core import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_customer
from app.modules.checkout.schemas import (
    CheckoutValidationRequest,
    CheckoutValidationResponse,
)
from app.modules.checkout.service import CheckoutService
from app.modules.users.models import User

router = APIRouter(prefix="/checkout", tags=["Checkout"])


@router.post(
    "/validate",
    response_model=CheckoutValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate cart and shipping address for checkout",
)
def validate_checkout(
    payload: CheckoutValidationRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Validates the customer's current cart and selected shipping address:
    - Re-reads live cart from DB
    - Checks address ownership
    - Checks product active status
    - Checks available inventory
    - Computes authoritative price totals

    NON-DESTRUCTIVE:
    Does NOT reserve inventory, mutate stock, clear cart, or create orders.
    """
    service = CheckoutService(db)
    return service.validate_checkout(
        user_id=current_user.id,
        address_id=payload.address_id,
    )
