from typing import Optional, Tuple
from sqlalchemy.orm import Session, joinedload

from app.modules.products.models import Product
from app.modules.wishlist.models import Wishlist, WishlistItem


class WishlistRepository:
    """
    Data access repository for Wishlist and WishlistItems.
    Encapsulates database operations and eager loading strategies.
    """

    @classmethod
    def get_wishlist_by_user_id(cls, db: Session, user_id: int) -> Optional[Wishlist]:
        """
        Retrieves a user's wishlist with eager-loaded items and full product details
        to avoid N+1 query overhead.
        """
        return (
            db.query(Wishlist)
            .filter(Wishlist.user_id == user_id)
            .options(
                joinedload(Wishlist.items)
                .joinedload(WishlistItem.product)
                .joinedload(Product.brand),
                joinedload(Wishlist.items)
                .joinedload(WishlistItem.product)
                .joinedload(Product.category),
                joinedload(Wishlist.items)
                .joinedload(WishlistItem.product)
                .joinedload(Product.inventory),
            )
            .first()
        )

    @classmethod
    def create_wishlist(cls, db: Session, user_id: int) -> Wishlist:
        """
        Initializes an empty wishlist for a customer.
        """
        wishlist = Wishlist(user_id=user_id)
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)
        return wishlist

    @classmethod
    def get_wishlist_item(
        cls, db: Session, wishlist_id: int, product_id: int
    ) -> Optional[WishlistItem]:
        """
        Retrieves a specific wishlist item by wishlist_id and product_id.
        """
        return (
            db.query(WishlistItem)
            .filter(
                WishlistItem.wishlist_id == wishlist_id,
                WishlistItem.product_id == product_id,
            )
            .first()
        )

    @classmethod
    def get_item_by_id(cls, db: Session, item_id: int) -> Optional[WishlistItem]:
        """
        Retrieves a wishlist item by its primary key id.
        """
        return (
            db.query(WishlistItem)
            .filter(WishlistItem.id == item_id)
            .options(joinedload(WishlistItem.wishlist))
            .first()
        )

    @classmethod
    def add_item(cls, db: Session, wishlist_id: int, product_id: int) -> WishlistItem:
        """
        Inserts a new product entry into a customer's wishlist.
        """
        item = WishlistItem(wishlist_id=wishlist_id, product_id=product_id)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def remove_item(cls, db: Session, item: WishlistItem) -> None:
        """
        Deletes an item from the customer's wishlist.
        """
        db.delete(item)
        db.commit()

    @classmethod
    def check_product_wishlisted(
        cls, db: Session, user_id: int, product_id: int
    ) -> Tuple[bool, Optional[int]]:
        """
        Performs a lightweight existence query to verify if a product is saved in the user's
        wishlist without loading full wishlist entities or product collections.
        """
        item = (
            db.query(WishlistItem.id)
            .join(Wishlist, WishlistItem.wishlist_id == Wishlist.id)
            .filter(
                Wishlist.user_id == user_id,
                WishlistItem.product_id == product_id,
            )
            .first()
        )
        if item:
            return True, item[0]
        return False, None
