"""MCP server exposing the Survey Accelerator library to Claude.

Mounted into the existing FastAPI app at /mcp (see app/__init__.py), so it
shares the backend's database engine, search pipeline and deployment.

The tool surface is deliberately two-layered:

  * `search_surveys` finds relevant pages across the library and explains why
    each one matched.
  * `get_document_info` / `get_document_pages` / `get_document_text` let Claude
    follow up on a hit and read the actual survey text, so it can quote real
    question wording rather than paraphrasing a summary.

Sessions are stateless (`stateless_http=True`) because the backend runs under
gunicorn with several workers and requests are not pinned to one of them.
"""

import contextlib
from typing import Any, AsyncIterator, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import (
    MCP_DEFAULT_MAX_RESULTS,
    MCP_MAX_RESULTS_LIMIT,
    MCP_MAX_TEXT_CHARS,
)
from app.database import get_sqlalchemy_async_engine
from app.ingestion.models import DocumentDB
from app.search.pdf_highlight_utils import get_highlighted_pdf
from app.search.utils import hybrid_search
from app.utils import setup_logger

from .documents import (
    count_library,
    count_pages,
    distinct_json_values,
    distinct_scalar_values,
    document_payload,
    extract_raw_text,
    get_document_row,
    get_pages,
    list_library,
    page_link,
)

logger = setup_logger()

INSTRUCTIONS = """\
Survey Accelerator indexes high-quality survey instruments and research \
documents from IDinsight, DHS, MICS/UNICEF, USAID, the World Bank and others.

Typical flow:
  1. `search_surveys` with a topic (for example "child nutrition anthropometry" \
or "household water access"). It returns matching documents with the specific \
pages that matched and why.
  2. `get_document_pages` on a promising hit to read the actual question \
wording on those pages. Do this before quoting or adapting questions -- the \
search result explanations are summaries, not the source text.
  3. `get_document_text` to read a document more broadly, or `list_documents` \
to browse the library by organization, country or year.

Use `list_filter_values` to discover valid filter values before filtering; \
guessing organization names tends to return nothing."""

mcp = FastMCP(
    "survey-accelerator",
    instructions=INSTRUCTIONS,
    stateless_http=True,
    json_response=True,
)


@contextlib.asynccontextmanager
async def db_session() -> AsyncIterator[AsyncSession]:
    """
    Open a database session for one tool call.

    Tools run outside the request/response cycle, so they cannot use the
    `get_async_session` FastAPI dependency; they share the same engine instead.
    """
    async with AsyncSession(
        get_sqlalchemy_async_engine(), expire_on_commit=False
    ) as session:
        yield session


def _clamp(value: int, low: int, high: int) -> int:
    """Clamp an integer into an inclusive range."""
    return max(low, min(value, high))


@mcp.tool()
async def search_surveys(
    query: str,
    organizations: Optional[List[str]] = None,
    survey_types: Optional[List[str]] = None,
    max_results: int = MCP_DEFAULT_MAX_RESULTS,
    include_highlighted_pdfs: bool = False,
) -> Dict[str, Any]:
    """Search the survey library for pages relevant to a topic.

    Runs a hybrid semantic + keyword search across every indexed page, reranks
    with an LLM, and returns the best matching documents grouped by document,
    each with the pages that matched and a short explanation of why.

    This is the entry point for questions like "find me good surveys measuring
    household food security". Results are page-level pointers: to read the
    actual question wording, follow up with `get_document_pages` using the
    `document_id` and `page_number` values returned here.

    Args:
        query: What to search for. Natural language works better than keywords.
        organizations: Restrict to these publishing organizations. Get valid
            values from `list_filter_values`.
        survey_types: Restrict to these survey types, for example "DHS Surveys".
            Get valid values from `list_filter_values`.
        max_results: How many matching pages to rank and explain. Higher values
            are slower; each result costs two LLM calls.
        include_highlighted_pdfs: Also generate a PDF with the matching terms
            highlighted and return its URL. Roughly doubles the time taken, so
            only set this when the user wants a marked-up PDF to open.

    Returns:
        The query, a result count, and a list of documents. Each document
        carries its metadata plus a `matches` list of pages with the
        explanation, a direct `page_link`, and the ranking scores.
    """
    if not query or not query.strip():
        return {"error": "Query cannot be empty.", "query": query, "results": []}

    max_results = _clamp(max_results, 1, MCP_MAX_RESULTS_LIMIT)

    async with db_session() as session:
        results = await hybrid_search(
            session,
            query_str=query,
            organizations=organizations or [],
            survey_types=survey_types or [],
            max_results=max_results,
        )

        if not results:
            return {
                "query": query,
                "count": 0,
                "results": [],
                "message": (
                    "No matching documents found. Try a broader query, or drop "
                    "the organization/survey type filters."
                ),
            }

        documents = []
        for result in results:
            meta = result.metadata

            if include_highlighted_pdfs and meta.pdf_url:
                highlighted = await _highlight(result, query)
                if highlighted:
                    meta.highlighted_pdf_url = highlighted

            documents.append(
                {
                    "document_id": meta.document_id,
                    "title": meta.title,
                    "summary": meta.summary,
                    "organizations": meta.organizations or [],
                    "countries": meta.countries or [],
                    "regions": meta.regions or [],
                    "year": meta.year,
                    "survey_type": meta.survey_type,
                    "pdf_url": meta.pdf_url,
                    "highlighted_pdf_url": meta.highlighted_pdf_url,
                    "num_matches": result.num_matches,
                    "matches": [
                        {
                            "page_number": match.page_number,
                            "rank": match.rank,
                            "explanation": match.explanation,
                            "match_type": match.match_type,
                            "contextual_score": match.contextual_score,
                            "direct_match_score": match.direct_match_score,
                            "page_link": page_link(meta.pdf_url, match.page_number),
                        }
                        for match in result.matches
                    ],
                }
            )

        return {
            "query": query,
            "count": len(documents),
            "results": documents,
            "next_step": (
                "Call get_document_pages(document_id, pages=[...]) on the most "
                "promising documents to read the real text of the matching pages."
            ),
        }


