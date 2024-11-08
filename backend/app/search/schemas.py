"""Schema definitions for the search API."""

from typing import List, Optional

from pydantic import BaseModel


class SearchRequest(BaseModel):
    """Schema for the search request parameters."""

    query: str
    precision: bool = False
    country: Optional[str] = None
    organization: Optional[str] = None
    region: Optional[str] = None


class DocumentMetadata(BaseModel):
    """Schema for the document metadata."""

    id: int
    file_id: str
    file_name: str
    title: str
    summary: str
    pdf_url: str
    countries: List[str]
    organizations: List[str]
    regions: List[str]
    year: int


class MatchedChunk(BaseModel):
    """Schema for a matched chunk in a document."""

    page_number: int
    rank: int
    explanation: Optional[str] = None  # Explanation remains


class MatchedQAPair(BaseModel):
    """Schema for a matched QA pair in a document."""

    page_number: int
    question: str
    answer: str
    rank: int


class DocumentSearchResult(BaseModel):
    """Schema for a document search result."""

    metadata: DocumentMetadata
    matches: List  # List of MatchedChunk or MatchedQAPair
    num_matches: Optional[int] = None  # Only used in precision search


class SearchResponse(BaseModel):
    """Schema for the search response."""

    query: str
    results: List[DocumentSearchResult]
    message: Optional[str] = None
