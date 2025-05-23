"""This module contains the ORM for managing feedback in the database."""

from datetime import datetime, timezone
from typing import Optional

from app.models import Base
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class FeedbackDB(Base):
    """ORM for storing user feedback."""

    __tablename__ = "feedback"

    feedback_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    feedback_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # 'like' or 'dislike'
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    search_term: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship to user
    user = relationship("UsersDB", backref="feedback")
