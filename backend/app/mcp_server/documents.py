"""Document lookups backing the MCP follow-up tools.

The `documents` table stores one row per page, keyed logically by
`document_id` + `page_number`. Everything here works in those terms so a tool
can go from a search hit straight to the underlying survey text.
"""

from typing import Any, Dict, List, Optional, Sequence, Set

from sqlalchemy import ARRAY, Text, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased as orm_aliased

from app.ingestion.models import DocumentDB
from app.utils import setup_logger

logger = setup_logger()


def extract_raw_text(chunk: Optional[str]) -> str:
    """
    Pull the verbatim page text out of a contextualized chunk.

    Chunks are stored as "METADATA: ... CONTEXT: ... RAW TEXT: ...", where only
    the RAW TEXT section is the actual document. Chunks written before that
    format are returned unchanged.
    """
    if not chunk:
        return ""
    if "RAW TEXT:" in chunk:
        return chunk.split("RAW TEXT:", 1)[1].strip()
    return chunk.strip()


def page_link(pdf_url: Optional[str], page_number: int) -> Optional[str]:
    """Build a link that opens the PDF at a specific page."""
    if not pdf_url:
        return None
    return f"{pdf_url}#page={page_number}"


def apply_filters(
    stmt: Any,
    *,
    organizations: Optional[Sequence[str]] = None,
    survey_types: Optional[Sequence[str]] = None,
    countries: Optional[Sequence[str]] = None,
    regions: Optional[Sequence[str]] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> Any:
    """
    Apply the standard library filters to a select statement.

    countries/organizations/regions are JSONB arrays, so they use the `?|`
    "has any of these keys" operator. survey_type is a plain string column.
    """
    if organizations:
        stmt = stmt.where(
            DocumentDB.organizations.op("?|")(cast(list(organizations), ARRAY(Text)))
        )
    if countries:
        stmt = stmt.where(
            DocumentDB.countries.op("?|")(cast(list(countries), ARRAY(Text)))
        )
    if regions:
        stmt = stmt.where(DocumentDB.regions.op("?|")(cast(list(regions), ARRAY(Text))))
    if survey_types:
        stmt = stmt.where(DocumentDB.survey_type.in_(list(survey_types)))
    if year_from is not None:
        stmt = stmt.where(DocumentDB.year >= year_from)
    if year_to is not None:
        stmt = stmt.where(DocumentDB.year <= year_to)
    return stmt


def document_payload(
    doc: DocumentDB, page_count: Optional[int] = None
) -> Dict[str, Any]:
    """Shape a document row into the metadata block every tool returns."""
    payload: Dict[str, Any] = {
        "document_id": doc.document_id,
        "title": doc.title,
        "file_name": doc.file_name,
        "summary": doc.summary,
        "organizations": doc.organizations or [],
        "countries": doc.countries or [],
        "regions": doc.regions or [],
        "year": doc.year,
        "survey_type": doc.survey_type,
        "pdf_url": doc.pdf_url,
    }
    if page_count is not None:
        payload["total_pages"] = page_count
    return payload


async def get_document_row(
    session: AsyncSession, document_id: int
) -> Optional[DocumentDB]:
    """Return any one page row for a document, for its shared metadata."""
    result = await session.execute(
        select(DocumentDB)
        .where(DocumentDB.document_id == document_id)
        .order_by(DocumentDB.page_number)
        .limit(1)
    )
    return result.scalars().first()


async def count_pages(session: AsyncSession, document_id: int) -> int:
    """Count the indexed pages for a document."""
    result = await session.execute(
        select(func.count())
        .select_from(DocumentDB)
        .where(DocumentDB.document_id == document_id)
    )
    return int(result.scalar() or 0)


async def get_pages(
    session: AsyncSession,
    document_id: int,
    page_numbers: Optional[Sequence[int]] = None,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
) -> List[DocumentDB]:
    """
    Fetch page rows for a document, either by explicit page numbers or by range.

    Both selectors are optional; with neither, every page is returned in order.
    """
    stmt = select(DocumentDB).where(DocumentDB.document_id == document_id)
    if page_numbers:
        stmt = stmt.where(DocumentDB.page_number.in_(list(page_numbers)))
    if start_page is not None:
        stmt = stmt.where(DocumentDB.page_number >= start_page)
    if end_page is not None:
        stmt = stmt.where(DocumentDB.page_number <= end_page)
    stmt = stmt.order_by(DocumentDB.page_number)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_library(
    session: AsyncSession,
    *,
    organizations: Optional[Sequence[str]] = None,
    survey_types: Optional[Sequence[str]] = None,
    countries: Optional[Sequence[str]] = None,
    regions: Optional[Sequence[str]] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[DocumentDB]:
    """
    List distinct documents matching the filters.

    DISTINCT ON collapses the per-page rows down to one row per document; the
    inner ordering picks the lowest page number so the metadata is stable.
    """
    inner = select(DocumentDB).distinct(DocumentDB.document_id)
    inner = apply_filters(
        inner,
        organizations=organizations,
        survey_types=survey_types,
        countries=countries,
        regions=regions,
        year_from=year_from,
        year_to=year_to,
    )
    # Postgres requires DISTINCT ON expressions to lead the ORDER BY, so the
    # display ordering has to happen in an outer query.
    subq = inner.order_by(DocumentDB.document_id, DocumentDB.page_number).subquery()
    doc = orm_aliased(DocumentDB, subq)

    stmt = (
        select(doc)
        .order_by(subq.c.year.desc().nullslast(), subq.c.title)
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_library(
    session: AsyncSession,
    *,
    organizations: Optional[Sequence[str]] = None,
    survey_types: Optional[Sequence[str]] = None,
    countries: Optional[Sequence[str]] = None,
    regions: Optional[Sequence[str]] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> int:
    """Count distinct documents matching the filters."""
    stmt = select(func.count(func.distinct(DocumentDB.document_id)))
    stmt = apply_filters(
        stmt,
        organizations=organizations,
        survey_types=survey_types,
        countries=countries,
        regions=regions,
        year_from=year_from,
        year_to=year_to,
    )
    result = await session.execute(stmt)
    return int(result.scalar() or 0)


async def distinct_json_values(session: AsyncSession, column: Any) -> List[str]:
    """
    Flatten a JSONB array column into its sorted distinct values.

    DISTINCT collapses the per-page rows down to the handful of distinct arrays
    in the table, and the flattening happens in Python -- unnesting in SQL needs
    a lateral join for the sake of a list that is only ever tens of items long.
    """
    result = await session.execute(select(column).distinct())
    values: Set[str] = set()
    for row in result.scalars().all():
        if isinstance(row, list):
            values.update(str(v) for v in row if v)
        elif row:
            values.add(str(row))
    return sorted(values)


async def distinct_scalar_values(session: AsyncSession, column: Any) -> List[str]:
    """Return the sorted distinct values of a plain column."""
    stmt = select(column).distinct().where(column.isnot(None)).order_by(column)
    result = await session.execute(stmt)
    return [v for v in result.scalars().all() if v]
