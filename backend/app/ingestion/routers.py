# routers.py

from fastapi import APIRouter, Body, Depends

from app.auth.dependencies import authenticate_key
from app.ingestion.schemas import AirtableIngestionResponse
from app.ingestion.utils.airtable_utils import (
    get_airtable_records,
    get_missing_document_ids,
)
from app.ingestion.utils.record_processing import ingest_records
from app.utils import setup_logger

logger = setup_logger()

router = APIRouter(
    dependencies=[Depends(authenticate_key)],
    prefix="/ingestion",
    tags=["Document Ingestion"],
)

TAG_METADATA = {
    "name": "Ingestion",
    "description": "Endpoints for ingesting documents from Airtable records",
}


@router.post("/airtable", response_model=AirtableIngestionResponse)
async def ingest_airtable(
    ids: list[int] = Body(..., embed=True),
) -> AirtableIngestionResponse:
    """
    Ingest documents from Airtable records with page-level progress logging.
    Accepts a list of document IDs to process.
    """
    records = get_airtable_records()
    if not records:
        return AirtableIngestionResponse(
            total_records_processed=0,
            total_chunks_created=0,
            message="No records found in Airtable.",
        )

    # Map IDs to records
    airtable_id_to_record = {}
    for record in records:
        fields = record.get("fields", {})
        id_value = fields.get("ID")
        if id_value is not None:
            airtable_id_to_record[id_value] = record

    records_to_process = [
        airtable_id_to_record[id_] for id_ in ids if id_ in airtable_id_to_record
    ]
    if not records_to_process:
        return AirtableIngestionResponse(
            total_records_processed=0,
            total_chunks_created=0,
            message="No matching records found for the provided IDs.",
        )

    return await ingest_records(records_to_process)


@router.post("/airtable/refresh", response_model=AirtableIngestionResponse)
async def airtable_refresh_and_ingest() -> AirtableIngestionResponse:
    """
    Refresh the list of documents by comparing Airtable 'ID' fields with database
    'document_id's. Automatically ingest the missing documents.
    """
    records = get_airtable_records()
    if not records:
        return AirtableIngestionResponse(
            total_records_processed=0,
            total_chunks_created=0,
            message="No records found in Airtable.",
        )

    # Get missing IDs
    missing_ids = await get_missing_document_ids(records)
    if not missing_ids:
        return AirtableIngestionResponse(
            total_records_processed=0,
            total_chunks_created=0,
            message="No new documents to ingest.",
        )

    # Map IDs to records
    airtable_id_to_record = {}
    for record in records:
        fields = record.get("fields", {})
        id_value = fields.get("ID")
        if id_value is not None:
            airtable_id_to_record[id_value] = record

    records_to_process = [
        airtable_id_to_record[id_]
        for id_ in missing_ids
        if id_ in airtable_id_to_record
    ]

    return await ingest_records(records_to_process)
