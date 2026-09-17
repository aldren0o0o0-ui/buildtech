from decimal import Decimal
from typing import List
from app.core import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.products.models import Product, ProductStatus
from app.modules.users.models import User, UserRole
from app.modules.wishlist.models import Wishlist
from app.modules.wishlist.repository import WishlistRepository
from app.modules.wishlist.schemas import (
    WishlistCheckResponse,
    WishlistItemResponse,
    WishlistProductBrand,
    WishlistProductCategory,
    WishlistProductResponse,
    WishlistResponse,
)


class WishlistService:
    """
    Business logic for Customer Wishlist Management.
    Enforces customer role isolation, product visibility rules, live stock availability
    calculation (read-only with respect to inventory), and duplicate protection.
    """

    @classmethod
    def _verify_customer_role(cls, user: User) -> None:
        if user.role != UserRole.CUSTOMER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Customer privileges required.",
            )

    @classmethod
    def get_or_create_wishlist(cls, db: Session, user_id: int) -> Wishlist:
        """
        Retrieves the customer's wishlist, lazily initializing one if not present.
        """
        wishlist = WishlistRepository.get_wishlist_by_user_id(db, user_id)
        if not wishlist:
            wishlist = WishlistRepository.create_wishlist(db, user_id)
        return wishlist

    @classmethod
    def build_wishlist_response(cls, db: Session, wishlist: Wishlist) -> WishlistResponse:
        """
        Constructs a structured WishlistResponse with fresh live availability calculations.
        Does not mutate inventory.
        """
        # Re-fetch wishlist with eager-loaded relations to guarantee freshest state
        fresh_wishlist = (
            WishlistRepository.get_wishlist_by_user_id(db, wishlist.user_id)
            or wishlist
        )

        item_responses: List[WishlistItemResponse] = []

        for item in fresh_wishlist.items:
            product = item.product

            # Evaluate product active status
            is_product_active = (
                product.is_active and product.status == ProductStatus.ACTIVE.value
            )

            # Evaluate live availability status
            if not is_product_active:
                is_available = False
                avail_status = "UNAVAILABLE"
            else:
                inventory = product.inventory
                available_qty = inventory.available_quantity if inventory else 0
                if available_qty > 0:
                    is_available = True
                    avail_status = "IN_STOCK"
                else:
                    is_available = False
                    avail_status = "OUT_OF_STOCK"

            brand_data = (
                WishlistProductBrand(
                    id=product.brand.id,
                    name=product.brand.name,
                    slug=product.brand.slug,
                )
                if product.brand
                else None
            )

            category_data = (
                WishlistProductCategory(
                    id=product.category.id,
                    name=product.category.name,
                    slug=product.category.slug,
                )
                if product.category
                else None
            )

            product_response = WishlistProductResponse(
                id=product.id,
                name=product.name,
                slug=product.slug,
                sku=product.sku,
                price=Decimal(str(product.price)),
                image_url=product.image_url,
                status=product.status,
                is_active=product.is_active,
                brand=brand_data,
                category=category_data,
                availability_status=avail_status,
                is_available=is_available,
            )

            item_responses.append(
                WishlistItemResponse(
                    id=item.id,
                    product_id=product.id,
                    product=product_response,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
            )

        return WishlistResponse(
            id=fresh_wishlist.id,
            user_id=fresh_wishlist.user_id,
            items=item_responses,
            item_count=len(item_responses),
            created_at=fresh_wishlist.created_at,
            updated_at=fresh_wishlist.updated_at,
        )

    @classmethod
    def get_wishlist(cls, db: Session, user: User) -> WishlistResponse:
        """
        Retrieves the authenticated customer's wishlist.
        """
        cls._verify_customer_role(user)
        wishlist = cls.get_or_create_wishlist(db, user.id)
        return cls.build_wishlist_response(db, wishlist)

    @classmethod
    def add_item(cls, db: Session, user: User, product_id: int) -> WishlistResponse:
        """
        Adds a product to the customer's wishlist.
        Idempotent: if product is already in the wishlist, returns current wishlist without error.
        Validates product existence and storefront visibility.
        """
        cls._verify_customer_role(user)

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found.",
            )

        # Inactive or draft products cannot be newly added
        if not product.is_active or product.status != ProductStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add inactive or draft product to wishlist.",
            )

        wishlist = cls.get_or_create_wishlist(db, user.id)

        # Check whether item is already present (application-level idempotency)
        existing_item = WishlistRepository.get_wishlist_item(db, wishlist.id, product.id)
        if existing_item:
            return cls.build_wishlist_response(db, wishlist)

        # Insert item with database unique constraint safety
        try:
            WishlistRepository.add_item(db, wishlist.id, product.id)
        except IntegrityError:
            db.rollback()
            # Already added concurrently

        return cls.build_wishlist_response(db, wishlist)

    @classmethod
    def remove_item(cls, db: Session, user: User, item_id: int) -> WishlistResponse:
        """
        Removes an item from the customer's wishlist.
        Enforces ownership isolation: returns 404 if item does not exist or belongs to another user.
        """
        cls._verify_customer_role(user)

        item = WishlistRepository.get_item_by_id(db, item_id)
        if not item or item.wishlist.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wishlist item not found.",
            )

        wishlist = item.wishlist
        WishlistRepository.remove_item(db, item)
        return cls.build_wishlist_response(db, wishlist)

    @classmethod
    def check_product(
        cls, db: Session, user: User, product_id: int
    ) -> WishlistCheckResponse:
        """
        Lightweight check returning whether a product is currently in the customer's wishlist.
        """
        cls._verify_customer_role(user)
        is_wishlisted, item_id = WishlistRepository.check_product_wishlisted(
            db, user.id, product_id
        )
        return WishlistCheckResponse(
            product_id=product_id,
            is_wishlisted=is_wishlisted,
            wishlist_item_id=item_id,
        )
