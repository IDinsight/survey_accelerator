from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Integer, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.utils import setup_logger

from ..models import Base

logger = setup_logger()


# Add this to your models.py
class SearchLogDB(Base):
    """ORM for logging searches performed on the document database."""

    __tablename__ = "search_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    precision: Mapped[bool] = mapped_column(Boolean, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )
    search_response: Mapped[dict] = mapped_column(JSON, nullable=False)

    def __repr__(self) -> str:
        """Return a string representation of the object."""
        return f"""<SearchLog(id={self.id}, query='{self.query}', \
            timestamp='{self.timestamp}', precision={self.precision})>"""


async def log_search(
    asession: AsyncSession,
    query: str,
    search_response: dict,
    precision: bool,
) -> None:
    """
    Log a search performed on the document database.
    """
    try:
        search_log = SearchLogDB(
            query=query,
            precision=precision,
            timestamp=datetime.now(timezone.utc),
            search_response=search_response,
        )
        asession.add(search_log)
        await asession.commit()
        logger.info(f"Logged search for query: '{query}' with precision={precision}")
    except Exception as e:
        logger.error(f"Failed to log search for query: '{query}': {e}")
        await asession.rollback()
