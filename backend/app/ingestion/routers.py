"""
Code for the ingestion router.
"""

import asyncio
from typing import Any, Dict, Tuple

from fastapi import APIRouter, Depends
from tqdm.asyncio import tqdm_asyncio

from app.auth.dependencies import authenticate_key
from app.ingestion.schemas import AirtableIngestionResponse
from app.ingestion.utils.airtable_utils import get_airtable_records
from app.ingestion.utils.record_processing import process_record
from app.utils import setup_logger

logger = setup_logger()

router = APIRouter(
    dependencies=[Depends(authenticate_key)],
    prefix="/ingestion",
    tags=["Document Ingestion"],
)

TAG_METADATA = {
    "name": "Document Ingestion",
    "description": "Endpoints for ingesting documents.",
}


@router.post("/airtable", response_model=AirtableIngestionResponse)
async def ingest_airtable() -> AirtableIngestionResponse:
    """
    Ingest documents from Airtable records with page-level progress logging.
    """
    records = get_airtable_records()
    if not records:
        return AirtableIngestionResponse(
            total_records_processed=0,
            total_chunks_created=0,
            message="No records found in Airtable.",
        )

    total_records_processed = 0
    total_chunks_created = 0

    # Create an asynchronous lock for progress bar updates
    progress_lock = asyncio.Lock()

    # Initialize the progress bar without a total
    progress_bar = tqdm_asyncio(desc="Processing pages", unit="page", total=0)

    # Limit the number of concurrent tasks to prevent resource exhaustion
    semaphore = asyncio.Semaphore(10)  # Adjust the number as needed

    async def process_with_semaphore(record: Dict[str, Any]) -> Tuple[int, int]:
        """Semaphore-protected function to process a record."""
        async with semaphore:
            return await process_record(record, progress_bar, progress_lock)

    # Create a list of tasks to process records concurrently
    tasks = [process_with_semaphore(record) for record in records]

    # Run tasks concurrently
    results = await asyncio.gather(*tasks)

    # Sum up the totals from each task
    for records_processed, chunks_created in results:
        total_records_processed += records_processed
        total_chunks_created += chunks_created

    progress_bar.close()

    return AirtableIngestionResponse(
        total_records_processed=total_records_processed,
        total_chunks_created=total_chunks_created,
        message="Ingestion completed.",
    )
