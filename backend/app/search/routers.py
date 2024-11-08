from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import authenticate_key
from app.database import get_async_session
from app.search.schemas import SearchRequest, SearchResponse
from app.search.utils import hybrid_search

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

        return SearchResponse(
            query=request.query,
            results=results,
            message="Search completed successfully.",
        )

    except Exception as e:
        # Log or raise the exception as needed
        raise e
