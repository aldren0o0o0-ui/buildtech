from typing import List, Optional
from app.core import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_optional_current_user, require_admin
from app.modules.inventory.schemas import (
    InventoryAdminResponse,
    InventoryAdjustmentRequest,
    InventoryResponse,
    InventoryStockInRequest,
    InventoryThresholdUpdateRequest,
    InventoryTransactionResponse,
    ProductAvailabilityResponse,
)
from app.modules.inventory.service import (
    adjust_inventory,
    get_inventory_by_product_id,
    get_product_availability,
    get_transactions,
    list_inventories,
    stock_in,
    update_low_stock_threshold,
)
from app.modules.users.models import User, UserRole

# 1. Admin Inventory Management Router
inventory_router = APIRouter(prefix="/inventory", tags=["Inventory Management"])

# 2. Public Product Availability Router
public_availability_router = APIRouter(prefix="/products/{product_id}/availability", tags=["Product Availability"])


# ==========================================
# ADMIN INVENTORY ENDPOINTS
# ==========================================

@inventory_router.get(
    "",
    response_model=List[InventoryAdminResponse],
    summary="List all product inventories (Admin only)",
)
def get_all_inventory(
    search: Optional[str] = Query(None, description="Search by product name or SKU"),
    availability: Optional[str] = Query(None, description="Filter by availability status: IN_STOCK, LOW_STOCK, OUT_OF_STOCK"),
    sort: Optional[str] = Query("name_asc", description="Sort order: name_asc, name_desc, quantity_asc, quantity_desc, available_asc, available_desc"),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Returns inventory status across catalog products with stock levels and alert thresholds.
    """
    return list_inventories(
        db=db,
        search=search,
        availability=availability,
        sort=sort,
    )


@inventory_router.get(
    "/{product_id}",
    response_model=InventoryResponse,
    summary="Get product inventory details (Admin only)",
)
def get_single_inventory(
    product_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Returns the inventory record for a specific product.
    """
    return get_inventory_by_product_id(db=db, product_id=product_id)


@inventory_router.post(
    "/{product_id}/stock-in",
    response_model=InventoryResponse,
    summary="Receive new stock into inventory (Admin only)",
)
def add_stock(
    product_id: int,
    stock_in_data: InventoryStockInRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Atomically adds received stock to inventory and creates a STOCK_IN audit transaction record.
    """
    return stock_in(
        db=db,
        product_id=product_id,
        quantity=stock_in_data.quantity,
        reason=stock_in_data.reason,
        user_id=admin_user.id,
    )


@inventory_router.post(
    "/{product_id}/adjust",
    response_model=InventoryResponse,
    summary="Adjust inventory stock level (Admin only)",
)
def make_adjustment(
    product_id: int,
    adjustment_data: InventoryAdjustmentRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Atomically increases or decreases inventory stock. Enforces non-negative and reserved stock invariants.
    """
    return adjust_inventory(
        db=db,
        product_id=product_id,
        adj_type=adjustment_data.type,
        quantity=adjustment_data.quantity,
        reason=adjustment_data.reason,
        user_id=admin_user.id,
    )


@inventory_router.patch(
    "/{product_id}/threshold",
    response_model=InventoryResponse,
    summary="Update low stock threshold (Admin only)",
)
def change_threshold(
    product_id: int,
    threshold_data: InventoryThresholdUpdateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Updates the minimum quantity threshold for triggering low-stock alerts.
    """
    return update_low_stock_threshold(
        db=db,
        product_id=product_id,
        low_stock_threshold=threshold_data.low_stock_threshold,
    )


@inventory_router.get(
    "/{product_id}/transactions",
    response_model=List[InventoryTransactionResponse],
    summary="Get immutable inventory transaction history (Admin only)",
)
def get_transaction_history(
    product_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Returns the immutable audit trail of all stock operations for a product, sorted newest first.
    """
    return get_transactions(db=db, product_id=product_id)


# ==========================================
# PUBLIC AVAILABILITY ENDPOINT
# ==========================================

@public_availability_router.get(
    "",
    response_model=ProductAvailabilityResponse,
    summary="Get product availability status",
)
def get_availability(
    product_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns public availability state (IN_STOCK, LOW_STOCK, OUT_OF_STOCK) for visible products.
    """
    is_admin = bool(current_user and current_user.role == UserRole.ADMIN.value)
    return get_product_availability(
        db=db,
        product_id=product_id,
        include_inactive=is_admin,
    )
