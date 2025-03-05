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


# Precision search schemas
class PrecisionSearchRequest(BaseSearchRequest):
    """Schema for precision search request parameters."""

    pass


class MatchedQAPair(BaseModel):
    """Schema for a matched QA pair in a document."""

    page_number: int
    question: str
    answer: str
    rank: int


class PrecisionDocumentSearchResult(BaseModel):
    """Schema for a precision search document result."""

    metadata: DocumentMetadata
    matches: List[MatchedQAPair]
    num_matches: int


class PrecisionSearchResponse(BaseModel):
    """Schema for the precision search response."""

    query: str
    results: List[PrecisionDocumentSearchResult]
    message: Optional[str] = None


# Legacy schemas for backward compatibility (to be removed once migration is complete)
class SearchRequest(BaseSearchRequest):
    """Legacy schema for the search request parameters."""

    precision: bool = False


class DocumentSearchResult(BaseModel):
    """Legacy schema for a document search result."""

    metadata: DocumentMetadata
    matches: List  # List of MatchedChunk or MatchedQAPair
    num_matches: Optional[int] = None


class SearchResponse(BaseModel):
    """Legacy schema for the search response."""

    query: str
    results: List[DocumentSearchResult]
    message: Optional[str] = None