async def _highlight(result: Any, query: str) -> Optional[str]:
    """
    Build a highlighted copy of the PDF for one search result.

    Mirrors the web app: each match contributes its keyphrase (which may be a
    comma-separated list) to the pages it was found on.
    """
    page_keywords: Dict[int, List[str]] = {}
    for match in result.matches:
        keyphrase = getattr(match, "starting_keyphrase", "")
        if not keyphrase:
            continue
        page = page_keywords.setdefault(match.page_number, [])
        if "," in keyphrase:
            page.extend(kw.strip() for kw in keyphrase.split(",") if kw.strip())
        else:
            page.append(keyphrase)

    try:
        return await get_highlighted_pdf(
            result.metadata.pdf_url, query, page_keywords=page_keywords
        )
    except Exception as e:
        logger.error(f"MCP: highlighting failed for '{result.metadata.title}': {e}")
        return None


@mcp.tool()
async def get_document_info(document_id: int) -> Dict[str, Any]:
    """Get metadata and page count for one document.

    Use this to orient yourself before reading a document: it tells you how
    many pages are indexed, what the document covers, and where the PDF lives.

    Args:
        document_id: The `document_id` from a `search_surveys` or
            `list_documents` result.

    Returns:
        Document metadata including `total_pages`, or an error if no document
        with that id is indexed.
    """
    async with db_session() as session:
        doc = await get_document_row(session, document_id)
        if doc is None:
            return {"error": f"No document found with document_id {document_id}."}
        pages = await count_pages(session, document_id)
        return document_payload(doc, page_count=pages)


@mcp.tool()
async def get_document_pages(
    document_id: int,
    pages: List[int],
    include_context: bool = False,
) -> Dict[str, Any]:
    """Read the full text of specific pages of a document.

    This is the follow-up to `search_surveys`: it returns what is actually
    written on those pages, so you can quote real question wording, response
    options and module structure instead of working from summaries.

    Args:
        document_id: The `document_id` from a search or listing result.
        pages: Page numbers to read, from the `page_number` fields of a search
            result. Requesting a page that is not indexed simply omits it.
        include_context: Also return the indexing context and summary written
            alongside each page. Off by default, since the verbatim text is
            usually what you want.

    Returns:
        Document metadata plus a `pages` list, each with `page_number`, `text`
        and a `page_link` that opens the PDF at that page.
    """
    if not pages:
        return {"error": "Provide at least one page number."}

    async with db_session() as session:
        doc = await get_document_row(session, document_id)
        if doc is None:
            return {"error": f"No document found with document_id {document_id}."}

        rows = await get_pages(session, document_id, page_numbers=pages)
        found = {row.page_number for row in rows}
        missing = [p for p in pages if p not in found]

        payload = document_payload(
            doc, page_count=await count_pages(session, document_id)
        )
        payload["pages"] = [_page_payload(row, doc, include_context) for row in rows]
        if missing:
            payload["pages_not_indexed"] = missing
        return payload


