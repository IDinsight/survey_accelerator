import asyncio
import io
import os
from typing import Any, Dict, List

from app.database import get_async_session
from app.ingestion.fetch_utils.google_drive_utils import (
    determine_file_type,
    download_file,
    extract_file_id,
    get_drive_service,
)
from app.ingestion.models import save_document_to_db
from app.ingestion.schemas import AirtableIngestionResponse
from app.ingestion.storage_utils.gcp_storage_utils import (
    upload_file_buffer_to_gcp_bucket,
)
from app.ingestion.utils.file_processing_utils import process_file
from app.utils import setup_logger

logger = setup_logger()

MAX_CONCURRENT_TASKS = 5  # Adjust as needed


async def extract_metadata(record: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Extracts and validates metadata from a record.
    """
    fields = record.get("fields", {})
    file_name = fields.get("File name")
    survey_name = fields.get("Survey name")
    gdrive_link = fields.get("Drive link")
    document_id = fields.get("ID")

    if not file_name or not gdrive_link or document_id is None:
        logger.warning(
            f"""Record {record.get('id')} is missing 'File name', 'Drive link', or 'ID'.
            Skipping."""
        )
        return None

    # Determine file type
    file_type = await determine_file_type(file_name)
    if file_type == "other":
        logger.warning(f"File '{file_name}' has an unsupported extension. Skipping.")
        return None

    # Extract file ID from Drive link
    try:
        file_id = await extract_file_id(gdrive_link)
    except ValueError as ve:
        logger.error(f"Error processing file '{file_name}': {ve}. Skipping.")
        return None

    # Collect metadata
    metadata = {
        "record_id": record.get("id"),
        "fields": fields,
        "file_name": file_name,
        "file_type": file_type,
        "file_id": file_id,
        "document_id": document_id,
        "survey_name": survey_name,
    }
    return metadata


async def download_files(
    metadata_list: List[Dict[str, Any]],
    semaphore: asyncio.Semaphore,
    drive_service,
) -> List[Dict[str, Any]]:
    """
    Downloads files concurrently and updates metadata with file buffers.
    """

    async def download(metadata):
        """
        Downloads a single file and updates metadata with file buffer.
        """
        async with semaphore:
            file_name = metadata["file_name"]
            file_id = metadata["file_id"]

            try:
                file_buffer = await asyncio.to_thread(
                    download_file, file_id, drive_service
                )

                metadata["file_buffer"] = file_buffer
                return metadata

            except Exception as e:
                logger.error(f"Error downloading file '{file_name}': {e}")
                return None

    tasks = [download(metadata) for metadata in metadata_list if metadata]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res]


async def process_files(
    metadata_list: List[Dict[str, Any]],
    semaphore: asyncio.Semaphore,
) -> List[Dict[str, Any]]:
    """
    Processes files concurrently and updates metadata with processed pages.
    """

    async def process(metadata):
        """
        Processes a single file and updates metadata with processed pages.
        """
        async with semaphore:
            file_name = metadata["file_name"]
            file_type = metadata["file_type"]
            fields = metadata["fields"]
            file_buffer = metadata["file_buffer"]

            # Read the file content into bytes
            file_buffer.seek(0)
            file_bytes = file_buffer.read()

            # Create a new BytesIO object for processing
            processing_file_buffer = io.BytesIO(file_bytes)

            # Process the file asynchronously
            processed_pages = await process_file(
                processing_file_buffer,
                file_name,
                file_type,
                metadata=fields,
            )

            if not processed_pages:
                logger.warning(f"No processed pages for file '{file_name}'. Skipping.")
                return None

            metadata["processed_pages"] = processed_pages
            metadata["file_bytes"] = file_bytes
            return metadata

    tasks = [process(metadata) for metadata in metadata_list]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res]


async def upload_files_to_gcp(
    metadata_list: List[Dict[str, Any]],
    semaphore: asyncio.Semaphore,
) -> List[Dict[str, Any]]:
    """
    Uploads files to GCP concurrently and updates metadata with PDF URLs.
    """

    async def upload(metadata):
        async with semaphore:
            file_name = metadata["file_name"]
            file_bytes = metadata["file_bytes"]
            uploading_file_buffer = io.BytesIO(file_bytes)

            # Upload the file to GCP bucket
            bucket_name = os.getenv("GCP_BUCKET_NAME", "survey_accelerator_files")

            pdf_url = await asyncio.to_thread(
                upload_file_buffer_to_gcp_bucket,
                uploading_file_buffer,
                bucket_name,
                file_name,
            )

            if not pdf_url:
                logger.error(f"Failed to upload document '{file_name}' to GCP bucket")
                return None

            metadata["pdf_url"] = pdf_url
            return metadata

    tasks = [upload(metadata) for metadata in metadata_list]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res]


async def save_single_document(metadata: Dict[str, Any], asession):
    """
    Saves a single document to the database and prints a success message.
    """
    await save_document_to_db(
        file_name=metadata["file_name"],
        processed_pages=metadata["processed_pages"],
        file_id=metadata["file_id"],
        asession=asession,
        metadata=metadata["fields"],
        pdf_url=metadata["pdf_url"],
        summary=metadata.get("brief_summary"),
        title=metadata.get("generated_title"),
    )
    print(f"File '{metadata['file_name']}' processed and saved successfully.")


async def save_all_to_db(metadata_list: List[Dict[str, Any]]):
    """
    Saves all documents to the database concurrently.
    """
    try:
        async with get_async_session() as asession:
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

            async def save_with_semaphore(metadata, session):
                async with semaphore:
                    await save_single_document(metadata, session)

            save_tasks = [
                save_with_semaphore(metadata, asession) for metadata in metadata_list
            ]
            await asyncio.gather(*save_tasks)
    except Exception as e:
        logger.error(f"Error saving documents to database: {e}")


async def ingest_records(records: List[Dict[str, Any]]) -> AirtableIngestionResponse:
    """
    Ingests a list of Airtable records in parallel stages.
    """
    total_records_processed = 0
    total_chunks_created = 0
    # Step 1: Extract metadata
    metadata_list = [await extract_metadata(record) for record in records]
    metadata_list = [m for m in metadata_list if m]

    if not metadata_list:
        return AirtableIngestionResponse(
            total_records_processed=0,
            total_chunks_created=0,
            message="No valid records to process.",
        )

    # Step 2: Download files
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
    drive_service = get_drive_service()  # Get Google Drive service once

    files = await download_files(metadata_list, semaphore, drive_service)
    if not metadata_list:
        return AirtableIngestionResponse(
            total_records_processed=0,
            total_chunks_created=0,
            message="Failed to download any files.",
        )

    # Step 3: Process files
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

    updated_metadata_list = await process_files(files, semaphore)
    if not metadata_list:
        return AirtableIngestionResponse(
            total_records_processed=0,
            total_chunks_created=0,
            message="No files were processed.",
        )

    # Step 4: Upload files to GCP
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

    metadata_list = await upload_files_to_gcp(updated_metadata_list, semaphore)

    # Step 5: Save all to database
    await save_all_to_db(metadata_list)

    # Update totals
    total_records_processed = len(metadata_list)
    total_chunks_created = sum(
        len(metadata["processed_pages"]) for metadata in metadata_list
    )

    return AirtableIngestionResponse(
        total_records_processed=total_records_processed,
        total_chunks_created=total_chunks_created,
        message=f"Ingestion completed. Processed {total_records_processed} documents.",
    )
