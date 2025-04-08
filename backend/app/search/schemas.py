"""Schema definitions for the search API."""

from typing import List, Optional

from pydantic import BaseModel


# Common schemas shared across search types
class DocumentMetadata(BaseModel):
    """Schema for the document metadata."""

    id: int
    file_name: str
    title: str
    summary: str
    pdf_url: str
    highlighted_pdf_url: Optional[str] = None  # URL to the pre-highlighted PDF
    countries: List[str]
    organizations: List[str]
    regions: List[str]
    year: int


# Base search request shared by both search types
class BaseSearchRequest(BaseModel):
    """Base schema for search request parameters."""

    query: str
    country: Optional[str] = None
    organization: Optional[str] = None
    region: Optional[str] = None


# Generic search schemas
class GenericSearchRequest(BaseSearchRequest):
    """Schema for generic search request parameters."""

    pass


class MatchedChunk(BaseModel):
    """Schema for a matched chunk in a document."""

    page_number: int
    rank: int
    explanation: str
    starting_keyphrase: str = ""  # Text to highlight in the PDF


class GenericDocumentSearchResult(BaseModel):
    """Schema for a generic search document result."""

    metadata: DocumentMetadata
    matches: List[MatchedChunk]
    num_matches: int


class GenericSearchResponse(BaseModel):
    """Schema for the generic search response."""

    query: str
    results: List[GenericDocumentSearchResult]
    message: Optional[str] = None


class DocumentSearchResult(BaseModel):
    """Legacy schema for a document search result."""

    metadata: DocumentMetadata
    matches: List[MatchedChunk]
    num_matches: Optional[int] = None


class SearchResponse(BaseModel):
    """Legacy schema for the search response."""

    query: str
    results: List[DocumentSearchResult]
    message: Optional[str] = None
