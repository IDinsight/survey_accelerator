"""This module contains the ORM for managing documents in the database and
database helper functions such as saving, updating, deleting, and retrieving documents.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import (
    PGVECTOR_DISTANCE,
    PGVECTOR_EF_CONSTRUCTION,
    PGVECTOR_M,
    PGVECTOR_VECTOR_SIZE,
)
from app.database import get_async_session
from app.utils import setup_logger

from ..models import Base

logger = setup_logger()

# Maximum number of concurrent database operations
MAX_CONCURRENT_DB_TASKS = 5


class QAPairDB(Base):
    """ORM for managing question-answer pairs associated with each document."""

    __tablename__ = "qa_pairs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    # Define relationship back to DocumentDB
    document = relationship("DocumentDB", back_populates="qa_pairs")


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
            "contextualized_chunk",
            postgresql_using="gin",
            postgresql_ops={"contextualized_chunk": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(length=150), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    contextualized_chunk: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_summary: Mapped[str] = mapped_column(Text, nullable=False)
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
    drive_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    date_added: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    document_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=False)
    qa_pairs = relationship(
        "QAPairDB", back_populates="document", cascade="all, delete-orphan"
    )


async def save_document_to_db(
    *,
    processed_pages: list[dict],
    file_name: str,
    asession: AsyncSession,
    metadata: dict,
    pdf_url: str,
    summary: str,
    title: str,
    document_id: int,
) -> None:
    """
    Save documents and their associated QA pairs to the database.
    """
    logger.debug(f"Starting save_document_to_db for file '{file_name}'.")

    # Process metadata fields
    try:
        date_added_str = metadata.get("Date added")
        date_added = (
            datetime.strptime(date_added_str, "%Y-%m-%d") if date_added_str else None
        )

        countries = metadata.get("Countries", [])
        organizations = metadata.get("Organization(s)", [])
        regions = metadata.get("Region(s)", [])
        drive_link = metadata.get("Drive link", "")
        year = metadata.get("Year", None)
        document_id = metadata.get("ID", None)
    except Exception as e:
        logger.error(f"Error processing metadata for file '{file_name}': {e}")
        raise

    # Process pages one by one to avoid transaction issues
    for idx, page in enumerate(processed_pages):
        logger.debug(f"Processing page {idx + 1}/{len(processed_pages)}.")

        try:
            # Create DocumentDB instance for each page
            document = DocumentDB(
                file_name=file_name,
                page_number=page["page_number"],
                contextualized_chunk=page["contextualized_chunk"],
                chunk_summary=page["chunk_summary"],
                content_embedding=page["embedding"],
                created_datetime_utc=datetime.now(timezone.utc),
                updated_datetime_utc=datetime.now(timezone.utc),
                countries=countries,
                organizations=organizations,
                regions=regions,
                drive_link=drive_link,
                year=year,
                date_added=date_added,
                document_id=document_id,  # Using the document_id passed to the function
                pdf_url=pdf_url,
                summary=summary,
                title=title,
            )

            # Create QAPairDB instances and associate them with the document
            extracted_qa_pairs = page.get("extracted_question_answers", [])
            if not isinstance(extracted_qa_pairs, list):
                logger.warning(
                    f"extracted_question_answers is not a list on page {idx + 1}."
                )
                extracted_qa_pairs = []

            qa_pairs = []
            for _, qa_pair in enumerate(extracted_qa_pairs):
                try:
                    question = qa_pair.get("question", "")
                    answers = qa_pair.get("answers", [])

                    # Ensure answers is a list
                    if not isinstance(answers, list):
                        answers = [answers]

                    # Convert answers list to a string
                    answer_text = ", ".join(answers)

                    qa_pair_instance = QAPairDB(
                        question=question,
                        answer=answer_text,
                    )

                    qa_pairs.append(qa_pair_instance)
                except Exception as e:
                    logger.error(f"Error processing QA pair on page {idx + 1}: {e}")

            document.qa_pairs = qa_pairs

            # Add document to session and commit immediately
            asession.add(document)
            await asession.commit()
            logger.debug(f"Saved page {idx + 1} for file '{file_name}'")

        except Exception as e:
            logger.error(f"Error saving page {idx + 1} for file '{file_name}': {e}")
            await asession.rollback()
            # Continue with next page

    logger.debug(f"Finished save_document_to_db for file '{file_name}'.")


async def save_single_document(metadata: Dict[str, Any]) -> bool:
    """
    Saves a single document to the database using the iterator-style session.
    """
    success = False

    # Use the iterator style from the original code
    async for asession in get_async_session():
        try:
            await save_document_to_db(
                file_name=metadata["file_name"],
                processed_pages=metadata["processed_pages"],
                asession=asession,
                metadata=metadata["fields"],
                pdf_url=metadata["pdf_url"],
                title=metadata["survey_name"],
                summary=metadata["summary"],
                document_id=metadata["document_id"],
            )
            logger.info(
                f"File '{metadata['file_name']}' processed and saved successfully."
            )
            success = True
            break  # Success, exit the loop
        except Exception as e:
            logger.error(
                f"Error saving document '{metadata['file_name']}' to database: {e}"
            )
        finally:
            # Explicitly close the session
            await asession.close()

    return success


async def save_all_to_db(metadata_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Saves all documents to the database.
    """
    saved_documents = []

    # Process each document sequentially
    for metadata in metadata_list:
        success = await save_single_document(metadata)
        if success:
            saved_documents.append(metadata)

    return saved_documents
