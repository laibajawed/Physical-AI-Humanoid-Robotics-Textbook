# Research: Embedding Retrieval & Similarity Search

**Feature**: 004-embedding-retrieval
**Date**: 2025-12-16

## Research Summary

All technical decisions for this feature are pre-resolved based on alignment with 003-embedding-pipeline and explicit spec constraints. No external research was required.

## Decisions

### R1: Cohere Query Embedding Configuration

**Decision**: Use `input_type="search_query"` for query embeddings
**Rationale**: Cohere's embed-english-v3.0 model is designed for asymmetric search. The ingestion pipeline uses `input_type="search_document"` for indexing, and retrieval should use `input_type="search_query"` for queries to optimize similarity matching.
**Source**: Spec constraint PC-002, Cohere documentation
**Alternatives considered**:
- Use `search_document` for both (rejected: suboptimal asymmetric search)
- Use different model (rejected: must match ingestion model dimensions)

### R2: Qdrant Filter Implementation

**Decision**: Use Qdrant `Filter` with `FieldCondition` for metadata filtering
**Rationale**: Qdrant's native filtering is efficient and supports prefix matching via `match.text` condition. This aligns with FR-018 (prefix matching for source_url).
**Source**: Qdrant Python client documentation
**Alternatives considered**:
- Post-filter in Python (rejected: inefficient for large result sets)
- Full-text search (rejected: out of scope per spec)

### R3: Async vs Sync Implementation

**Decision**: Use async functions with `asyncio`
**Rationale**: Enables non-blocking I/O for Qdrant and Cohere API calls, supporting concurrent search requests (SC-006: 10 concurrent requests).
**Source**: Python best practices for I/O-bound operations
**Alternatives considered**:
- Sync with threading (rejected: more complex, GIL limitations)
- Sync blocking (rejected: poor concurrency support)

### R4: Error Handling Pattern

**Decision**: Use try/except with exponential backoff for transient failures, ValueError for input validation
**Rationale**: Matches pattern in main.py (003-embedding-pipeline) for consistency. Cohere and Qdrant can have transient failures requiring retry.
**Source**: Existing main.py implementation
**Alternatives considered**:
- Custom exception hierarchy (rejected: over-engineering for this scope)
- No retry (rejected: poor reliability)

### R5: Logging Format

**Decision**: JSON structured logs matching main.py format
**Rationale**: Enables unified log analysis across ingestion and retrieval pipelines. Fields: timestamp, level, stage, message, query_length, result_count, latency_ms, error.
**Source**: Spec FR-021, FR-022
**Alternatives considered**:
- Plain text logs (rejected: harder to parse)
- Different JSON schema (rejected: inconsistency with ingestion)

## No Clarifications Needed

All technical questions were resolved through:
1. Spec constraints (PC-001 through PC-005)
2. Alignment with 003-embedding-pipeline implementation
3. Explicit clarifications in spec (Clarifications section)

## Dependencies Verified

| Dependency | Version | Status |
|------------|---------|--------|
| cohere | >=4.0.0 | ✅ Already in pyproject.toml |
| qdrant-client | >=1.7.0 | ✅ Already in pyproject.toml |
| python-dotenv | >=1.0.0 | ✅ Already in pyproject.toml |
| pytest-asyncio | >=0.23.0 | ⚠️ Add for testing |
