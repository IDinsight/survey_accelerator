"""This module contains the ORM for managing documents in the database and
database helper functions such as saving, updating, deleting, and retrieving documents.
"""

from datetime import datetime, timezone
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.config import (
    PGVECTOR_DISTANCE,
    PGVECTOR_EF_CONSTRUCTION,
    PGVECTOR_M,
    PGVECTOR_VECTOR_SIZE,
)
from app.ingestion.utils.file_processing_utils import create_metadata_string
from app.utils import setup_logger

from ..models import Base

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

    countries: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    organizations: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    regions: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    drive_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    date_added: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    document_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=False)


async def save_document_to_db(
    *,
    processed_pages: list[dict],
    file_id: str,
    file_name: str,
    asession: AsyncSession,
    metadata: dict,
) -> None:
    """
    Save documents to the database.
    """

    # Process metadata fields
    date_added_str = metadata.get("Date added")
    if date_added_str:
        date_added = datetime.strptime(date_added_str, "%Y-%m-%d")
    else:
        date_added = None

    countries = metadata.get("Countries", [])
    organizations = metadata.get("Organization(s)", [])
    regions = metadata.get("Region(s)", [])
    notes = metadata.get("Notes", "")
    drive_link = metadata.get("Drive link", "")
    year = metadata.get("Year", None)
    document_id = metadata.get("ID", None)

    # Create metadata string to include in content_text
    metadata_string = create_metadata_string(metadata)

    documents = []
    for page in processed_pages:
        # Include metadata in content_text under a section
        content_text = (
            "Information about this document:\n"
            + metadata_string
            + "\n\n"
            + page["contextualized_chunk"]
        )

        document = DocumentDB(
            file_id=file_id,
            file_name=file_name,
            page_number=page["page_number"],
            content_text=content_text,
            content_embedding=page["embedding"],
            created_datetime_utc=datetime.now(timezone.utc),
            updated_datetime_utc=datetime.now(timezone.utc),
            countries=countries,
            organizations=organizations,
            regions=regions,
            notes=notes,
            drive_link=drive_link,
            year=year,
            date_added=date_added,
            document_id=document_id,
        )
        documents.append(document)

    asession.add_all(documents)
    await asession.commit()
