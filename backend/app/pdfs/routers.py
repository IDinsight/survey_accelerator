import os

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from ..utils import setup_logger

logger = setup_logger()

router = APIRouter(tags=["PDFs"])
TAG_METADATA = {
    "name": "PDFs",
    "description": "Distribute PDFs.",
}

HIGHLIGHT_DIR = os.getenv("HIGHLIGHT_DIR", "./highlighted_pdfs")
LOCAL_UPLOAD_DIR = os.getenv("LOCAL_UPLOAD_DIR", "./uploaded_files")

def create_pdf_response(file_path: str) -> FileResponse:
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    
    response = FileResponse(file_path, media_type="application/pdf")
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = "frame-ancestors *; object-src *"
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response

@router.get("/pdf/{filename}")
async def serve_pdf(
    filename: str,
    type: str = Query("regular", enum=["regular", "highlighted"]),
):
    """
    Serve PDFs based on the type.
    Use the 'type' query parameter to choose:
      - type=regular: serves PDFs from uploaded_files
      - type=highlighted: serves PDFs from highlighted_pdfs
    """
    if type == "regular":
        file_path = os.path.join(LOCAL_UPLOAD_DIR, filename)
    elif type == "highlighted":
        file_path = os.path.join(HIGHLIGHT_DIR, filename)
    else:
        raise HTTPException(status_code=400, detail="Invalid type specified")
    
    return create_pdf_response(file_path)
