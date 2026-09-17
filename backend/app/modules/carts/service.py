from decimal import Decimal
from typing import List
from app.core import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.carts.models import Cart
from app.modules.carts.repository import CartRepository
from app.modules.carts.schemas import (
    CartItemResponse,
    CartProductBrand,
    CartProductResponse,
    CartResponse,
)
from app.modules.inventory.models import Inventory
from app.modules.products.models import Product, ProductStatus
from app.modules.users.models import User, UserRole


class CartService:
    """
    Business logic for Shopping Cart and Cart Management.
    Enforces product availability, live inventory validation, decimal-safe subtotal
    calculations, customer-ownership isolation, and strict non-reservation of stock.
    """

    @classmethod
    def _verify_customer_role(cls, user: User) -> None:
        if user.role != UserRole.CUSTOMER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only customer accounts can maintain a shopping cart.",
            )

    @classmethod
    def get_or_create_cart(cls, db: Session, user_id: int) -> Cart:
        cart = CartRepository.get_cart_by_user_id(db, user_id)
        if not cart:
            cart = CartRepository.create_cart(db, user_id)
        return cart

    @classmethod
    def build_cart_response(cls, db: Session, cart: Cart) -> CartResponse:
        # Re-fetch cart with eager loads to ensure fresh state
        fresh_cart = CartRepository.get_cart_by_user_id(db, cart.user_id) or cart

        item_responses: List[CartItemResponse] = []
        subtotal = Decimal("0.00")
        total_quantity = 0

        for item in fresh_cart.items:
            product = item.product

            # Query current live inventory
            inventory = (
                db.query(Inventory).filter(Inventory.product_id == product.id).first()
            )
            available_qty = inventory.available_quantity if inventory else 0

            # Evaluate live availability status
            is_product_active = (
                product.is_active and product.status == ProductStatus.ACTIVE.value
            )

            if not is_product_active:
                is_available = False
                avail_status = "PRODUCT_UNAVAILABLE"
                avail_reason = "Product is currently unavailable."
            elif available_qty <= 0:
                is_available = False
                avail_status = "OUT_OF_STOCK"
                avail_reason = "Item is out of stock."
            elif available_qty < item.quantity:
                is_available = False
                avail_status = "INSUFFICIENT_STOCK"
                avail_reason = f"Only {available_qty} units available in stock."
            else:
                is_available = True
                avail_status = "AVAILABLE"
                avail_reason = None

            # Precise Decimal item subtotal
            unit_price = Decimal(str(product.price))
            item_subtotal = unit_price * item.quantity

            # Accumulate totals
            subtotal += item_subtotal
            total_quantity += item.quantity

            brand_data = (
                CartProductBrand(id=product.brand.id, name=product.brand.name)
                if product.brand
                else None
            )

            product_response = CartProductResponse(
                id=product.id,
                name=product.name,
                slug=product.slug,
                sku=product.sku,
                price=unit_price,
                image_url=product.image_url,
                brand=brand_data,
            )

            item_responses.append(
                CartItemResponse(
                    id=item.id,
                    product=product_response,
                    quantity=item.quantity,
                    available_quantity=available_qty,
                    is_available=is_available,
                    availability_status=avail_status,
                    availability_reason=avail_reason,
                    item_subtotal=item_subtotal,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
            )

        return CartResponse(
            id=fresh_cart.id,
            items=item_responses,
            subtotal=subtotal,
            item_count=len(item_responses),
            total_quantity=total_quantity,
            updated_at=fresh_cart.updated_at,
        )

    @classmethod
    def get_cart(cls, db: Session, user: User) -> CartResponse:
        cls._verify_customer_role(user)
        cart = cls.get_or_create_cart(db, user.id)
        return cls.build_cart_response(db, cart)

    @classmethod
    def add_item(
        cls, db: Session, user: User, product_id: int, quantity: int
    ) -> CartResponse:
        cls._verify_customer_role(user)

        if quantity < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Quantity must be at least 1.",
            )

        # Validate product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found.",
            )

        # Validate product visibility
        if not product.is_active or product.status != ProductStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add an inactive or unavailable product to the cart.",
            )

        # Validate available inventory
        inventory = (
            db.query(Inventory).filter(Inventory.product_id == product.id).first()
        )
        available_qty = inventory.available_quantity if inventory else 0

        if available_qty <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add product to cart: item is currently out of stock.",
            )

        cart = cls.get_or_create_cart(db, user.id)
        existing_item = CartRepository.get_cart_item(db, cart.id, product_id)

        target_quantity = (
            (existing_item.quantity + quantity) if existing_item else quantity
        )

        if target_quantity > available_qty:
            if existing_item:
                detail_msg = (
                    f"Cannot add {quantity} units. Only {available_qty} units available in stock "
                    f"({existing_item.quantity} already in your cart)."
                )
            else:
                detail_msg = (
                    f"Cannot add {quantity} units. Only {available_qty} units available in stock."
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail_msg,
            )

        # Upsert cart item (DOES NOT increment inventory.reserved_quantity)
        if existing_item:
            CartRepository.update_cart_item_quantity(
                db, existing_item, target_quantity
            )
        else:
            CartRepository.create_cart_item(db, cart.id, product_id, quantity)

        return cls.build_cart_response(db, cart)

    @classmethod
    def update_item(
        cls, db: Session, user: User, item_id: int, quantity: int
    ) -> CartResponse:
        cls._verify_customer_role(user)

        if quantity < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Quantity must be at least 1.",
            )

        cart_item = CartRepository.get_cart_item_by_id(db, item_id)
        # Ownership isolation: Return 404 to avoid leaking whether another user's item exists
        if not cart_item or cart_item.cart.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found.",
            )

        product = cart_item.product
        if not product.is_active or product.status != ProductStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update quantity for an unavailable product.",
            )

        inventory = (
            db.query(Inventory).filter(Inventory.product_id == product.id).first()
        )
        available_qty = inventory.available_quantity if inventory else 0

        if quantity > available_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot set quantity to {quantity}. Only {available_qty} units available in stock.",
            )

        CartRepository.update_cart_item_quantity(db, cart_item, quantity)
        cart = CartRepository.get_cart_by_user_id(db, user.id)
        return cls.build_cart_response(db, cart)

    @classmethod
    def remove_item(cls, db: Session, user: User, item_id: int) -> CartResponse:
        cls._verify_customer_role(user)

        cart_item = CartRepository.get_cart_item_by_id(db, item_id)
        if not cart_item or cart_item.cart.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found.",
            )

        CartRepository.delete_cart_item(db, cart_item)
        cart = CartRepository.get_cart_by_user_id(db, user.id)
        return cls.build_cart_response(db, cart)

    @classmethod
    def clear_cart(cls, db: Session, user: User) -> CartResponse:
        cls._verify_customer_role(user)

        cart = cls.get_or_create_cart(db, user.id)
        CartRepository.clear_cart_items(db, cart.id)
        return cls.build_cart_response(db, cart)
