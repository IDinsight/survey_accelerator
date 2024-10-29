# utils/airtable_utils.py

from typing import Any, Dict

from pyairtable import Api
from sqlalchemy import select

from app.config import AIRTABLE_API_KEY, AIRTABLE_CONFIGS
from app.database import get_async_session
from app.ingestion.models import DocumentDB
from app.utils import setup_logger

logger = setup_logger()

if not AIRTABLE_API_KEY:
    logger.error("Airtable API key not found in environment variables.")
    raise EnvironmentError("Airtable API key not found in environment variables.")


def get_airtable_records() -> list:
    """
    Fetch records from Airtable and return a dictionary of metadata keyed by file name.
    """
    try:
        airtable_config: Dict[str, str] = AIRTABLE_CONFIGS.get("default", {})
        if not airtable_config:
            logger.error("Airtable configuration 'default' not found.")
            raise KeyError("Airtable configuration 'default' not found.")

        base_id = airtable_config.get("AIRTABLE_BASE_ID")
        table_name = airtable_config.get("TABLE_NAME")
        if not base_id or not table_name:
            logger.error("Airtable base ID or table name not found in configuration.")
            raise KeyError("Airtable base ID or table name not found in configuration.")

        api = Api(AIRTABLE_API_KEY)
        table = api.table(base_id, table_name)
        records = table.all()
        print(records)
        return records

    except Exception as e:
        logger.error(f"Error fetching records from Airtable: {e}")
        return []


async def get_missing_document_ids(records: list[Dict[str, Any]]) -> list[int]:
    """
    Compare Airtable records with database records to find missing document IDs.
    Returns a list of document IDs that are in Airtable but not in the database.
    """
    # Extract 'ID's from the 'fields' of each record
    airtable_ids = []
    for record in records:
        fields = record.get("fields", {})
        id_value = fields.get("ID")
        if id_value is not None:
            airtable_ids.append(id_value)
        else:
            logger.warning(f"Record {record.get('id')} is missing 'ID' field.")

    # Get document_ids from the database
    db_document_ids: list[int] = []
    async for session in get_async_session():
        result = await session.execute(select(DocumentDB.document_id).distinct())
        db_document_ids = result.scalars().all()
        break  # Exit after obtaining the session

    # Find IDs that are in Airtable but not in the database
    missing_ids = list(set(airtable_ids) - set(db_document_ids))
    return missing_ids
