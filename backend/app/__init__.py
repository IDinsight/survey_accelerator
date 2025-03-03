from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import ingestion, search
from .utils import setup_logger

logger = setup_logger()

tags_metadata = [ingestion.TAG_METADATA]


def create_app() -> FastAPI:
    """
    Create a FastAPI application with the appropriate routers.
    """
    app = FastAPI(
        title="Survey Accelerator",
        openapi_tags=tags_metadata,
        debug=True,
    )

    app.include_router(ingestion.router)
    app.include_router(search.router)

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
    )
    return app
