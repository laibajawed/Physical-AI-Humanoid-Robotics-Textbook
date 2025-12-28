"""
Response models for embedding retrieval module and RAG Agent API.

Contains dataclasses for search results, responses, and validation reports,
plus Pydantic models for chat response schema.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Chat API Response Models (Pydantic)
# =============================================================================


class SourceCitation(BaseModel):
    """Citation from Qdrant retrieval."""

    source_url: str = Field(..., description="Full URL to the book section")
    title: str = Field(..., description="Document/chapter title")
    section: str = Field(..., description="Section or heading name")
    chunk_position: int = Field(..., ge=0, description="Position of chunk within document")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score")
    snippet: str = Field(..., max_length=200, description="First 200 chars of chunk_text for preview")


class SelectedTextCitation(BaseModel):
    """Citation for selected-text mode responses."""

    source_type: str = Field(
        default="selected_text",
        description="Always 'selected_text' for this type",
    )
    selection_length: int = Field(..., ge=0, description="Character count of provided selection")
    snippet: str = Field(..., max_length=200, description="First 200 chars of selection for preview")
    relevance_note: str = Field(..., description="How the selection relates to the answer")


class ResponseMetadata(BaseModel):
    """Metadata about the response."""

    query_time_ms: float = Field(..., ge=0, description="Total processing time in milliseconds")
    retrieval_count: int = Field(..., ge=0, description="Number of chunks retrieved from Qdrant")
    mode: str = Field(
        ...,
        description="Response mode: 'full' | 'selected_text' | 'retrieval_only' | 'no_results'",
    )
    low_confidence: bool = Field(
        default=False,
        description="True if best results had scores 0.3-0.5",
    )
    request_id: UUID = Field(..., description="UUID v4 for request tracing")


class ChatResponse(BaseModel):
    """Complete response to chat request."""

    answer: Optional[str] = Field(
        None,
        description="AI-generated answer. Null if Gemini unavailable.",
    )
    fallback_message: Optional[str] = Field(
        None,
        description="Message when answer is null (graceful degradation)",
    )
    sources: List[Union[SourceCitation, SelectedTextCitation]] = Field(
        default_factory=list,
        description="Citations for the answer",
    )
    metadata: ResponseMetadata = Field(
        ...,
        description="Response metadata including timing and mode",
    )
    session_id: UUID = Field(
        ...,
        description="Session ID (provided or newly generated)",
    )


class ErrorResponse(BaseModel):
    """Structured error response for all API errors."""

    error_code: str = Field(
        ...,
        description="Machine-readable error code",
        examples=["EMPTY_QUERY"],
    )
    message: str = Field(
        ...,
        description="Human-readable error description",
        examples=["Query cannot be empty"],
    )
    request_id: UUID = Field(
        ...,
        description="UUID v4 for request tracing",
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error context",
    )


class ErrorCodes:
    """Error code constants for API responses."""

    EMPTY_QUERY = "EMPTY_QUERY"
    QUERY_TOO_LONG = "QUERY_TOO_LONG"
    SELECTION_TOO_LONG = "SELECTION_TOO_LONG"
    INVALID_SESSION_ID = "INVALID_SESSION_ID"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    QDRANT_UNAVAILABLE = "QDRANT_UNAVAILABLE"
    GEMINI_UNAVAILABLE = "GEMINI_UNAVAILABLE"


# =============================================================================
# Retrieval Module Response Models (Dataclasses - Existing)
# =============================================================================


@dataclass
class SearchResult:
    """
    A single retrieved chunk with relevance information.

    Attributes:
        similarity_score: Cosine similarity score (0.0-1.0)
        chunk_text: The text content of the chunk
        source_url: Original document URL
        title: Document title
        section: Section/module name
        chunk_position: Position in source document (0-indexed)
    """
    similarity_score: float
    chunk_text: str
    source_url: str
    title: str
    section: str
    chunk_position: int


@dataclass
class SearchResponse:
    """
    Complete response to a search query.

    Attributes:
        results: List of SearchResult objects ranked by similarity
        total_results: Count of results returned
        query_time_ms: Total processing time in milliseconds
        warnings: List of non-fatal warnings (e.g., truncated query)
    """
    results: list[SearchResult]
    total_results: int
    query_time_ms: float
    warnings: list[str] = field(default_factory=list)


@dataclass
class CollectionStats:
    """
    Statistics about the Qdrant collection.

    Attributes:
        vector_count: Total number of vectors in collection
        dimensions: Vector dimensions (1024 for Cohere v3)
        index_status: Health status ("green" | "yellow" | "red")
        points_count: Number of indexed points
        segments_count: Number of segments in collection
        disk_data_size_bytes: Storage usage on disk
        ram_data_size_bytes: Storage usage in RAM
    """
    vector_count: int
    dimensions: int
    index_status: str
    points_count: int
    segments_count: int
    disk_data_size_bytes: int
    ram_data_size_bytes: int


@dataclass
class ValidationReport:
    """
    Output of pipeline validation.

    Attributes:
        passed: Overall pass/fail status
        total_queries: Number of test queries (5 golden + 1 negative)
        passed_queries: Number of queries that passed
        failed_queries: List of dicts with query and failure reason
        vector_count: Total vectors in collection
        metadata_completeness: Percentage of vectors with full metadata (0.0-100.0)
    """
    passed: bool
    total_queries: int
    passed_queries: int
    failed_queries: list[dict[str, Any]]
    vector_count: int
    metadata_completeness: float
