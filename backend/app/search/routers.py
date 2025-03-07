from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import authenticate_key
from app.database import get_async_session
from app.search.models import log_search
from app.search.pdf_highlight_utils import get_highlighted_pdf
from app.search.schemas import (
    GenericSearchRequest,
    GenericSearchResponse,
)
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

# Debug endpoint to test PDF viewing
@router.get("/debug/pdf-test")
async def test_pdf_viewing():
    """Test endpoint to check PDF viewing capabilities"""
    pdf_urls = []
    # Get a list of PDFs in the highlighted_pdfs folder
    import os
    highlighted_dir = os.environ.get("HIGHLIGHT_DIR", "./highlighted_pdfs")
    if os.path.exists(highlighted_dir):
        for file in os.listdir(highlighted_dir):
            if file.endswith('.pdf'):
                pdf_urls.append(f"/highlighted_pdfs/{file}")
    
    # Return sample PDF links for testing
    return {
        "message": "Test PDF viewing endpoint",
        "highlighted_pdfs": pdf_urls[:5],  # First 5 PDFs
        "test_html": """
        <html>
            <head><title>PDF Test</title></head>
            <body>
                <h1>Test Highlighted PDFs</h1>
                <div id="pdf-container" style="width:100%; height:500px;">
                    <!-- PDF will be loaded here -->
                </div>
                <script>
                    // Get the first PDF URL
                    const pdfUrls = PDFS_PLACEHOLDER;
                    if (pdfUrls.length > 0) {
                        const iframe = document.createElement('iframe');
                        iframe.src = pdfUrls[0];
                        iframe.style.width = '100%';
                        iframe.style.height = '100%';
                        iframe.style.border = 'none';
                        document.getElementById('pdf-container').appendChild(iframe);
                    } else {
                        document.getElementById('pdf-container').innerHTML = 
                            '<p>No highlighted PDFs found</p>';
                    }
                </script>
            </body>
        </html>
        """.replace("PDFS_PLACEHOLDER", str(pdf_urls[:5]))
    }


@router.post("/generic", response_model=GenericSearchResponse)
async def search_generic(
    request: GenericSearchRequest,
    session: AsyncSession = Depends(get_async_session),
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
                        if hasattr(match, 'page_number') and hasattr(match, 'starting_keyphrase'):
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
                                keywords = [kw.strip() for kw in keyphrase.split(",") if kw.strip()]
                                page_keywords[page_num].extend(keywords)
                            else:
                                # Still a phrase, add it as is
                                page_keywords[page_num].append(keyphrase)
                    
                    # Create a highlighted PDF with the page-specific keywords
                    highlighted_pdf_url = await get_highlighted_pdf(
                        result.metadata.pdf_url, 
                        request.query,
                        page_keywords=page_keywords
                    )
                    
                    # Add the highlighted PDF URL to the metadata
                    result.metadata.highlighted_pdf_url = highlighted_pdf_url
                except Exception as e:
                    logger.error(f"Error highlighting PDF: {e}")
                    # If highlighting fails, continue without it
            
            # Add the result to the list
            generic_results.append({
                "metadata": result.metadata,
                "matches": result.matches,
                "num_matches": result.num_matches,
            })

        response = GenericSearchResponse(
            query=request.query,
            results=generic_results,
            message="Search completed successfully.",
        )

        # Log the search
        await log_search(session, request.query, response.model_dump_json())

        return response

    except Exception as e:
        logger.error(f"Error during generic search for query '{request.query}': {e}")
        raise e


