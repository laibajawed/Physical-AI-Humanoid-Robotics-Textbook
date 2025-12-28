# Quickstart: Embedding Retrieval

**Feature**: 004-embedding-retrieval
**Date**: 2025-12-16

## Prerequisites

1. Python 3.11+
2. Environment variables configured (same as 003-embedding-pipeline):
   ```bash
   COHERE_API_KEY=your_cohere_api_key
   QDRANT_URL=https://your-cluster.qdrant.io
   QDRANT_API_KEY=your_qdrant_api_key
   ```
3. Qdrant collection `rag_embedding` populated by running the ingestion pipeline

## Installation

```bash
cd backend
pip install -r requirements.txt  # or: uv sync
```

## Basic Usage

### Perform a Search

```python
import asyncio
from retrieve import search

async def main():
    response = await search(
        query_text="What is inverse kinematics?",
        limit=5,
        score_threshold=0.5
    )

    print(f"Found {response.total_results} results in {response.query_time_ms:.0f}ms")

    for result in response.results:
        print(f"[{result.similarity_score:.2f}] {result.title}")
        print(f"  URL: {result.source_url}")
        print(f"  Text: {result.chunk_text[:100]}...")
        print()

asyncio.run(main())
```

### Search with Filters

```python
# Filter by URL prefix (e.g., only module-2 content)
response = await search(
    query_text="robot motion",
    source_url_filter="/docs/module-2"
)

# Filter by section
response = await search(
    query_text="sensors",
    section_filter="module4-vla-systems"
)

# Combined filters (AND logic)
response = await search(
    query_text="control systems",
    source_url_filter="/docs/module-3",
    section_filter="module3-advanced-robotics-nvidia-isaac"
)
```

### Get Collection Statistics

```python
from retrieve import get_collection_stats

async def check_health():
    stats = await get_collection_stats()
    print(f"Total vectors: {stats['vector_count']}")
    print(f"Dimensions: {stats['dimensions']}")
    print(f"Index status: {stats['index_status']}")

asyncio.run(check_health())
```

### Run Pipeline Validation

```python
from retrieve import validate_pipeline

async def validate():
    report = await validate_pipeline()

    print(f"Validation: {'PASSED' if report.passed else 'FAILED'}")
    print(f"Queries passed: {report.passed_queries}/{report.total_queries}")
    print(f"Vector count: {report.vector_count}")
    print(f"Metadata completeness: {report.metadata_completeness:.1f}%")

    if report.failed_queries:
        print("\nFailed queries:")
        for failure in report.failed_queries:
            print(f"  - {failure['query']}: {failure['reason']}")

asyncio.run(validate())
```

## Response Structure

### SearchResponse

```python
@dataclass
class SearchResponse:
    results: list[SearchResult]  # Ranked by similarity
    total_results: int           # Count of results
    query_time_ms: float         # Processing time
    warnings: list[str]          # Non-fatal warnings
```

### SearchResult

```python
@dataclass
class SearchResult:
    similarity_score: float   # 0.0-1.0 (cosine similarity)
    chunk_text: str           # The retrieved text
    source_url: str           # Original document URL
    title: str                # Document title
    section: str              # Module/section name
    chunk_position: int       # Position in document
```

## Error Handling

```python
from retrieve import search

async def safe_search():
    try:
        response = await search("my query")
        return response
    except ValueError as e:
        # Invalid input (empty query, invalid params)
        print(f"Input error: {e}")
    except ConnectionError as e:
        # Qdrant or Cohere unavailable
        print(f"Service error: {e}")
```

## Running Tests

```bash
# Unit tests
pytest backend/tests/test_retrieve.py -v

# Integration tests (requires live Qdrant)
pytest backend/tests/test_retrieve.py -v -m integration

# Run validation suite
python -c "import asyncio; from retrieve import validate_pipeline; print(asyncio.run(validate_pipeline()))"
```

## Logging

All operations emit JSON structured logs:

```json
{
  "timestamp": "2025-12-16T10:30:00Z",
  "level": "INFO",
  "stage": "search",
  "message": "Search completed",
  "query_length": 28,
  "result_count": 5,
  "latency_ms": 450
}
```

## Performance Expectations

| Metric | Target | Constraint |
|--------|--------|------------|
| Query latency (p95) | <2 seconds | SC-001 |
| Embedding generation | <500ms | SC-007 |
| Concurrent queries | 10 | SC-006 |
| Relevance (golden set) | ≥80% | SC-002 |
