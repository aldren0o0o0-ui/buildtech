from typing import Any, Dict, List, Optional
from app.core import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.modules.inventory.models import (
    Inventory,
    InventoryTransaction,
    InventoryTransactionType,
)
from app.modules.products.models import Product, ProductStatus


def get_or_create_inventory(db: Session, product_id: int) -> Inventory:
    """
    Retrieves or automatically initializes an Inventory record for a product.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found.",
        )

    inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inventory:
        inventory = Inventory(
            product_id=product_id,
            quantity=0,
            reserved_quantity=0,
            low_stock_threshold=5,
        )
        db.add(inventory)
        db.commit()
        db.refresh(inventory)

    return inventory


def get_inventory_by_product_id(db: Session, product_id: int) -> Inventory:
    """
    Retrieves the inventory record for a product.
    """
    return get_or_create_inventory(db, product_id)


def list_inventories(
    db: Session,
    search: Optional[str] = None,
    availability: Optional[str] = None,
    sort: Optional[str] = "name_asc",
) -> List[Dict[str, Any]]:
    """
    Lists inventory status across all catalog products for administration.
    """
    products_query = (
        db.query(Product)
        .options(
            joinedload(Product.category),
            joinedload(Product.brand),
            joinedload(Product.inventory),
        )
    )

    if search:
        search_term = f"%{search.strip()}%"
        products_query = products_query.filter(
            Product.name.ilike(search_term) | Product.sku.ilike(search_term)
        )

    products = products_query.all()
    results = []

    for product in products:
        # Ensure inventory object exists
        inventory = product.inventory
        if not inventory:
            inventory = Inventory(
                product_id=product.id,
                quantity=0,
                reserved_quantity=0,
                low_stock_threshold=5,
            )
            db.add(inventory)
            db.commit()
            db.refresh(inventory)

        avail_status = inventory.availability_status

        # Optional availability status filter
        if availability and avail_status != availability.strip().upper():
            continue

        item = {
            "id": inventory.id,
            "product_id": product.id,
            "product": {
                "id": product.id,
                "name": product.name,
                "sku": product.sku,
                "category_name": product.category.name if product.category else None,
                "brand_name": product.brand.name if product.brand else None,
                "status": product.status,
                "is_active": product.is_active,
            },
            "quantity": inventory.quantity,
            "reserved_quantity": inventory.reserved_quantity,
            "available_quantity": inventory.available_quantity,
            "low_stock_threshold": inventory.low_stock_threshold,
            "availability_status": avail_status,
            "updated_at": inventory.updated_at,
        }
        results.append(item)

    # Sorting
    if sort == "quantity_asc":
        results.sort(key=lambda x: x["quantity"])
    elif sort == "quantity_desc":
        results.sort(key=lambda x: x["quantity"], reverse=True)
    elif sort == "available_asc":
        results.sort(key=lambda x: x["available_quantity"])
    elif sort == "available_desc":
        results.sort(key=lambda x: x["available_quantity"], reverse=True)
    elif sort == "name_desc":
        results.sort(key=lambda x: (x["product"]["name"] or "").lower(), reverse=True)
    else:
        # Default: product name ascending
        results.sort(key=lambda x: (x["product"]["name"] or "").lower())

    return results


def stock_in(
    db: Session,
    product_id: int,
    quantity: int,
    reason: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Inventory:
    """
    Atomically adds physical stock to inventory and creates a STOCK_IN audit transaction.
    """
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock-in quantity must be a positive integer greater than 0.",
        )

    inventory = get_or_create_inventory(db, product_id)
    before_qty = inventory.quantity
    after_qty = before_qty + quantity

    # Update inventory
    inventory.quantity = after_qty

    # Create immutable audit transaction
    transaction = InventoryTransaction(
        product_id=product_id,
        inventory_id=inventory.id,
        type=InventoryTransactionType.STOCK_IN.value,
        quantity_change=quantity,
        quantity_before=before_qty,
        quantity_after=after_qty,
        reason=reason.strip() if reason else "Standard stock replenishment",
        created_by_user_id=user_id,
    )

    db.add(inventory)
    db.add(transaction)
    db.commit()
    db.refresh(inventory)
    return inventory


def adjust_inventory(
    db: Session,
    product_id: int,
    adj_type: str,
    quantity: int,
    reason: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Inventory:
    """
    Atomically adjusts inventory upward or downward with strict negative and reserved stock protections.
    """
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adjustment quantity must be a positive integer greater than 0.",
        )

    norm_type = adj_type.strip().upper()
    if norm_type not in (
        InventoryTransactionType.ADJUSTMENT_IN.value,
        InventoryTransactionType.ADJUSTMENT_OUT.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid adjustment type. Must be either 'ADJUSTMENT_IN' or 'ADJUSTMENT_OUT'.",
        )

    inventory = get_or_create_inventory(db, product_id)
    before_qty = inventory.quantity

    if norm_type == InventoryTransactionType.ADJUSTMENT_IN.value:
        change = quantity
        after_qty = before_qty + quantity
    else:
        change = -quantity
        after_qty = before_qty - quantity

        # Negative stock protection
        if after_qty < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reduce inventory below 0 units. Current stock is {before_qty}, requested reduction is {quantity}.",
            )

        # Reserved quantity invariant protection
        if after_qty < inventory.reserved_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reduce stock below reserved level of {inventory.reserved_quantity} units. Available for reduction: {inventory.available_quantity}.",
            )

    inventory.quantity = after_qty

    transaction = InventoryTransaction(
        product_id=product_id,
        inventory_id=inventory.id,
        type=norm_type,
        quantity_change=change,
        quantity_before=before_qty,
        quantity_after=after_qty,
        reason=reason.strip() if reason else "Inventory count adjustment",
        created_by_user_id=user_id,
    )

    db.add(inventory)
    db.add(transaction)
    db.commit()
    db.refresh(inventory)
    return inventory


def update_low_stock_threshold(
    db: Session,
    product_id: int,
    low_stock_threshold: int,
) -> Inventory:
    """
    Updates the low stock threshold for a product.
    """
    if low_stock_threshold < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Low stock threshold cannot be negative.",
        )

    inventory = get_or_create_inventory(db, product_id)
    inventory.low_stock_threshold = low_stock_threshold
    db.add(inventory)
    db.commit()
    db.refresh(inventory)
    return inventory


def get_transactions(db: Session, product_id: int) -> List[InventoryTransaction]:
    """
    Retrieves the immutable audit trail of inventory transactions for a product, newest first.
    """
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found.",
        )

    return (
        db.query(InventoryTransaction)
        .filter(InventoryTransaction.product_id == product_id)
        .order_by(InventoryTransaction.created_at.desc(), InventoryTransaction.id.desc())
        .all()
    )


def get_product_availability(
    db: Session,
    product_id: int,
    include_inactive: bool = False,
) -> Dict[str, Any]:
    """
    Retrieves public availability indicator for a product.
    Enforces product visibility constraints for public storefront requests.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found.",
        )

    if not include_inactive:
        if not product.is_active or product.status != ProductStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or not currently available.",
            )

    inventory = get_or_create_inventory(db, product_id)
    status_str = inventory.availability_status

    return {
        "product_id": product.id,
        "availability": status_str,
        "is_available": status_str != "OUT_OF_STOCK",
    }
