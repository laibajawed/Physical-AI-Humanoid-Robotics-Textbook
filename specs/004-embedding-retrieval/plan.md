# Implementation Plan: Embedding Retrieval & Similarity Search Validation

**Branch**: `004-embedding-retrieval` | **Date**: 2025-12-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-embedding-retrieval/spec.md`

## Summary

Implement a Python async retrieval module (`retrieve.py`) that queries the existing Qdrant `rag_embedding` collection using Cohere query embeddings. The module provides similarity search with configurable parameters, metadata filtering, and a validation suite to confirm the end-to-end RAG pipeline works correctly. This complements the ingestion pipeline (003-embedding-pipeline) and enables RAG-based chatbot integration.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `cohere`, `qdrant-client`, `python-dotenv` (same as 003-embedding-pipeline)
**Storage**: Qdrant Cloud free tier (collection: `rag_embedding`, 1024-dim vectors, cosine distance)
**Testing**: pytest with async support (`pytest-asyncio`)
**Target Platform**: Python backend module (called directly by RAG chatbot)
**Project Type**: Backend module extension
**Performance Goals**: p95 query latency <2s, embedding generation <500ms, 10 concurrent queries
**Constraints**: Cohere API rate limits (100 calls/min trial), Qdrant Cloud free tier (1GB RAM)
**Scale/Scope**: ~100-500 vectors in collection, 5-50 queries/minute expected load

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| CODE QUALITY | ✅ PASS | Python with type hints, async patterns match existing main.py |
| USER EXPERIENCE | ✅ PASS | Developer-focused API with clear error messages |
| CONTENT ORGANIZATION | ✅ PASS | Extends existing backend/ structure |
| DESIGN STANDARDS | N/A | No UI components |

**Gate Result**: PASS - Proceed to implementation

## Project Structure

### Documentation (this feature)

```text
specs/004-embedding-retrieval/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Python interface docs)
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
backend/
├── main.py              # Existing ingestion pipeline (003-embedding-pipeline)
├── retrieve.py          # NEW: Retrieval module (this feature)
├── models/              # NEW: Python dataclasses for type safety
│   ├── __init__.py
│   ├── query.py         # GoldenTestQuery model
│   └── response.py      # SearchResult, SearchResponse, ValidationReport, CollectionStats models
├── tests/
│   ├── __init__.py
│   ├── test_retrieve.py # Unit tests for retrieval
│   └── test_validation.py # Validation suite tests
├── .env                 # Environment variables (existing)
├── pyproject.toml       # Dependencies (existing)
└── README.md            # Documentation
```

**Structure Decision**: Single backend project extending existing structure. New `retrieve.py` module at root level alongside `main.py` for consistency. Models extracted to `models/` for reusability.

## Complexity Tracking

> No violations requiring justification.

| Check | Status |
|-------|--------|
| Max 3 projects | ✅ Single project |
| No ORM for simple storage | ✅ Direct Qdrant client |
| No DI framework | ✅ Simple function composition |
| No abstract factories | ✅ Direct instantiation |

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                     RAG Chatbot Backend                         │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ main.py      │    │ retrieve.py  │    │ models/      │      │
│  │ (ingestion)  │    │ (retrieval)  │    │ (types)      │      │
│  │              │    │              │    │              │      │
│  │ - URL fetch  │    │ - search()   │    │ - Query      │      │
│  │ - Extract    │    │ - validate() │    │ - Result     │      │
│  │ - Chunk      │    │ - stats()    │    │ - Response   │      │
│  │ - Embed      │    │              │    │              │      │
│  │ - Store      │    │              │    │              │      │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┘      │
│         │                   │                                   │
│         │    ┌──────────────┴──────────────┐                   │
│         │    │                             │                   │
│         ▼    ▼                             ▼                   │
│  ┌──────────────────┐            ┌─────────────────┐           │
│  │   Cohere API     │            │   Qdrant Cloud  │           │
│  │ embed-english-v3 │            │  rag_embedding  │           │
│  │ input_type:      │            │  collection     │           │
│  │ search_document  │◄──main.py  │                 │           │
│  │ search_query     │◄──retrieve │                 │           │
│  └──────────────────┘            └─────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### D1: Async Functions
- **Decision**: Use `async/await` pattern for all external API calls
- **Rationale**: Enables concurrent searches (SC-006), non-blocking I/O
- **Alternative rejected**: Sync functions (would block on I/O, poor concurrency)

### D2: Cohere input_type Differentiation
- **Decision**: Use `input_type="search_query"` for retrieval (vs `search_document` for ingestion)
- **Rationale**: Cohere recommends different input types for asymmetric search scenarios
- **Source**: Spec constraint PC-002

### D3: Prefix Matching for URL Filters
- **Decision**: Implement `source_url` filter as string prefix match using Qdrant's `match` filter
- **Rationale**: Enables both exact match and path-based filtering (FR-018)
- **Implementation**: Use Qdrant `Filter` with `FieldCondition` using `MatchText` for prefix matching

**Exact Qdrant Filter Syntax**:
```python
from qdrant_client.models import Filter, FieldCondition, MatchText

