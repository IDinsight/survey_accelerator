# routers.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.auth.dependencies import authenticate_key
from app.database import get_async_session
from app.ingestion.schemas import AirtableIngestionResponse
from app.ingestion.models import save_document_to_db
from app.ingestion.utils.airtable_utils import get_airtable_records
from app.ingestion.utils.google_drive_utils import (
    get_drive_service,
    extract_file_id,
    determine_file_type,
    download_file,
)
from app.ingestion.utils.file_processing_utils import (
    process_file,
    create_directories,
    open_sheet_in_pandas,
)
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

XLSX_SUBDIR = "xlsx_files"


@router.post("/airtable", response_model=AirtableIngestionResponse)
async def ingest_airtable(asession: AsyncSession = Depends(get_async_session)):
    """
    Ingest documents from Airtable records.
    """
    contents = get_airtable_records()
    if not contents:
        return AirtableIngestionResponse(
            total_records_processed=0,
            total_chunks_created=0,
            message="No records found in Airtable.",
        )

    drive_service = get_drive_service()
    total_records_processed = 0
    total_chunks_created = 0

    create_directories()

    for record in contents:
        fields = record.get("fields", {})
        file_name = fields.get("File name")
        gdrive_link = fields.get("Drive link")

        if not file_name or not gdrive_link:
            logger.warning(
                f"Record {record.get('id')} is missing 'File name' or 'Drive link'. Skipping."
            )
            continue

        # Determine file type
        file_type = determine_file_type(file_name)
        if file_type == "other":
            logger.warning(
                f"File '{file_name}' has an unsupported extension. Skipping."
            )
            continue

        # Extract file ID from Drive link
        try:
            file_id = extract_file_id(gdrive_link)
        except ValueError as ve:
            logger.error(f"Error processing file '{file_name}': {ve}. Skipping.")
            continue

        # Download the file
        file_buffer = download_file(file_id, file_name, file_type, drive_service)

        if not file_buffer and file_type != "xlsx":
            logger.error(f"Failed to download file '{file_name}'. Skipping.")
            continue

        # If the file is an Excel file, optionally load it into pandas
        if file_type == "xlsx":
            excel_path = os.path.join(
                XLSX_SUBDIR,
                (
                    file_name
                    if file_name.lower().endswith(".xlsx")
                    else f"{file_name}.xlsx"
                ),
            )
            df = open_sheet_in_pandas(excel_path)
            if df is not None:
                logger.info(f"Excel file '{file_name}' loaded successfully.")
            else:
                logger.warning(f"Failed to load Excel file '{file_name}'.")
            continue  # Assuming we don't process Excel files further

        # Process the file
        processed_pages = process_file(file_buffer, file_name, file_type)

        if not processed_pages:
            logger.warning(f"No processed pages for file '{file_name}'. Skipping.")
            continue

        # Save to database
        await save_document_to_db(
            processed_pages=processed_pages,
            file_id=file_id,
            file_name=file_name,
            asession=asession,
        )

        total_records_processed += 1
        total_chunks_created += len(processed_pages)
        print(f"File '{file_name}' processed successfully.")
    return AirtableIngestionResponse(
        total_records_processed=total_records_processed,
        total_chunks_created=total_chunks_created,
        message="Ingestion completed.",
    )
