from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import authenticate_user
from app.database import get_async_session
from app.search.models import log_search
from app.search.pdf_highlight_utils import get_highlighted_pdf
from app.search.schemas import GenericSearchRequest, GenericSearchResponse
from app.search.utils import hybrid_search
from app.users.models import UsersDB
from app.utils import setup_logger

logger = setup_logger()

router = APIRouter(
    prefix="/search",
    tags=["Document Search"],
)


@router.post("/generic", response_model=GenericSearchResponse)
async def search_generic(
    request: GenericSearchRequest,
    session: AsyncSession = Depends(get_async_session),
    user: UsersDB = Depends(authenticate_user),
) -> GenericSearchResponse:
    # Log the request for debugging
    logger.info(f"Generic search request: {request.query}")
    # We'll log highlighted URLs below in the handler
    """
    Search for document chunks based on the provided query.
    Returns chunks with context and explanation.
    """
    try:
        if not request.query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty."
            )

        # Call hybrid_search
        results = await hybrid_search(
            session,
            query_str=request.query,
            country=request.country,
            organization=request.organization,
            region=request.region,
        )

        if not results:
            return GenericSearchResponse(
                query=request.query, results=[], message="No matching documents found."
            )

        # Process results to add highlighted PDFs
        generic_results = []
        for result in results:
            # Process the PDF to add highlights if there's a PDF URL
            if result.metadata.pdf_url:
                try:
                    # Extract page numbers and keywords for each page from the matches
                    # Each match already has starting_keyphrase which contains the words to highlight
                    page_keywords = {}
                    for match in result.matches:
                        if hasattr(match, "page_number") and hasattr(
                            match, "starting_keyphrase"
                        ):
                            page_num = match.page_number
                            keyphrase = match.starting_keyphrase

                            # Skip if keyphrase is empty
                            if not keyphrase:
                                continue

                            # Add this page and keyphrase if not already present
                            if page_num not in page_keywords:
                                page_keywords[page_num] = []

                            # If keyphrase is already a comma-separated list (as per our updated openai_utils)
                            # use it directly, otherwise add it as a single term
                            if "," in keyphrase:
                                keywords = [
                                    kw.strip()
                                    for kw in keyphrase.split(",")
                                    if kw.strip()
                                ]
                                page_keywords[page_num].extend(keywords)
                            else:
                                # Still a phrase, add it as is
                                page_keywords[page_num].append(keyphrase)

                    # Create a highlighted PDF with the page-specific keywords
                    highlighted_pdf_url = await get_highlighted_pdf(
                        result.metadata.pdf_url,
                        request.query,
                        page_keywords=page_keywords,
                    )

                    # Add the highlighted PDF URL to the metadata
                    result.metadata.highlighted_pdf_url = highlighted_pdf_url
                except Exception as e:
                    logger.error(f"Error highlighting PDF: {e}")
                    # If highlighting fails, continue without it

            # Add the result to the list
            generic_results.append(
                {
                    "metadata": result.metadata,
                    "matches": result.matches,
                    "num_matches": result.num_matches,
                }
            )

        response = GenericSearchResponse(
            query=request.query,
            results=generic_results,
            message="Search completed successfully.",
        )

        # Log the search
        await log_search(
            session,
            user=user,
            query=request.query,
            search_response=response.model_dump_json(),
        )

        return response

    except Exception as e:
        logger.error(f"Error during generic search for query '{request.query}': {e}")
        raise e
