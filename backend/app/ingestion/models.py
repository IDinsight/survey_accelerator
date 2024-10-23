"""This module contains the ORM for managing documents in the database and
database helper functions such as saving, updating, deleting, and retrieving documents.
"""

from datetime import datetime, timezone
from typing import List

from numpy import ndarray
from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from ..models import Base, JSONDict


from app.config import (
    PGVECTOR_DISTANCE,
    PGVECTOR_EF_CONSTRUCTION,
    PGVECTOR_M,
    PGVECTOR_VECTOR_SIZE,
)
from app.utils import setup_logger

logger = setup_logger()


class DocumentDB(Base):
    """ORM for managing document indexing."""

    __tablename__ = "documents"

    __table_args__ = (
        Index(
            "idx_documents_embedding",
            "content_embedding",
            postgresql_using="hnsw",
            postgresql_with={
                "M": PGVECTOR_M,
                "ef_construction": PGVECTOR_EF_CONSTRUCTION,
            },
            postgresql_ops={"content_embedding": PGVECTOR_DISTANCE},
        ),
        Index(
            "idx_documents_fulltext",
            "content_text",
            postgresql_using="gin",
            postgresql_ops={"content_text": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    file_id: Mapped[str] = mapped_column(String(length=36), nullable=False)
    file_name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_embedding: Mapped[Vector] = mapped_column(
        Vector(int(PGVECTOR_VECTOR_SIZE)), nullable=False
    )
    created_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.now(timezone.utc), nullable=False
    )


async def save_document_to_db(
    *,
    processed_pages: List[dict],
    file_id: str,
    file_name: str,
    asession: AsyncSession,
):
    """
    Save documents to the database.
    """
    documents = []
    for page in processed_pages:
        document = DocumentDB(
            file_id=file_id,
            file_name=file_name,
            page_number=page["page_number"],
            content_text=page["contextualized_chunk"],
            content_embedding=page["embedding"],
            created_datetime_utc=datetime.now(timezone.utc),
            updated_datetime_utc=datetime.now(timezone.utc),
        )
        documents.append(document)

    asession.add_all(documents)
    await asession.commit()
