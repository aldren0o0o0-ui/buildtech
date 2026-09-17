"""
Compatibility API Routes (Module 14).

Exposes customer-safe hardware compatibility checking endpoint.
Operates strictly as a read-only domain operation without side effects.
"""

from app.core import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.compatibility.schemas import (
    CompatibilityCheckRequest,
    CompatibilityResponse,
)
from app.modules.compatibility.service import CompatibilityService

router = APIRouter(prefix="/compatibility", tags=["Compatibility"])


@router.post(
    "/check",
    response_model=CompatibilityResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate hardware compatibility across selected components",
    description=(
        "Customer-safe deterministic compatibility evaluation. Accepts a list of product IDs, "
        "retrieves authoritative specifications from PostgreSQL, and evaluates physical and "
        "electrical domain compatibility rules."
    ),
)
def check_compatibility(
    request: CompatibilityCheckRequest,
    db: Session = Depends(get_db),
) -> CompatibilityResponse:
    """
    Evaluates selected hardware components for compatibility.
    Does not modify inventory, carts, orders, or any persistent state.
    """
    service = CompatibilityService(db)
    return service.check_compatibility(request)
