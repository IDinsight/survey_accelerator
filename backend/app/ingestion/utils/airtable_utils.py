# utils/airtable_utils.py

from typing import Any, Dict

from app.config import AIRTABLE_API_KEY, AIRTABLE_CONFIGS
from app.utils import setup_logger
from pyairtable import Api

logger = setup_logger()

if not AIRTABLE_API_KEY:
    logger.error("Airtable API key not found in environment variables.")
    raise EnvironmentError("Airtable API key not found in environment variables.")


def get_airtable_records() -> Dict[str, Dict[str, Any]]:
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

        metadata_dict = {}
        for record in records:
            fields = record.get("fields", {})
            file_name = fields.get("File Name")
            if file_name:
                metadata_dict[file_name] = fields
            else:
                logger.warning(f"Record {record.get('id')} missing 'File Name' field.")
        return metadata_dict

    except Exception as e:
        logger.error(f"Error fetching records from Airtable: {e}")
        return {}
