import enum
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(20), default=UserRole.CUSTOMER.value, nullable=False)
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

    # Module 6 Cart Relationship (1:1 with Cart, cascade delete-orphan)
    cart = relationship(
        "Cart",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Module 7 Wishlist Relationship (1:1 with Wishlist, cascade delete-orphan)
    wishlist = relationship(
        "Wishlist",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Module 7 Orders Relationship
    orders = relationship("Order", back_populates="user")

    # Module 9 Addresses Relationship (1:N with Address, cascade delete-orphan)
    addresses = relationship(
        "Address",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Address.created_at.desc()",
    )

    # Module 12 Reviews Relationship
    reviews = relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Review.created_at.desc()",
    )


