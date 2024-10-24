from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import asyncio as aioredis

from . import ingestion, search
from .config import REDIS_HOST
from .utils import setup_logger

logger = setup_logger()

tags_metadata = [ingestion.TAG_METADATA]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifespan events for the FastAPI application.
    """

    logger.info("Application started")
    app.state.redis = await aioredis.from_url(REDIS_HOST)

    yield

    await app.state.redis.close()
    logger.info("Application finished")


def create_app() -> FastAPI:
    """
    Create a FastAPI application with the appropriate routers.
    """
    app = FastAPI(
        title="Survey Accelerator",
        openapi_tags=tags_metadata,
        lifespan=lifespan,
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