def _page_payload(
    row: DocumentDB, doc: DocumentDB, include_context: bool
) -> Dict[str, Any]:
    """Shape one page row for a tool response."""
    payload: Dict[str, Any] = {
        "page_number": row.page_number,
        "text": extract_raw_text(row.contextualized_chunk),
        "page_link": page_link(doc.pdf_url, row.page_number),
    }
    if include_context:
        payload["chunk_summary"] = row.chunk_summary
        payload["indexed_context"] = row.contextualized_chunk
    return payload


@mcp.tool()
async def get_document_text(
    document_id: int,
    start_page: int = 1,
    end_page: Optional[int] = None,
    max_chars: int = MCP_MAX_TEXT_CHARS,
) -> Dict[str, Any]:
    """Read a document straight through, in page order.

    Use this when you need the whole instrument rather than a few pages, for
    example to summarise a survey's structure or extract every question in a
    module. Long documents are truncated at a character budget and report
    `next_start_page`; call again from there to continue.

    Args:
        document_id: The `document_id` from a search or listing result.
        start_page: First page to read.
        end_page: Last page to read. Defaults to the end of the document.
        max_chars: Character budget for this call. Reading stops at the last
            page that fits.

    Returns:
        Document metadata, the pages read, and `next_start_page` when there is
        more to read (null when the document is complete).
    """
    max_chars = _clamp(max_chars, 1000, MCP_MAX_TEXT_CHARS)

    async with db_session() as session:
        doc = await get_document_row(session, document_id)
        if doc is None:
            return {"error": f"No document found with document_id {document_id}."}

        rows = await get_pages(
            session, document_id, start_page=start_page, end_page=end_page
        )

        collected: List[Dict[str, Any]] = []
        budget = max_chars
        next_start_page = None
        for row in rows:
            text = extract_raw_text(row.contextualized_chunk)
            # Always emit the first page, even if it alone blows the budget --
            # otherwise a single long page would make the tool return nothing.
            if collected and len(text) > budget:
                next_start_page = row.page_number
                break
            collected.append(
                {
                    "page_number": row.page_number,
                    "text": text,
                    "page_link": page_link(doc.pdf_url, row.page_number),
                }
            )
            budget -= len(text)

        payload = document_payload(
            doc, page_count=await count_pages(session, document_id)
        )
        payload["pages"] = collected
        payload["pages_returned"] = len(collected)
        payload["next_start_page"] = next_start_page
        if next_start_page is not None:
            payload["note"] = (
                f"Truncated at the character budget. Call get_document_text with "
                f"start_page={next_start_page} to continue."
            )
        return payload


@mcp.tool()
async def list_documents(
    organizations: Optional[List[str]] = None,
    survey_types: Optional[List[str]] = None,
    countries: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """Browse the survey library by metadata, without searching content.

    Use this to answer questions about coverage ("what DHS surveys do you have
    for Kenya?") or to enumerate a set of documents before reading them. For
    topic-based questions use `search_surveys` instead, which looks inside the
    documents.

    Args:
        organizations: Filter to these publishing organizations.
        survey_types: Filter to these survey types.
        countries: Filter to these countries.
        regions: Filter to these regions.
        year_from: Only documents from this year onwards.
        year_to: Only documents up to this year.
        limit: Maximum documents to return (capped at 200).
        offset: Skip this many documents, for paging through results.

    Returns:
        `total` matching documents, the slice requested, and the documents
        themselves ordered by year descending.
    """
    limit = _clamp(limit, 1, 200)
    offset = max(0, offset)

    async with db_session() as session:
        total = await count_library(
            session,
            organizations=organizations,
            survey_types=survey_types,
            countries=countries,
            regions=regions,
            year_from=year_from,
            year_to=year_to,
        )
        docs = await list_library(
            session,
            organizations=organizations,
            survey_types=survey_types,
            countries=countries,
            regions=regions,
            year_from=year_from,
            year_to=year_to,
            limit=limit,
            offset=offset,
        )
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "count": len(docs),
            "documents": [document_payload(doc) for doc in docs],
        }


@mcp.tool()
async def list_filter_values() -> Dict[str, Any]:
    """List the values available for filtering searches and listings.

    Call this before using the `organizations`, `survey_types`, `countries` or
    `regions` filters. The stored values are exact strings, so a guessed name
    will usually match nothing.

    Returns:
        Sorted distinct values for each filterable field, plus the year range
        covered by the library.
    """
    async with db_session() as session:
        return {
            "organizations": await distinct_json_values(
                session, DocumentDB.organizations
            ),
            "countries": await distinct_json_values(session, DocumentDB.countries),
            "regions": await distinct_json_values(session, DocumentDB.regions),
            "survey_types": await distinct_scalar_values(
                session, DocumentDB.survey_type
            ),
            "years": await distinct_scalar_values(session, DocumentDB.year),
        }
