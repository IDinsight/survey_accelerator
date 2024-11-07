"""Schema definitions for the search API."""

from typing import Any, List, Optional

from pydantic import BaseModel


class SearchRequest(BaseModel):
    """Schema for the search request parameters."""

    query: str
    top_k: int = 10
    precision: bool = False  # Add the precision parameter


class DocumentMetadata(BaseModel):
    """Metadata for a document."""

    id: int
    file_id: str
    file_name: str
    title: Optional[str]
    summary: Optional[str]
    pdf_url: Optional[str]

    class Config:
        """Pydantic configuration options."""

        orm_mode = True
        from_attributes = True


class MatchedChunk(BaseModel):
    """Schema representing a matched chunk in a document."""

    page_number: int
    contextualized_chunk: str
    relevance_score: float
    rank: int


class MatchedQAPair(BaseModel):
    """Schema representing a matched question-answer pair."""

    page_number: int
    question: str
    answer: str
    relevance_score: float
    rank: int


class DocumentSearchResult(BaseModel):
    """Schema for search results grouped by document."""

    metadata: DocumentMetadata
    matches: List[Any]  # Will contain either MatchedChunk or MatchedQAPair


class SearchResponse(BaseModel):
    """Schema for the search response."""

    query: str
    results: List[DocumentSearchResult]
    message: Optional[str] = None
