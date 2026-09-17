import enum
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class InventoryTransactionType(str, enum.Enum):
    STOCK_IN = "STOCK_IN"
    ADJUSTMENT_IN = "ADJUSTMENT_IN"
    ADJUSTMENT_OUT = "ADJUSTMENT_OUT"
    SALE = "SALE"
    SALE_REVERSAL = "SALE_REVERSAL"


class Inventory(Base):
    __tablename__ = "inventories"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="check_inventory_quantity_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="check_inventory_reserved_non_negative"),
        CheckConstraint("low_stock_threshold >= 0", name="check_inventory_threshold_non_negative"),
        CheckConstraint("reserved_quantity <= quantity", name="check_inventory_reserved_lte_quantity"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=5, nullable=False)
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

    # Relationships
    product = relationship("Product", back_populates="inventory")
    transactions = relationship(
        "InventoryTransaction",
        back_populates="inventory",
        cascade="all, delete-orphan",
    )

    @property
    def available_quantity(self) -> int:
        return max(0, self.quantity - self.reserved_quantity)

    @property
    def availability_status(self) -> str:
        avail = self.available_quantity
        if avail <= 0:
            return "OUT_OF_STOCK"
        elif avail <= self.low_stock_threshold:
            return "LOW_STOCK"
        return "IN_STOCK"


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    inventory_id = Column(
        Integer,
        ForeignKey("inventories.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type = Column(String(50), nullable=False)
    quantity_change = Column(Integer, nullable=False)
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=True)
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    product = relationship("Product", back_populates="inventory_transactions")
    inventory = relationship("Inventory", back_populates="transactions")
    created_by = relationship("User")
