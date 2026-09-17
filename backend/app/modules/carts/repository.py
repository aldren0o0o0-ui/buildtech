from typing import Optional
from sqlalchemy.orm import Session, joinedload

from app.modules.carts.models import Cart, CartItem
from app.modules.products.models import Product


class CartRepository:
    """
    Database persistence operations for Shopping Carts and Cart Items.
    Isolates raw SQLAlchemy queries from business logic.
    """

    @staticmethod
    def get_cart_by_user_id(db: Session, user_id: int) -> Optional[Cart]:
        return (
            db.query(Cart)
            .options(
                joinedload(Cart.items)
                .joinedload(CartItem.product)
                .joinedload(Product.brand)
            )
            .filter(Cart.user_id == user_id)
            .first()
        )

    @staticmethod
    def create_cart(db: Session, user_id: int) -> Cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
        return cart

    @staticmethod
    def get_cart_item(db: Session, cart_id: int, product_id: int) -> Optional[CartItem]:
        return (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
            .first()
        )

    @staticmethod
    def get_cart_item_by_id(db: Session, item_id: int) -> Optional[CartItem]:
        return (
            db.query(CartItem)
            .options(
                joinedload(CartItem.product).joinedload(Product.brand),
                joinedload(CartItem.cart),
            )
            .filter(CartItem.id == item_id)
            .first()
        )

    @staticmethod
    def create_cart_item(
        db: Session, cart_id: int, product_id: int, quantity: int
    ) -> CartItem:
        item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def update_cart_item_quantity(
        db: Session, cart_item: CartItem, quantity: int
    ) -> CartItem:
        cart_item.quantity = quantity
        db.add(cart_item)
        db.commit()
        db.refresh(cart_item)
        return cart_item

    @staticmethod
    def delete_cart_item(db: Session, cart_item: CartItem) -> None:
        db.delete(cart_item)
        db.commit()

    @staticmethod
    def clear_cart_items(db: Session, cart_id: int) -> None:
        db.query(CartItem).filter(CartItem.cart_id == cart_id).delete(
            synchronize_session="fetch"
        )
        db.commit()
