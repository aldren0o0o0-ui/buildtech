import enum
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, enum.Enum):
    CASH_ON_DELIVERY = "CASH_ON_DELIVERY"
    COD = "COD"


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="check_payment_amount_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="RESTRICT"),
        unique=True,
        index=True,
        nullable=False,
    )
    payment_reference = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    method = Column(
        String(50),
        default=PaymentMethod.CASH_ON_DELIVERY.value,
        nullable=False,
        index=True,
    )
    status = Column(
        String(50),
        default=PaymentStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="PHP", nullable=False)
    provider = Column(String(50), default="COD", nullable=False)
    provider_payment_id = Column(String(100), nullable=True)

    paid_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    order = relationship("Order", back_populates="payment")
