# Data Model: Embedding Retrieval

**Feature**: 004-embedding-retrieval
**Date**: 2025-12-16

## Entity Overview

This feature operates on the existing Qdrant collection created by 003-embedding-pipeline. No new persistent storage is created; the models below are runtime data structures.

## Entities

### SearchResult

A single retrieved chunk with relevance information.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| similarity_score | float | Cosine similarity score | 0.0-1.0 |
| chunk_text | str | The text content of the chunk | Non-empty |
| source_url | str | Original document URL | Valid URL |
| title | str | Document title | Non-empty |
| section | str | Section/module name | String |
| chunk_position | int | Position in source document | >= 0 |

### SearchResponse

Complete response to a search query.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| results | list[SearchResult] | Ranked results | 0-20 items |
| total_results | int | Count of results | >= 0 |
| query_time_ms | float | Total processing time | > 0 |
| warnings | list[str] | Non-fatal warnings | Optional |

### ValidationReport

Output of pipeline validation.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| passed | bool | Overall pass/fail | Boolean |
| total_queries | int | Number of test queries | 5 (golden set) |
| passed_queries | int | Queries that passed | 0-5 |
| failed_queries | list[dict] | Details of failures | Query, reason |
| vector_count | int | Total vectors in collection | >= 0 |
| metadata_completeness | float | % of vectors with full metadata | 0.0-100.0 |

### GoldenTestQuery

Test query with expected results (hardcoded).

| Field | Type | Description |
|-------|------|-------------|
| query_text | str | Natural language query |
| expected_url_patterns | list[str] | URL patterns that should match |
| min_score | float | Minimum acceptable similarity (0.6) |

### CollectionStats

Statistics returned from `get_collection_stats()`.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| vector_count | int | Total vectors in collection | >= 0 |
| dimensions | int | Vector dimensions | 1024 (Cohere v3) |
| index_status | str | Health status | "green" \| "yellow" \| "red" |
| points_count | int | Number of indexed points | >= 0 |
| segments_count | int | Number of segments | >= 1 |
| disk_data_size_bytes | int | Storage on disk | >= 0 |
| ram_data_size_bytes | int | Storage in RAM | >= 0 |

## Qdrant Collection Schema (Reference)

Existing collection from 003-embedding-pipeline:

```
Collection: rag_embedding
├── Vector: 1024 dimensions (Cohere embed-english-v3.0)
├── Distance: Cosine
└── Payload:
    ├── source_url: string
    ├── title: string
    ├── section: string
    ├── chunk_position: integer
    ├── chunk_text: string
    └── content_hash: string (SHA-256)
```

## Relationships

```text
SearchResponse 1──* SearchResult
ValidationReport 1──* GoldenTestQuery (5 hardcoded)
SearchResult ←→ Qdrant Point (maps payload fields)
```

## Validation Rules

### Query Input
- `query_text`: Non-empty, max 8000 tokens
- `limit`: 1-20 (default 5)
- `score_threshold`: 0.0-1.0 (default 0.5)
- `source_url_filter`: Optional, prefix match
- `section_filter`: Optional, exact match

### Response Output
- Results sorted by similarity_score descending
- All metadata fields must be present (SC-003)
- Empty results valid when no matches above threshold

## Golden Test Set (Hardcoded)

| Query | Expected URL Pattern | Min Score |
|-------|---------------------|-----------|
| "What is inverse kinematics?" | `/docs/module1-ros2-fundamentals` or `/docs/module3-advanced-robotics` | 0.6 |
| "How does robot arm control work?" | `/docs/module1-ros2-fundamentals/chapter3` or `/docs/module3-advanced-robotics/chapter8` | 0.6 |
| "Explain sensor fusion techniques" | `/docs/module4-vla-systems` or `/docs/module1-ros2-fundamentals` | 0.6 |
| "What is motion planning for robots?" | `/docs/module1-ros2-fundamentals/chapter2` or `/docs/module2-simulation` | 0.6 |
| "How do coordinate transforms work?" | `/docs/module1-ros2-fundamentals` or `/docs/introduction` | 0.6 |

### Negative Test Query (Out-of-Domain)

| Query | Expected Behavior |
|-------|-------------------|
| "What is the best pizza recipe?" | Empty results OR all results have similarity_score < 0.5 |

**Pass Criteria**: ≥4/5 golden queries return expected URL in top-5 with score ≥0.6, AND negative test returns no relevant results
