"""This module contains the Pydantic models (schemas) for data validation and
serialization."""

from typing import Any, List, Optional

from pydantic import BaseModel


class AirtableIngestionResponse(BaseModel):
    total_records_processed: int
    total_chunks_created: int
    message: str


class DocumentPreview(BaseModel):
    title: Optional[str]
    file_name: str
    preview_link: Optional[str]
    year: Optional[int]
    description: Optional[str]  
    countries: Optional[Any] 
    regions: Optional[Any]


class OrganizationDocuments(BaseModel):
    organization: str
    documents: List[DocumentPreview]
