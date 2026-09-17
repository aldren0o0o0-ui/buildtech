from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.modules.reviews.models import ReviewStatus


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 (poor) to 5 (excellent)")
    title: str = Field(..., min_length=2, max_length=150, description="Brief summary of review")
    comment: str = Field(..., min_length=5, max_length=2000, description="Detailed customer review text")

    model_config = ConfigDict(extra="forbid")


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Updated rating 1-5")
    title: Optional[str] = Field(None, min_length=2, max_length=150, description="Updated headline")
    comment: Optional[str] = Field(None, min_length=5, max_length=2000, description="Updated review text")

    model_config = ConfigDict(extra="forbid")


class ReviewRead(BaseModel):
    id: int
    product_id: int
    rating: int
    title: str
    comment: str
    is_verified_purchase: bool
    author_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewAdminRead(ReviewRead):
    user_id: int
    user_email: Optional[str] = None
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class ReviewSummaryResponse(BaseModel):
    average_rating: float
    total_reviews: int
    rating_distribution: Dict[str, int]

    model_config = ConfigDict(from_attributes=True)


class ReviewListResponse(BaseModel):
    items: List[ReviewRead]
    total: int
    page: int
    page_size: int
    total_pages: int
    summary: Optional[ReviewSummaryResponse] = None

    model_config = ConfigDict(from_attributes=True)


class MyReviewResponse(BaseModel):
    can_review: bool
    has_reviewed: bool
    review: Optional[ReviewRead] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewStatusUpdate(BaseModel):
    status: ReviewStatus = Field(..., description="Target review status (PUBLISHED or HIDDEN)")

    model_config = ConfigDict(extra="forbid")
