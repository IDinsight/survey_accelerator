import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import auth, contributions, ingestion, pdfs, search, users
from .utils import setup_logger

logger = setup_logger()


def create_app() -> FastAPI:
    """
    Create a FastAPI application with the appropriate routers.
    """
    app = FastAPI(
        title="Survey Accelerator",
        debug=True,
    )
    logger.info("Creating FastAPI application")
    app.include_router(ingestion.router)
    app.include_router(search.router)
    app.include_router(users.router)
    app.include_router(auth.router)
    app.include_router(pdfs.router)
    app.include_router(contributions.router)

    origins = [
        "http://localhost",
        "http://localhost:3000",
        "https://localhost",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition", "Content-Type"],
    )

    # Add headers middleware to enable PDF embedding in iframes and objects
    @app.middleware("http")
    async def add_pdf_headers(request, call_next):
        response = await call_next(request)

        # For PDF files, add headers to allow embedding in iframes and objects
        if (
            request.url.path.endswith(".pdf")
            or "/highlighted_pdfs/" in request.url.path
        ):
            # Allow cross-origin resource sharing
            response.headers["Access-Control-Allow-Origin"] = "*"
            # Allow embedding in iframes from any origin
            response.headers["X-Frame-Options"] = "ALLOWALL"
            # Allow embedding in frames, iframes, objects, etc.
            response.headers["Content-Security-Policy"] = (
                "frame-ancestors *; object-src *"
            )
            # Cache control for PDFs - cache for 1 hour
            response.headers["Cache-Control"] = "public, max-age=3600"
            # Ensure PDF is recognized as PDF
            if request.url.path.endswith(".pdf"):
                response.headers["Content-Type"] = "application/pdf"
            # Disable content disposition header if present (prevents download)
            if "Content-Disposition" in response.headers:
                del response.headers["Content-Disposition"]

        return response

    return app
