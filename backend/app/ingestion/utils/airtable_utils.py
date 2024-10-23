# utils/airtable_utils.py

import os
from pyairtable import Api
from app.config import AIRTABLE_CONFIGS
from app.utils import setup_logger

logger = setup_logger()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")


def get_airtable_records():
    """
    Fetch records from Airtable.
    """
    airtable_config = AIRTABLE_CONFIGS["default"]
    base_id = airtable_config["AIRTABLE_BASE_ID"]
    table_name = airtable_config["TABLE_NAME"]
    api = Api(AIRTABLE_API_KEY)
    table = api.table(base_id, table_name)
    records = table.all()
    return records
