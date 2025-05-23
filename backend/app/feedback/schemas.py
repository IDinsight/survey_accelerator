"""This module contains the Pydantic models for feedback data validation and serialization."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    """Schema for creating a new feedback entry."""

    feedback_type: str  # 'like' or 'dislike'
    comment: Optional[str] = None
    search_term: str


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""

    message: str
    feedback_id: int


class FeedbackOut(BaseModel):
    """Schema for returning feedback data."""

    feedback_id: int
    user_id: int
    feedback_type: str
    comment: Optional[str] = None
    search_term: str
    created_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True
