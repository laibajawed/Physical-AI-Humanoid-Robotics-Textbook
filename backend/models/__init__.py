"""
Data models for embedding retrieval module and RAG Agent API.

This package contains:

Retrieval Module (dataclasses):
- SearchResult: Individual search result with metadata
- SearchResponse: Complete response wrapper
- CollectionStats: Qdrant collection statistics
- ValidationReport: Pipeline validation output
- GoldenTestQuery: Test query definition

RAG Agent API (Pydantic models):
- ChatRequest, MetadataFilter: Request models
- ChatResponse, SourceCitation, SelectedTextCitation: Response models
- ResponseMetadata, ErrorResponse, ErrorCodes: Metadata and errors
- Session, ConversationRecord, HistoryEntry: Session models
- HealthResponse, ServiceStatus: Health check models
"""

# Retrieval module models (existing)
from .response import (
    CollectionStats,
    SearchResponse,
    SearchResult,
    ValidationReport,
)
from .query import GoldenTestQuery

# Chat API response models
from .response import (
    ChatResponse,
    ErrorCodes,
    ErrorResponse,
    ResponseMetadata,
    SelectedTextCitation,
    SourceCitation,
)

# Request models
from .request import (
    ChatRequest,
    MetadataFilter,
)

# Session models
from .session import (
    ConversationHistoryResponse,
    ConversationRecord,
    HistoryEntry,
    Session,
)

# Health models
from .health import (
    HealthResponse,
    ServiceStatus,
)

__all__ = [
    # Retrieval module
    "SearchResult",
    "SearchResponse",
    "CollectionStats",
    "ValidationReport",
    "GoldenTestQuery",
    # Chat API response
    "ChatResponse",
    "SourceCitation",
    "SelectedTextCitation",
    "ResponseMetadata",
    "ErrorResponse",
    "ErrorCodes",
    # Request
    "ChatRequest",
    "MetadataFilter",
    # Session
    "Session",
    "ConversationRecord",
    "HistoryEntry",
    "ConversationHistoryResponse",
    # Health
    "HealthResponse",
    "ServiceStatus",
]
