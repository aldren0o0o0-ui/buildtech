import enum
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class ProductStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    slug = Column(String(220), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(String(500), nullable=True)
    status = Column(String(20), default=ProductStatus.ACTIVE.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Core Relationships
    category = relationship("Category", back_populates="products")
    brand = relationship("Brand", back_populates="products")

    # Module 4 One-to-One Specification Relationships (cascade delete-orphan)
    cpu_spec = relationship(
        "CpuSpecification",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    gpu_spec = relationship(
        "GpuSpecification",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    motherboard_spec = relationship(
        "MotherboardSpecification",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    memory_spec = relationship(
        "MemorySpecification",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    storage_spec = relationship(
        "StorageSpecification",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    psu_spec = relationship(
        "PsuSpecification",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    case_spec = relationship(
        "CaseSpecification",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    cooling_spec = relationship(
        "CoolingSpecification",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Module 5 Inventory Relationships (cascade delete-orphan)
    inventory = relationship(
        "Inventory",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    inventory_transactions = relationship(
        "InventoryTransaction",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    # Module 6 Cart Items Relationship (cascade delete-orphan)
    cart_items = relationship(
        "CartItem",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    # Module 7 Wishlist Items Relationship (cascade delete-orphan)
    wishlist_items = relationship(
        "WishlistItem",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    # Module 7 Order Items Relationship (SET NULL on product deletion, preserve history)
    order_items = relationship(
        "OrderItem",
        back_populates="product",
    )

    # Module 12 Reviews Relationship
    reviews = relationship(
        "Review",
        back_populates="product",
        cascade="all, delete-orphan",
    )


