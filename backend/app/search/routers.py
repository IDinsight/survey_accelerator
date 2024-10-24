# app/search/routers.py


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
    request: SearchRequest, session: AsyncSession = Depends(get_async_session)
) -> SearchResponse:
    """Router for searching documents based on a query."""
    try:
        if not request.query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty."
            )

        results = await hybrid_search(session, request.query, request.top_k)

        if not results:
            return SearchResponse(
                query=request.query, results=[], message="No matching documents found."
            )

        return SearchResponse(
            query=request.query,
            results=results,
            message="Search completed successfully.",
        )
    except HTTPException as he:
        raise he  # Optionally, you might remove this block (see below)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