# Prefix matching for source_url (e.g., "/docs/module1")
url_filter = Filter(
    must=[
        FieldCondition(
            key="source_url",
            match=MatchText(text="/docs/module1")  # Matches any URL starting with this prefix
        )
    ]
)

# Exact matching for section
section_filter = Filter(
    must=[
        FieldCondition(
            key="section",
            match=MatchValue(value="module1-ros2-fundamentals")  # Exact match
        )
    ]
)

# Combined filter (AND logic)
combined_filter = Filter(
    must=[
        FieldCondition(key="source_url", match=MatchText(text="/docs/module1")),
        FieldCondition(key="section", match=MatchValue(value="module1-ros2-fundamentals"))
    ]
)
```

**Note**: `MatchText` performs full-text search (not pure prefix matching). During T039 implementation, verify actual behavior and consider Python post-filtering with `str.startswith()` if true prefix matching is required. `MatchValue` performs exact matching.

### D4: Golden Test Set for Validation
- **Decision**: Hardcode 5 test queries with expected URL patterns in validation module
- **Rationale**: Enables automated regression testing of retrieval quality (SC-002)
- **Source**: Spec Golden Test Set section

## API Design

### Core Functions

```python
# retrieve.py

async def search(
    query_text: str,
    limit: int = 5,
    score_threshold: float = 0.5,
    source_url_filter: str | None = None,
    section_filter: str | None = None
) -> SearchResponse:
    """
    Perform semantic similarity search against Qdrant collection.

    Args:
        query_text: Natural language query (required, 1+ chars)
        limit: Max results to return (1-20, default 5)
        score_threshold: Minimum similarity score (0.0-1.0, default 0.5)
        source_url_filter: Filter by URL prefix (optional)
        section_filter: Filter by section name (optional)

    Returns:
        SearchResponse with results, metadata, and timing info

    Raises:
        ValueError: Invalid input parameters
        ConnectionError: Qdrant/Cohere unavailable
    """

async def get_collection_stats() -> CollectionStats:
    """Get collection health and statistics."""

async def validate_pipeline() -> ValidationReport:
    """Run golden test set and return pass/fail report."""
```

### Response Models

```python
@dataclass
class SearchResult:
    similarity_score: float
    chunk_text: str
    source_url: str
    title: str
    section: str
    chunk_position: int

@dataclass
class SearchResponse:
    results: list[SearchResult]
    total_results: int
    query_time_ms: float
    warnings: list[str]

@dataclass
class ValidationReport:
    passed: bool
    total_queries: int
    passed_queries: int
    failed_queries: list[dict]
    vector_count: int
    metadata_completeness: float

