# utils/record_processing.py

import asyncio
import os
from typing import Any, Dict, List, Tuple

import tqdm

from app.database import get_async_session
from app.ingestion.models import save_document_to_db
from app.ingestion.schemas import AirtableIngestionResponse
from app.ingestion.utils.file_processing_utils import (
    open_sheet_in_pandas,
    process_file,
)
from app.ingestion.utils.google_drive_utils import (
    determine_file_type,
    download_file,
    extract_file_id,
    get_drive_service,
)
from app.utils import setup_logger

logger = setup_logger()

XLSX_SUBDIR = "xlsx_files"


async def process_record(
    record: Dict[str, Any],
    progress_bar: tqdm.tqdm,
    progress_lock: asyncio.Lock,
) -> Tuple[int, int]:
    """
    Process a single record from Airtable.

    Args:
        record (Dict[str, Any]): The record to process.
        progress_bar (tqdm.tqdm): The tqdm progress bar instance.
        progress_lock (asyncio.Lock): An asyncio.Lock to synchronize progress
        bar updates.

    Returns:
        Tuple[int, int]: Number of records processed and chunks created.
    """
    fields = record.get("fields", {})
    file_name = fields.get("File name")
    gdrive_link = fields.get("Drive link")
    document_id = fields.get("ID")  # Get the 'ID' field for document_id

    if not file_name or not gdrive_link or document_id is None:
        logger.warning(
            f"""Record {record.get('id')} is missing 'File name',
            'Drive link', or 'ID'. Skipping."""
        )
        return (0, 0)

    # Determine file type
    file_type = determine_file_type(file_name)
    if file_type == "other":
        logger.warning(f"File '{file_name}' has an unsupported extension. Skipping.")
        return (0, 0)

    # Extract file ID from Drive link
    try:
        file_id = extract_file_id(gdrive_link)
    except ValueError as ve:
        logger.error(f"Error processing file '{file_name}': {ve}. Skipping.")
        return (0, 0)

    # Get a Google Drive service instance
    drive_service = get_drive_service()

    # Download the file asynchronously
    try:
        file_buffer = await asyncio.to_thread(
            download_file, file_id, file_name, file_type, drive_service
        )
    except Exception as e:
        logger.error(f"Error downloading file '{file_name}': {e}")
        return (0, 0)

    if not file_buffer and file_type != "xlsx":
        logger.error(f"Failed to download file '{file_name}'. Skipping.")
        return (0, 0)

    # If the file is an Excel file, load it into pandas
    if file_type == "xlsx":
        excel_path = os.path.join(
            XLSX_SUBDIR,
            file_name if file_name.lower().endswith(".xlsx") else f"{file_name}.xlsx",
        )
        df = await asyncio.to_thread(open_sheet_in_pandas, excel_path)
        if df is not None:
            logger.info(f"Excel file '{file_name}' loaded successfully.")
        else:
            logger.warning(f"Failed to load Excel file '{file_name}'.")
        return (0, 0)  # Assuming we don't process Excel files further

    # Process the file asynchronously
    processed_pages = await process_file(
        file_buffer, file_name, file_type, progress_bar, progress_lock
    )

    if not processed_pages:
        logger.warning(f"No processed pages for file '{file_name}'. Skipping.")
        return (0, 0)

    # Save to database with metadata
    async for asession in get_async_session():
        try:
            await save_document_to_db(
                processed_pages=processed_pages,
                file_id=file_id,
                file_name=file_name,
                asession=asession,
                metadata=fields,
            )
            break  # Exit after processing
        except Exception as e:
            logger.error(f"Error saving document '{file_name}' to database: {e}")
            return (0, 0)
        finally:
            await asession.close()

    logger.info(f"File '{file_name}' processed successfully.")

    return (1, len(processed_pages))


async def ingest_records(records: List[Dict[str, Any]]) -> AirtableIngestionResponse:
    """
    Ingest a list of Airtable records.

    Args:
        records (List[Dict[str, Any]]): The list of Airtable records to process.

    Returns:
        AirtableIngestionResponse: The response containing ingestion results.
    """
    total_records_processed = 0
    total_chunks_created = 0

    # Create an asynchronous lock for progress bar updates
    progress_lock = asyncio.Lock()

    # Initialize the progress bar without a total
    progress_bar = tqdm.tqdm(desc="Processing pages", unit="page", total=0)

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
        message=f"Ingestion completed. Processed {total_records_processed} documents.",
    )
