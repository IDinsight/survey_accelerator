import asyncio
import logging

from fastapi import APIRouter, Depends

from app.auth.dependencies import authenticate_key
from app.ingestion.fetch_utils.airtable_utils import (
    get_airtable_records,
    get_missing_document_ids,
)
from app.ingestion.fetch_utils.google_drive_utils import download_all_files
from app.ingestion.models import save_all_to_db
from app.ingestion.process_utils.embedding_utils import process_files
from app.ingestion.schemas import AirtableIngestionResponse
from app.ingestion.storage_utils.gcp_storage_utils import upload_files_to_gcp

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(authenticate_key)],
    prefix="/ingestion",
    tags=["Document Ingestion"],
)

TAG_METADATA = {
    "name": "Ingestion",
    "description": "Endpoints for ingesting documents from Airtable records",
}
MAX_CONCURRENT_DOWNLOADS = 10
MAX_CONCURRENT_UPLOADS = 10
MAX_CONCURRENT_PROCESSING = 5  # Processing is CPU intensive


@router.post("/airtable/refresh", response_model=AirtableIngestionResponse)
async def airtable_refresh_and_ingest() -> AirtableIngestionResponse:
    """
    Refresh the list of documents by comparing Airtable 'ID' fields with database
    'document_id's. Automatically ingest the missing documents.
    """
    logger.info("Starting Airtable refresh and ingestion process.")
    # Get all Airtable records
    online_records = await get_airtable_records()
    # Compare IDs with SQL DB IDs to get missing IDS
    missing_ids = await get_missing_document_ids(online_records)

    # Map IDs to records
    missing_records = [
        record for record in online_records if record["fields"]["ID"] in missing_ids
    ]

    # Limit to 15 records for development
    missing_records = (
        missing_records[:5] if len(missing_records) > 5 else missing_records
    )

    logger.info(f"Found {len(missing_records)} records to process")

    # Download the files concurrently
    downloaded_files = download_all_files(missing_records, MAX_CONCURRENT_DOWNLOADS)

    if not downloaded_files:
        return AirtableIngestionResponse(
            total_records_processed=0,
            total_chunks_created=0,
            message="No files were downloaded.",
        )

    logger.info(f"Downloaded {len(downloaded_files)} files")

    # Upload files to GCP
    upload_semaphore = asyncio.Semaphore(MAX_CONCURRENT_UPLOADS)
    uploaded_files = await upload_files_to_gcp(downloaded_files, upload_semaphore)

    if not uploaded_files:
        return AirtableIngestionResponse(
            total_records_processed=0,
            total_chunks_created=0,
            message="No files were uploaded to GCP.",
        )

    logger.info(f"Uploaded {len(uploaded_files)} files to GCP")

    # Process files (text extraction and embedding)
    process_semaphore = asyncio.Semaphore(MAX_CONCURRENT_PROCESSING)
    processed_files = await process_files(uploaded_files, process_semaphore)

    if not processed_files:
        return AirtableIngestionResponse(
            total_records_processed=0,
            total_chunks_created=0,
            message="No files were processed successfully.",
        )

    logger.info(f"Processed {len(processed_files)} files")

    # Save processed files to database
    saved_files = await save_all_to_db(processed_files)

    logger.info(f"Saved {len(saved_files)} files to database")

    # Count total pages processed
    total_chunks_created = sum(len(x.get("processed_pages", [])) for x in saved_files)

    # Return information about processed files
    return AirtableIngestionResponse(
        total_records_processed=len(saved_files),
        total_chunks_created=total_chunks_created,
        message=f"Ingestion completed. Processed {len(saved_files)} documents.",
    )
