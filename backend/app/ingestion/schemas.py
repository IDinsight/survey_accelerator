"""This module contains the Pydantic models (schemas) for data validation and
serialization."""

from pydantic import BaseModel


class AirtableIngestionResponse(BaseModel):
    total_records_processed: int
    total_chunks_created: int
    message: str
