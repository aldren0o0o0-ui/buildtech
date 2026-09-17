from decimal import Decimal
from typing import List
from app.core import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.addresses.repository import AddressRepository
from app.modules.addresses.schemas import AddressResponse
from app.modules.carts.repository import CartRepository
from app.modules.checkout.schemas import (
    CheckoutIssue,
    CheckoutItemPreview,
    CheckoutValidationResponse,
)
from app.modules.checkout.shipping import ShippingService
from app.modules.products.models import ProductStatus


class CheckoutService:
    def __init__(self, db: Session):
        self.db = db
        self.address_repo = AddressRepository(db)

    def validate_checkout(self, user_id: int, address_id: int) -> CheckoutValidationResponse:

        """
        Non-destructive checkout validation pipeline:
        1. Validates address exists and belongs to the customer (404 if unauthorized).
        2. Re-reads the customer's cart from the database.
        3. Verifies cart is non-empty.
        4. Re-reads authoritative product active status, prices, and available inventory.
        5. Computes authoritative Decimal subtotals, shipping fee, tax, and total.
        6. Returns structured checkout preview with validation status and specific issues.

        CRITICAL ARCHITECTURAL INVARIANT:
        This operation NEVER reserves stock, mutates inventory, clears cart, or creates orders.
        """
        # 1. Validate shipping address ownership
        address = self.address_repo.get_by_id(address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found",
            )

        address_response = AddressResponse.model_validate(address)

        # 2. Re-read customer cart
        cart = CartRepository.get_cart_by_user_id(self.db, user_id)
        if not cart or not cart.items:

            return CheckoutValidationResponse(
                valid=False,
                address=address_response,
                items=[],
                subtotal=Decimal("0.00"),
                shipping_fee=Decimal("0.00"),
                tax=Decimal("0.00"),
                total=Decimal("0.00"),
                issues=[
                    CheckoutIssue(
                        code="EMPTY_CART",
                        message="Your cart is empty. Please add items before proceeding to checkout.",
                    )
                ],
            )

        # 3. Validate items, pricing, and inventory
        issues: List[CheckoutIssue] = []
        preview_items: List[CheckoutItemPreview] = []
        subtotal = Decimal("0.00")

        for item in cart.items:
            product = item.product

            if not product:
                issues.append(
                    CheckoutIssue(
                        code="PRODUCT_NOT_FOUND",
                        product_id=item.product_id,
                        message="A product in your cart is no longer available in the catalog.",
                    )
                )
                continue

            # Check product publication & active status
            is_active = (
                product.is_active
                and product.status == ProductStatus.ACTIVE.value
            )

            # Check live inventory stock
            inv = product.inventory
            available_qty = max(0, inv.quantity - inv.reserved_quantity) if inv else 0

            # Determine item availability state & issues
            if not is_active:
                item_status = "PRODUCT_UNAVAILABLE"
                is_available = False
                issues.append(
                    CheckoutIssue(
                        code="PRODUCT_UNAVAILABLE",
                        product_id=product.id,
                        product_name=product.name,
                        message=f"{product.name} is currently inactive or unavailable for purchase.",
                    )
                )
            elif available_qty <= 0:
                item_status = "OUT_OF_STOCK"
                is_available = False
                issues.append(
                    CheckoutIssue(
                        code="OUT_OF_STOCK",
                        product_id=product.id,
                        product_name=product.name,
                        requested_quantity=item.quantity,
                        available_quantity=0,
                        message=f"{product.name} is out of stock.",
                    )
                )
            elif available_qty < item.quantity:
                item_status = "INSUFFICIENT_STOCK"
                is_available = False
                issues.append(
                    CheckoutIssue(
                        code="INSUFFICIENT_STOCK",
                        product_id=product.id,
                        product_name=product.name,
                        requested_quantity=item.quantity,
                        available_quantity=available_qty,
                        message=f"Only {available_qty} unit(s) available in stock for {product.name} (requested {item.quantity}).",
                    )
                )
            else:
                item_status = "AVAILABLE"
                is_available = True

            # Server-authoritative monetary calculations
            unit_price = Decimal(str(product.price))
            item_subtotal = (unit_price * Decimal(item.quantity)).quantize(Decimal("0.01"))
            subtotal += item_subtotal

            preview_items.append(
                CheckoutItemPreview(
                    cart_item_id=item.id,
                    product_id=product.id,
                    product_name=product.name,
                    sku=product.sku,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    item_subtotal=item_subtotal,
                    available_quantity=available_qty,
                    is_available=is_available,
                    status=item_status,
                )
            )

        # Authoritative shipping & tax calculations
        subtotal = subtotal.quantize(Decimal("0.01"))
        shipping_fee = ShippingService.calculate_shipping_fee(subtotal, address).quantize(Decimal("0.01"))
        tax = Decimal("0.00").quantize(Decimal("0.01"))
        total = (subtotal + shipping_fee + tax).quantize(Decimal("0.01"))

        is_valid = len(issues) == 0 and len(preview_items) > 0

        return CheckoutValidationResponse(
            valid=is_valid,
            address=address_response,
            items=preview_items,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            tax=tax,
            total=total,
            issues=issues,
        )
