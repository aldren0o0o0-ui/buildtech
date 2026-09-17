import enum
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class ReviewStatus(str, enum.Enum):
    PUBLISHED = "PUBLISHED"
    HIDDEN = "HIDDEN"


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_review_rating_range"),
        UniqueConstraint("user_id", "product_id", name="uq_user_product_review"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rating = Column(Integer, nullable=False)
    title = Column(String(150), nullable=False)
    comment = Column(Text, nullable=False)
    is_verified_purchase = Column(Boolean, default=True, nullable=False)
    status = Column(
        String(20),
        default=ReviewStatus.PUBLISHED.value,
        nullable=False,
        index=True,
    )

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
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")

    @property
    def author_name(self) -> str:
        """Safe public representation of customer identity (e.g. 'Jane D.')."""
        if not self.user:
            return "Verified Customer"
        last_initial = f"{self.user.last_name[0]}." if self.user.last_name else ""
        return f"{self.user.first_name} {last_initial}".strip()
