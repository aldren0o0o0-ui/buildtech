from datetime import datetime, timezone
from decimal import Decimal
import math
import secrets
from typing import Any, Dict, List, Optional
from app.core import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.addresses.repository import AddressRepository
from app.modules.carts.models import CartItem
from app.modules.carts.repository import CartRepository
from app.modules.inventory.models import (
    Inventory,
    InventoryTransaction,
    InventoryTransactionType,
)
from app.modules.orders.models import (
    Order,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.modules.orders.repository import OrderRepository
from app.modules.orders.schemas import CheckoutRequest, OrderCreateRequest
from app.modules.products.models import Product, ProductStatus
from app.modules.users.models import User, UserRole


ALLOWED_STATUS_TRANSITIONS: Dict[str, set] = {
    OrderStatus.PENDING.value: {
        OrderStatus.CONFIRMED.value,
        OrderStatus.CANCELLED.value,
    },
    OrderStatus.CONFIRMED.value: {
        OrderStatus.PROCESSING.value,
        OrderStatus.CANCELLED.value,
    },
    OrderStatus.PROCESSING.value: {
        OrderStatus.SHIPPED.value,
        OrderStatus.READY_FOR_FULFILLMENT.value,
        OrderStatus.CANCELLED.value,
    },
    OrderStatus.SHIPPED.value: {
        OrderStatus.DELIVERED.value,
    },
    OrderStatus.READY_FOR_FULFILLMENT.value: {
        OrderStatus.COMPLETED.value,
        OrderStatus.CANCELLED.value,
    },
    OrderStatus.DELIVERED.value: set(),
    OrderStatus.COMPLETED.value: set(),
    OrderStatus.CANCELLED.value: set(),
}

CUSTOMER_CANCELLABLE_STATUSES = {
    OrderStatus.PENDING.value,
    OrderStatus.CONFIRMED.value,
}


def generate_unique_order_number(db: Session) -> str:
    """
    Generates a human-friendly unique customer order number.
    Format: BT-YYYYMMDD-XXXXXX (e.g. BT-20260911-3A9B7C).
    Guarantees uniqueness by checking existing database records.
    """
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    for _ in range(10):
        random_suffix = secrets.token_hex(3).upper()
        order_number = f"BT-{date_str}-{random_suffix}"
        existing = (
            db.query(Order.id)
            .filter(Order.order_number == order_number)
            .first()
        )
        if not existing:
            return order_number
    # Fallback to microsecond precision if contention
    micro_suffix = datetime.now(timezone.utc).strftime("%H%M%S%f")[:6]
    return f"BT-{date_str}-{micro_suffix}"


class OrderService:
    """
    Core business logic and transactional coordination for Checkout and Orders.
    Guarantees that order creation, inventory deduction, audit logging,
    and cart clearing happen as a single atomic unit of work.
    """

    @staticmethod
    def checkout(
        db: Session,
        user: User,
        checkout_data: OrderCreateRequest,
        header_idempotency_key: Optional[str] = None,
    ) -> Order:
        """
        Executes atomic checkout:
        1. Checks idempotency
        2. Validates cart content
        3. Locks inventory rows (SELECT ... FOR UPDATE)
        4. Validates product availability & stock
        5. Computes authoritative prices
        6. Creates Order & OrderItem records
        7. Deducts stock & logs SALE transactions
        8. Clears customer cart
        9. Commits atomically
        """
        if user.role != UserRole.CUSTOMER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only authenticated customers can place orders.",
            )

        # Determine effective idempotency key (header takes precedence)
        effective_idempotency_key = (
            header_idempotency_key or checkout_data.idempotency_key
        )
        if effective_idempotency_key:
            effective_idempotency_key = effective_idempotency_key.strip()
            existing_order = OrderRepository.get_by_idempotency_key(
                db, user.id, effective_idempotency_key
            )
            if existing_order:
                # Safe idempotent retry: return existing order
                return existing_order

        try:
            # Step 1: Load customer cart
            cart = CartRepository.get_cart_by_user_id(db, user.id)
            if not cart or not cart.items or len(cart.items) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Your cart is empty. Please add products before checking out.",
                )

            # Step 2: Lock inventory rows for all products in cart
            # Sort product IDs to prevent deadlock across concurrent checkouts
            product_ids = sorted(list({item.product_id for item in cart.items}))

            locked_inventories = (
                db.query(Inventory)
                .filter(Inventory.product_id.in_(product_ids))
                .with_for_update()
                .all()
            )
            inventory_map = {inv.product_id: inv for inv in locked_inventories}

            # Step 3: Validate each cart item against product availability & locked stock
            subtotal = Decimal("0.00")
            validated_items = []

            for cart_item in cart.items:
                product = cart_item.product
                if not product or not product.is_active or product.status != ProductStatus.ACTIVE.value:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product '{cart_item.product.name if cart_item.product else 'Unknown'}' is no longer active or available for purchase.",
                    )

                inventory = inventory_map.get(cart_item.product_id)
                if not inventory:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"No inventory record found for product '{product.name}'.",
                    )

                if inventory.available_quantity < cart_item.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            f"Insufficient stock for '{product.name}'. "
                            f"Available: {inventory.available_quantity}, requested: {cart_item.quantity}."
                        ),
                    )

                # Authoritative server-calculated prices using Decimal
                unit_price = Decimal(str(product.price)).quantize(Decimal("0.01"))
                item_subtotal = (unit_price * cart_item.quantity).quantize(Decimal("0.01"))
                subtotal += item_subtotal

                validated_items.append({
                    "cart_item": cart_item,
                    "product": product,
                    "inventory": inventory,
                    "unit_price": unit_price,
                    "quantity": cart_item.quantity,
                    "item_subtotal": item_subtotal,
                })

            shipping_fee = Decimal("0.00")
            total_amount = (subtotal + shipping_fee).quantize(Decimal("0.01"))

            # Step 4: Resolve Shipping Address Snapshot (from Address model or inline data)
            if checkout_data.address_id:
                addr = AddressRepository(db).get_by_id(checkout_data.address_id, user.id)
                if not addr:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Shipping address not found or does not belong to your account.",
                    )
                customer_name = addr.recipient_name
                customer_email = user.email
                customer_phone = addr.phone
                shipping_address_line1 = addr.address_line1
                shipping_address_line2 = addr.address_line2
                shipping_barangay = addr.barangay
                shipping_city = addr.city
                shipping_province = addr.province
                shipping_postal_code = addr.postal_code
                shipping_country = addr.country or "Philippines"
            else:
                if not (
                    checkout_data.customer_name
                    and checkout_data.customer_email
                    and checkout_data.customer_phone
                    and checkout_data.shipping_address_line1
                    and checkout_data.shipping_city
                    and checkout_data.shipping_province
                    and checkout_data.shipping_postal_code
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Incomplete shipping address. Please provide either a saved address_id or all required address fields.",
                    )
                customer_name = checkout_data.customer_name.strip()
                customer_email = str(checkout_data.customer_email).strip().lower()
                customer_phone = checkout_data.customer_phone.strip()
                shipping_address_line1 = checkout_data.shipping_address_line1.strip()
                shipping_address_line2 = (
                    checkout_data.shipping_address_line2.strip()
                    if checkout_data.shipping_address_line2
                    else None
                )
                shipping_barangay = (
                    checkout_data.shipping_barangay.strip()
                    if checkout_data.shipping_barangay
                    else None
                )
                shipping_city = checkout_data.shipping_city.strip()
                shipping_province = checkout_data.shipping_province.strip()
                shipping_postal_code = checkout_data.shipping_postal_code.strip()
                shipping_country = (
                    checkout_data.shipping_country.strip()
                    if checkout_data.shipping_country
                    else "Philippines"
                )

            notes = checkout_data.notes.strip() if checkout_data.notes else None

            # Step 5: Create Order record
            order_number = generate_unique_order_number(db)

            order = Order(
                order_number=order_number,
                user_id=user.id,
                status=OrderStatus.CONFIRMED.value,
                payment_method=checkout_data.payment_method.value,
                payment_status=PaymentStatus.PENDING.value,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                total_amount=total_amount,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                shipping_address_line1=shipping_address_line1,
                shipping_address_line2=shipping_address_line2,
                shipping_barangay=shipping_barangay,
                shipping_city=shipping_city,
                shipping_province=shipping_province,
                shipping_postal_code=shipping_postal_code,
                shipping_country=shipping_country,
                notes=notes,
                idempotency_key=effective_idempotency_key,
            )
            db.add(order)
            db.flush()  # Populates order.id for OrderItems

            # Step 5: Create immutable OrderItems, deduct stock, and create SALE audit records
            for item_info in validated_items:
                product = item_info["product"]
                inventory = item_info["inventory"]
                qty = item_info["quantity"]

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    product_name=product.name,
                    product_sku=product.sku,
                    product_slug=product.slug,
                    unit_price=item_info["unit_price"],
                    quantity=qty,
                    subtotal=item_info["item_subtotal"],
                )
                db.add(order_item)

                # Deduct inventory stock
                before_qty = inventory.quantity
                inventory.quantity = before_qty - qty
                after_qty = inventory.quantity

                # Create audit transaction record
                sale_tx = InventoryTransaction(
                    product_id=product.id,
                    inventory_id=inventory.id,
                    type=InventoryTransactionType.SALE.value,
                    quantity_change=-qty,
                    quantity_before=before_qty,
                    quantity_after=after_qty,
                    reason=f"Order {order.order_number}",
                    created_by_user_id=user.id,
                )
                db.add(sale_tx)

            # Step 6: Create authoritative Payment record atomically
            from app.modules.payment.service import PaymentService
            PaymentService.create_payment_for_order(
                db=db,
                order=order,
                method=checkout_data.payment_method,
            )

            # Step 7: Clear customer's cart items while preserving Cart entity
            db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(
                synchronize_session=False
            )

            # Step 8: Commit entire atomic transaction
            db.commit()
            db.refresh(order)
            return order

        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Checkout failed due to an internal error: {str(exc)}",
            ) from exc

    @staticmethod
    def cancel_order(
        db: Session,
        user: User,
        order_identifier: str,
        is_admin: bool = False,
    ) -> Order:
        """
        Safely cancels an order:
        - Verifies customer ownership or admin role
        - Validates cancellation eligibility
        - Locks affected inventory rows
        - Restores stock & logs SALE_REVERSAL audit records
        - Updates order status to CANCELLED atomically
        """
        if is_admin:
            if order_identifier.isdigit():
                order = OrderRepository.get_by_id(db, int(order_identifier))
            else:
                order = OrderRepository.get_by_order_number(db, order_identifier)
        else:
            order = OrderRepository.get_customer_order(db, user.id, order_identifier)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )

        # Verify eligibility
        if not is_admin and order.status not in CUSTOMER_CANCELLABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order cannot be cancelled in its current status: '{order.status}'.",
            )

        if order.status in (
            OrderStatus.COMPLETED.value,
            OrderStatus.DELIVERED.value,
            OrderStatus.CANCELLED.value,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel an order that is already '{order.status}'.",
            )

        # Reject cancellation if payment has already been collected/paid
        if (
            (order.payment and order.payment.status == PaymentStatus.PAID.value)
            or order.payment_status == PaymentStatus.PAID.value
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel an order that has already been paid. Please contact customer support.",
            )

        try:
            # Lock inventory rows for items that still have a valid product_id
            product_ids = sorted(list({
                item.product_id for item in order.items if item.product_id is not None
            }))

            if product_ids:
                locked_inventories = (
                    db.query(Inventory)
                    .filter(Inventory.product_id.in_(product_ids))
                    .with_for_update()
                    .all()
                )
                inventory_map = {inv.product_id: inv for inv in locked_inventories}

                for item in order.items:
                    if item.product_id is None:
                        continue
                    inventory = inventory_map.get(item.product_id)
                    if inventory:
                        before_qty = inventory.quantity
                        inventory.quantity = before_qty + item.quantity
                        after_qty = inventory.quantity

                        reversal_tx = InventoryTransaction(
                            product_id=item.product_id,
                            inventory_id=inventory.id,
                            type=InventoryTransactionType.SALE_REVERSAL.value,
                            quantity_change=item.quantity,
                            quantity_before=before_qty,
                            quantity_after=after_qty,
                            reason=f"Order {order.order_number} cancelled",
                            created_by_user_id=user.id,
                        )
                        db.add(reversal_tx)

            # Update order status and record cancellation timestamp
            now = datetime.now(timezone.utc)
            order.status = OrderStatus.CANCELLED.value
            order.cancelled_at = now
            if order.payment_status == PaymentStatus.PENDING.value:
                order.payment_status = PaymentStatus.CANCELLED.value

            # Synchronize payment entity if present
            if order.payment and order.payment.status == PaymentStatus.PENDING.value:
                order.payment.status = PaymentStatus.CANCELLED.value
                order.payment.cancelled_at = now

            db.commit()
            db.refresh(order)
            return order

        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel order: {str(exc)}",
            ) from exc

    @staticmethod
    def update_order_status(
        db: Session,
        admin_user: User,
        order_id: int,
        target_status: OrderStatus,
    ) -> Order:
        """
        Enforces strict state transitions by administrator:
        - PENDING -> CONFIRMED, CANCELLED
        - CONFIRMED -> PROCESSING, CANCELLED
        - PROCESSING -> READY_FOR_FULFILLMENT, CANCELLED
        - READY_FOR_FULFILLMENT -> COMPLETED, CANCELLED
        - COMPLETED -> terminal
        - CANCELLED -> terminal
        If transitioned to CANCELLED, restores inventory and creates SALE_REVERSAL records.
        """
        if admin_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator credentials required.",
            )

        order = OrderRepository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )

        current_status = order.status
        allowed = ALLOWED_STATUS_TRANSITIONS.get(current_status, set())

        if target_status.value not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid status transition from '{current_status}' to '{target_status.value}'. "
                    f"Allowed transitions: {sorted(list(allowed)) if allowed else 'None (Terminal state)'}."
                ),
            )

        # If transitioning to CANCELLED, delegate to atomic cancellation
        if target_status == OrderStatus.CANCELLED:
            return OrderService.cancel_order(
                db=db,
                user=admin_user,
                order_identifier=str(order_id),
                is_admin=True,
            )

        order.status = target_status.value
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def get_customer_order(
        db: Session,
        user: User,
        order_identifier: str,
    ) -> Order:
        order = OrderRepository.get_customer_order(db, user.id, order_identifier)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )
        return order

    @staticmethod
    def list_customer_orders(
        db: Session,
        user: User,
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        orders, total = OrderRepository.list_customer_orders(
            db=db,
            user_id=user.id,
            page=page,
            page_size=page_size,
            status=status_filter,
        )
        pages = math.ceil(total / page_size) if total > 0 else 1
        return {
            "items": orders,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }

    @staticmethod
    def get_admin_order(
        db: Session,
        order_id: int,
    ) -> Order:
        order = OrderRepository.get_by_id(db, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )
        return order

    @staticmethod
    def list_admin_orders(
        db: Session,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        payment_status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        orders, total = OrderRepository.list_admin_orders(
            db=db,
            search=search,
            status=status_filter,
            payment_status=payment_status_filter,
            page=page,
            page_size=page_size,
        )
        pages = math.ceil(total / page_size) if total > 0 else 1
        return {
            "items": orders,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }

    create_order = checkout
