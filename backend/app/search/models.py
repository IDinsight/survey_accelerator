from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.users.models import UsersDB
from app.utils import setup_logger

from ..models import Base

logger = setup_logger()


# Add this to your models.py
class SearchLogDB(Base):
    """ORM for logging searches performed on the document database."""

    __tablename__ = "search_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )
    search_response: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Nullable because MCP callers may be anonymous. Web app searches always
    # carry a user.
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    # "web" or "mcp".
    source: Mapped[Optional[str]] = mapped_column(String(length=20), nullable=True)
    # Only recorded for MCP calls, where it is what the anonymous rate limit
    # counts against.
    client_ip: Mapped[Optional[str]] = mapped_column(String(length=64), nullable=True)

    def __repr__(self) -> str:
        """Return a string representation of the object."""
        return f"""<SearchLog(id={self.id}, query='{self.query}', \
            timestamp='{self.timestamp}')>"""


async def log_search(
    asession: AsyncSession,
    user: Optional[UsersDB],
    query: str,
    search_response: dict,
    source: str = "web",
    client_ip: Optional[str] = None,
) -> None:
    """
    Log a search performed on the document database.

    `user` is None for anonymous MCP callers; the search is still recorded so
    usage is visible even when it cannot be attributed to a person.
    """
    try:
        search_log = SearchLogDB(
            query=query,
            timestamp=datetime.now(timezone.utc),
            search_response=search_response,
            user_id=user.user_id if user else None,
            source=source,
            client_ip=client_ip,
        )
        asession.add(search_log)
        await asession.commit()
        logger.info(f"Logged search for query: '{query}'")
    except Exception as e:
        logger.error(f"Failed to log search for query: '{query}': {e}")
        await asession.rollback()
