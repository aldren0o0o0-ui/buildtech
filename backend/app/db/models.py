"""
BuildTech Model Registry for Database & Alembic Migration Discovery.

All SQLAlchemy ORM models from across domain feature modules are explicitly
imported here to ensure they register with Base.metadata.
"""

from app.db.session import Base
from app.modules.carts.models import Cart, CartItem
from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
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
from app.modules.payment.models import (
    Payment,
    PaymentMethod as PaymentDomainMethod,
    PaymentStatus as PaymentDomainStatus,
)
from app.modules.products.models import Product, ProductStatus
from app.modules.products.specifications.models import (
    CaseSpecification,
    CoolingSpecification,
    CpuSpecification,
    GpuSpecification,
    MemorySpecification,
    MotherboardSpecification,
    PsuSpecification,
    StorageSpecification,
)
from app.modules.addresses.models import Address
from app.modules.reviews.models import Review, ReviewStatus
from app.modules.users.models import User, UserRole
from app.modules.wishlist.models import Wishlist, WishlistItem

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Address",
    "Category",
    "Brand",
    "Product",
    "ProductStatus",
    "CpuSpecification",
    "GpuSpecification",
    "MotherboardSpecification",
    "MemorySpecification",
    "StorageSpecification",
    "PsuSpecification",
    "CaseSpecification",
    "CoolingSpecification",
    "Inventory",
    "InventoryTransaction",
    "InventoryTransactionType",
    "Cart",
    "CartItem",
    "Wishlist",
    "WishlistItem",
    "Order",
    "OrderItem",
    "OrderStatus",
    "PaymentStatus",
    "PaymentMethod",
    "Payment",
    "Review",
    "ReviewStatus",
]


