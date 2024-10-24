# app/search/schemas.py

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class SearchRequest(BaseModel):
    """Schema for the search request."""

    query: str
    top_k: Optional[int] = 10


class SearchResult(BaseModel):
    """Schema for a single search result."""

    id: int
    content_text: str
    score: float


class DocumentMetadata(BaseModel):
    """Schema for the metadata of a document.
    Can be pulled from ORM as per model_config"""

    id: int
    file_id: str
    file_name: str
    page_number: int
    created_datetime_utc: datetime
    updated_datetime_utc: datetime
    countries: Optional[List[str]] = None
    organizations: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    notes: Optional[str] = None
    drive_link: Optional[str] = None
    year: Optional[int] = None
    date_added: Optional[datetime] = None
    document_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class RerankedDocument(BaseModel):
    """Schema for a document that has been reranked."""

    metadata: DocumentMetadata
    content_text: str
    relevance_score: float
    rank: int


class SearchResponse(BaseModel):
    """Final schema for the search response."""

    query: str
    results: List[RerankedDocument]
    message: Optional[str] = "Search completed successfully."