@dataclass
class CollectionStats:
    """Statistics about the Qdrant collection."""
    vector_count: int           # Total number of vectors in collection
    dimensions: int             # Vector dimensions (1024 for Cohere v3)
    index_status: str           # "green" | "yellow" | "red"
    points_count: int           # Number of indexed points
    segments_count: int         # Number of segments in collection
    disk_data_size_bytes: int   # Storage usage on disk
    ram_data_size_bytes: int    # Storage usage in RAM
```

## Error Handling Strategy

| Error Type | Behavior | HTTP-equivalent |
|------------|----------|-----------------|
| Empty query | ValueError with message | 400 Bad Request |
| Query too long | Truncate + warning in response | 200 with warning |
| Qdrant unavailable | ConnectionError after 3 retries | 503 Service Unavailable |
| Cohere unavailable | ConnectionError after 3 retries | 503 Service Unavailable |
| Collection missing | ConnectionError with clear message | 404 Not Found |
| No results above threshold | Empty results list (not error) | 200 OK |
| Qdrant timeout (>10s) | TimeoutError after PC-004 timeout | 504 Gateway Timeout |
| Cohere timeout (>30s) | TimeoutError after PC-005 timeout | 504 Gateway Timeout |
| Cohere rate limit (429) | Retry with exponential backoff (max 3 attempts) | 429 Too Many Requests |

### Timeout Configuration

Per spec constraints PC-004 and PC-005:
- **Qdrant timeout**: 10 seconds per query
- **Cohere timeout**: 30 seconds per embedding request

### Retry Strategy

```python
# Exponential backoff for transient failures
RETRY_CONFIG = {
    "max_retries": 3,
    "base_delay_seconds": 1.0,
    "max_delay_seconds": 10.0,
    "backoff_multiplier": 2.0,
    "retryable_errors": [
        ConnectionError,      # Network issues
        TimeoutError,         # Timeout exceeded
        # HTTP 429 from Cohere (rate limit)
        # HTTP 503 from either service (temporary unavailable)
    ]
}
```

## Testing Strategy

### Unit Tests
- Query validation (empty, whitespace, length)
- Response model serialization
- Filter construction
- Score threshold filtering

### Integration Tests
- End-to-end search against live Qdrant
- Metadata completeness verification
- Golden test set validation
- Concurrent search handling

### Performance Tests
- Latency measurement (target <2s p95)
- Embedding generation timing (<500ms)
- Concurrent load (10 simultaneous queries)

## Dependencies

### From 003-embedding-pipeline (must exist)
- Qdrant collection `rag_embedding` with vectors
- Same environment variables: `COHERE_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`
- Same Cohere model: `embed-english-v3.0` (1024 dimensions)
- Same distance metric: Cosine

### New Dependencies (add to pyproject.toml)
- `pytest-asyncio>=0.23.0` (for async test support)

## Implementation Phases

### Phase 1: Core Retrieval (P1 Stories)
1. Create `retrieve.py` with `search()` function
2. Add query embedding generation with Cohere (`input_type="search_query"`)
3. Add Qdrant search with score threshold
4. Add JSON structured logging (matching main.py format)
5. Add response dataclasses

### Phase 2: Filtering & Configuration (P2 Stories)
1. Add `source_url_filter` prefix matching
2. Add `section_filter` exact matching
3. Add combined filter support (AND logic)
4. Add configurable limits and thresholds

### Phase 3: Validation Suite
1. Implement `get_collection_stats()`
2. Implement `validate_pipeline()` with golden test set
3. Add metadata completeness checking
4. Generate validation report

### Phase 4: Testing & Documentation
1. Write unit tests for retrieve.py
2. Write integration tests with live Qdrant
3. Add error handling tests

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Qdrant cluster suspended | Check connection at startup, clear error message |
| Cohere rate limits | Exponential backoff (same as main.py) |
| Low relevance scores | Golden test set catches regressions |
| Concurrent request failures | Connection pooling via qdrant-client |
