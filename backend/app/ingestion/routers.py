import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.ingestion.fetch_utils.airtable_utils import (
    get_airtable_records,
    get_missing_document_ids,
)
from app.ingestion.fetch_utils.google_drive_utils import download_all_files
from app.ingestion.models import DocumentDB, save_all_to_db
from app.ingestion.process_utils.embedding_utils import process_files
from app.ingestion.schemas import AirtableIngestionResponse, DocumentPreview
from app.ingestion.storage_utils.gcp_storage_utils import upload_files_to_local

from ..database import get_async_session
from .schemas import OrganizationDocuments

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ingestion",
    tags=["Document Ingestion"],
)


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
        missing_records[:15] if len(missing_records) > 5 else missing_records
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

    # Upload files to local
    upload_semaphore = asyncio.Semaphore(MAX_CONCURRENT_UPLOADS)
    uploaded_files = await upload_files_to_local(downloaded_files, upload_semaphore)

    if not uploaded_files:
        return AirtableIngestionResponse(
            total_records_processed=0,
            total_chunks_created=0,
            message="No files were uploaded to folder.",
        )

    logger.info(f"Uploaded {len(uploaded_files)} files to folder")

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


@router.get("/view-ingested-documents", response_model=list[OrganizationDocuments])
async def view_documents_grouped(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Retrieves all ingested documents grouped by their organization in alphabetical order.
    For each document it returns:

    - **Preview Link:** A link to preview the document (preferring pdf_url if available, then drive_link)
    - **Year:** The year the document was made
    - **Description:** The summary/description of the document
    - **Countries:** The countries related to the document
    - **Regions:** The regions related to the document

    Documents within each organization are sorted in alphabetical order (by title or file name).
    """
    organizations = await get_documents_grouped_by_organization(session)
    if not organizations:
        raise HTTPException(status_code=404, detail="No documents found.")

    # Sort documents within each organization by title or file name
    for org in organizations:
        org.documents.sort(key=lambda doc: (doc.title or doc.file_name).lower())
    # Additionally, sort the organization groups alphabetically by organization name
    organizations.sort(key=lambda org: org.organization.lower())
    return organizations


async def get_documents_grouped_by_organization(
    session: AsyncSession,
) -> list[OrganizationDocuments]:
    """
    Retrieves distinct document preview rows (one per document_id) from the database,
    then groups them by their organization (always taking the first element of the organizations list).

    This approach avoids duplicate rows from the chunked table.
    """
    # Use DISTINCT ON approach: here we order by document_id and created_datetime_utc (descending)
    # so that we pick the most recent row per document.
    query = (
        select(
            DocumentDB.document_id,
            DocumentDB.file_name,
            DocumentDB.pdf_url,
            DocumentDB.summary,
            DocumentDB.year,
            DocumentDB.countries,
            DocumentDB.regions,
            DocumentDB.title,
            DocumentDB.organizations,
        )
        .distinct(DocumentDB.document_id)
        .order_by(DocumentDB.document_id, DocumentDB.created_datetime_utc.desc())
    )
    result = await session.execute(query)
    rows = result.all()

    org_docs_map: dict[str, OrganizationDocuments] = {}

    for row in rows:
        # Each row is a Row object; access its columns via _mapping.
        data = row._mapping

        organizations = data.get("organizations")
        # Always take the first organization value; default to "Unknown" if missing or empty.
        org_name = (
            organizations[0]
            if isinstance(organizations, list) and organizations
            else "Unknown"
        )

        if org_name not in org_docs_map:
            org_docs_map[org_name] = OrganizationDocuments(
                organization=org_name,
                documents=[],
            )

        doc_preview = DocumentPreview(
            title=data.get("title"),
            file_name=data.get("file_name"),
            preview_link=data.get("pdf_url"),
            year=data.get("year"),
            description=data.get("summary"),
            countries=data.get("countries"),
            regions=data.get("regions"),
        )
        org_docs_map[org_name].documents.append(doc_preview)
    return_list = list(org_docs_map.values())
    # Print total number of docs
    return return_list


@router.get("/list-unique-organizations", response_model=list[str])
async def list_unique_organizations(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Retrieves a list of unique organizations from the database.
    """
    query = select(DocumentDB.organizations).distinct()
    result = await session.execute(query)
    organizations = result.scalars().all()
    # Flatten the list of organizations
    unique_organizations = set()
    for orgs in organizations:
        if isinstance(orgs, list):
            unique_organizations.update(orgs)
        else:
            unique_organizations.add(orgs)
    return sorted(unique_organizations)


@router.get("/list-unique-survey-types", response_model=list[str])
async def list_unique_survey_types(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Retrieves a list of unique survey types from the database.
    """
    query = select(DocumentDB.survey_type).distinct()
    result = await session.execute(query)
    survey_types = result.scalars().all()
    # Flatten the list of survey types
    unique_survey_types = set()
    for survey in survey_types:
        if isinstance(survey, list):
            unique_survey_types.update(survey)
        else:
            unique_survey_types.add(survey)
    return sorted(unique_survey_types)
