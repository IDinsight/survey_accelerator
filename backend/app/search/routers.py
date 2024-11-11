from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import authenticate_key
from app.database import get_async_session
from app.search.models import log_search
from app.search.schemas import SearchRequest, SearchResponse
from app.search.utils import hybrid_search
from app.utils import setup_logger

logger = setup_logger()

router = APIRouter(
    prefix="/search",
    tags=["Document Search"],
    dependencies=[Depends(authenticate_key)],
)

TAG_METADATA = {
    "name": "Search",
    "description": "Endpoints for querying the document base via different means",
}


@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    session: AsyncSession = Depends(get_async_session),
) -> SearchResponse:
    """Search for documents based on the provided query."""
    try:
        if not request.query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty."
            )

        # Perform search without passing `top_k`, as it’s managed internally
        results = await hybrid_search(
            session,
            query_str=request.query,
            precision=request.precision,
            country=request.country,
            organization=request.organization,
            region=request.region,
        )

        if not results:
            return SearchResponse(
                query=request.query, results=[], message="No matching documents found."
            )

        return_result = SearchResponse(
            query=request.query,
            results=results,
            message="Search completed successfully.",
        )

        # Log the search with the precision value
        await log_search(
            session, request.query, return_result.model_dump_json(), request.precision
        )

        return return_result

    except Exception as e:
        logger.error(f"Error during search for query '{request.query}': {e}")
        raise e
