import enum
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    READY_FOR_FULFILLMENT = "READY_FOR_FULFILLMENT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, enum.Enum):
    COD = "COD"
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"
    MANUAL = "MANUAL"


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="check_order_subtotal_non_negative"),
        CheckConstraint("shipping_fee >= 0", name="check_order_shipping_non_negative"),
        CheckConstraint("total_amount >= 0", name="check_order_total_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    status = Column(
        String(50),
        default=OrderStatus.CONFIRMED.value,
        nullable=False,
        index=True,
    )
    payment_method = Column(
        String(50),
        default=PaymentMethod.COD.value,
        nullable=False,
    )
    payment_status = Column(
        String(50),
        default=PaymentStatus.PENDING.value,
        nullable=False,
        index=True,
    )

    subtotal = Column(Numeric(10, 2), nullable=False)
    shipping_fee = Column(Numeric(10, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)

    # Customer snapshot (historical immutability)
    customer_name = Column(String(200), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_phone = Column(String(50), nullable=False)

    # Shipping snapshot (historical immutability)
    shipping_address_line1 = Column(String(255), nullable=False)
    shipping_address_line2 = Column(String(255), nullable=True)
    shipping_barangay = Column(String(100), nullable=True)
    shipping_city = Column(String(100), nullable=False)
    shipping_province = Column(String(100), nullable=False)
    shipping_postal_code = Column(String(20), nullable=False)
    shipping_country = Column(String(100), nullable=False, default="Philippines")

    notes = Column(Text, nullable=True)

    # Idempotency key for duplicate prevention
    idempotency_key = Column(String(100), unique=True, index=True, nullable=True)

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
    cancelled_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderItem.id.asc()",
    )
    payment = relationship(
        "Payment",
        back_populates="order",
        uselist=False,
    )

    @property
    def recipient_name(self) -> str:
        return self.customer_name

    @property
    def recipient_phone(self) -> str:
        return self.customer_phone

    @property
    def shipping_address_line(self) -> str:
        return self.shipping_address_line1


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity >= 1", name="check_order_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="check_order_item_unit_price_non_negative"),
        CheckConstraint("subtotal >= 0", name="check_order_item_subtotal_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    # Immutable product snapshots taken at checkout
    product_name = Column(String(200), nullable=False)
    product_sku = Column(String(50), nullable=False)
    product_slug = Column(String(220), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    subtotal = Column(Numeric(10, 2), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    @property
    def sku(self) -> str:
        return self.product_sku
