# record_processing.py

import asyncio
import os
from typing import Any, Dict, Tuple

import tqdm

from app.database import get_async_session
from app.ingestion.models import save_document_to_db
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
    progress_bar: tqdm.tqdm,  # Add type annotation
    progress_lock: asyncio.Lock,  # Add type annotation
) -> Tuple[int, int]:
    """
    Process a single record from Airtable.

    Args:
        record (Dict[str, Any]): The record to process.
        progress_bar: The tqdm progress bar instance.
        progress_lock: An asyncio.Lock to synchronize progress bar updates.

    Returns:
        A tuple containing:
        - records_processed (int): Number of records successfully processed (0 or 1).
        - chunks_created (int): Number of chunks created from the file.
    """
    fields = record.get("fields", {})
    file_name = fields.get("File name")
    gdrive_link = fields.get("Drive link")

    if not file_name or not gdrive_link:
        logger.warning(
            f"""Record {record.get('id')} is missing
            'File name' or 'Drive link'. Skipping."""
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
