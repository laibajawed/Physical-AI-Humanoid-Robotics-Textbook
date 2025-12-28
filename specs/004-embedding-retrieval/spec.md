# Feature Specification: Embedding Retrieval & Similarity Search Validation

**Feature Branch**: `004-embedding-retrieval`
**Created**: 2025-12-16
**Status**: Draft
**Input**: User description: "Retrieve stored embeddings from Qdrant, run similarity queries, and confirm the end-to-end extraction + embedding + vector storage pipeline works correctly."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Similarity Search (Priority: P1)

As a developer validating the RAG pipeline, I want to submit a natural language query and receive relevant text chunks so that I can confirm vectors are stored correctly and retrieval works.

**Why this priority**: This is the fundamental retrieval operation. Without basic search working, no RAG functionality is possible. This validates that the entire ingestion pipeline produced usable vectors.

**Independent Test**: Can be fully tested by submitting a sample query (e.g., "What is inverse kinematics?") and verifying that relevant chunks from the robotics book are returned with similarity scores.

**Acceptance Scenarios**:

1. **Given** vectors exist in Qdrant from the embedding pipeline, **When** I submit a text query, **Then** I receive a ranked list of relevant text chunks with similarity scores.
2. **Given** a query about robotics concepts covered in the book, **When** I search, **Then** the top-3 results contain content semantically related to my query.
3. **Given** a well-formed query, **When** retrieval completes, **Then** results are returned in under 2 seconds.

---

### User Story 2 - Source Attribution & Metadata Verification (Priority: P1)

As a developer building RAG responses, I want each retrieved chunk to include complete source metadata so that I can attribute answers to specific book sections and provide citations.

**Why this priority**: Source attribution is essential for trustworthy RAG answers. Without metadata, retrieved content cannot be traced back to its origin, making the system unreliable for users.

**Independent Test**: Can be tested by running any search query and verifying each result contains complete metadata fields (source_url, title, section, chunk_position).

**Acceptance Scenarios**:

1. **Given** a search returns results, **When** I examine any result, **Then** it includes: source_url (valid URL), title (non-empty), section (string), chunk_position (integer), and chunk_text (the actual content).
2. **Given** a result with source_url, **When** I visit that URL, **Then** the page exists and contains content related to the chunk_text.
3. **Given** multiple results from the same document, **When** I compare chunk_positions, **Then** they are sequential and correctly ordered.

---

### User Story 3 - Empty & Low-Confidence Result Handling (Priority: P1)

As a developer, I want the retrieval system to gracefully handle queries that produce no results or only low-confidence matches so that the RAG system can respond appropriately instead of failing.

**Why this priority**: Production systems must handle edge cases gracefully. Queries outside the book's domain or ambiguous queries must not crash the system or return misleading results.

**Independent Test**: Can be tested by submitting queries completely unrelated to robotics (e.g., "best pizza recipe") and verifying the system returns empty results or flags low confidence.

**Acceptance Scenarios**:

1. **Given** a query completely unrelated to book content, **When** I search, **Then** the system returns an empty result set or results below the confidence threshold.
2. **Given** a configurable similarity threshold (default 0.5), **When** results fall below this threshold, **Then** they are either filtered out or clearly marked as low-confidence.
3. **Given** the Qdrant collection is empty, **When** I attempt a search, **Then** the system returns an empty result set with appropriate messaging (not an error).

---

### User Story 4 - End-to-End Pipeline Validation (Priority: P2)

As a developer completing the RAG backend, I want to run validation tests that confirm the entire pipeline (extraction → embedding → storage → retrieval) works correctly so that I can deploy with confidence.

**Why this priority**: Comprehensive validation ensures all pipeline components work together. While individual searches test retrieval, explicit validation tests confirm data integrity across the system.

**Independent Test**: Can be tested by running a validation suite that checks vector count, metadata completeness, and search accuracy against known test queries.

**Acceptance Scenarios**:

1. **Given** the embedding pipeline has run, **When** I query collection statistics, **Then** the vector count matches the expected number of chunks (based on document count and average chunks per doc).
2. **Given** a set of test queries with expected source documents, **When** I run the validation suite, **Then** at least 80% of queries return expected documents in top-5 results.
3. **Given** the validation suite runs, **When** it completes, **Then** it produces a report showing: total vectors, metadata completeness percentage, search accuracy score, and any anomalies detected.

---

### User Story 5 - Configurable Search Parameters (Priority: P2)

As a developer fine-tuning RAG quality, I want to configure search parameters (result count, similarity threshold, filters) so that I can optimize retrieval for different use cases.

**Why this priority**: Different RAG scenarios require different retrieval configurations. A Q&A bot may need high-precision top-3 results, while a research tool may need broader top-10 results with lower threshold.

**Independent Test**: Can be tested by running the same query with different parameters and verifying results change accordingly.

**Acceptance Scenarios**:

1. **Given** I specify `limit=5`, **When** I search, **Then** I receive at most 5 results.
2. **Given** I specify `score_threshold=0.7`, **When** I search, **Then** all returned results have similarity score >= 0.7.
3. **Given** I filter by source_url pattern, **When** I search, **Then** only results matching that URL pattern are returned.

---

### Edge Cases

- What happens when the query text is empty or whitespace only?
  - System returns an error response indicating invalid input. No embedding is generated for empty queries.

- What happens when the query is extremely long (>8000 tokens)?
  - Query is truncated to the embedding model's limit with a warning logged. Search proceeds with truncated query.

- What happens when Qdrant Cloud is temporarily unavailable?
  - System returns an error with clear message indicating the external dependency is unavailable. Implements retry with exponential backoff (3 attempts).

- What happens when the Cohere API fails during query embedding?
  - System returns an error with clear message about embedding generation failure. Includes retry logic with backoff.

- What happens when search returns results but metadata is incomplete?
  - System returns available results with warning flag on incomplete entries. Validation suite would catch this as a data integrity issue.

- What happens when similarity scores are all below threshold?
  - System returns empty result set with metadata indicating "no confident matches found" rather than forcing low-quality results.

- What happens when the collection doesn't exist?
  - System returns a clear error indicating the collection must be created via the embedding pipeline first.

- What happens when concurrent searches are executed?
  - System handles concurrent requests without blocking. Qdrant Cloud supports concurrent queries natively.

## Requirements *(mandatory)*

### Functional Requirements

**Query Processing**

- **FR-001**: System MUST accept natural language text queries for similarity search
- **FR-002**: System MUST generate query embeddings using Cohere `embed-english-v3.0` with `input_type="search_query"`
- **FR-003**: System MUST validate query input is non-empty and within token limits before processing
- **FR-004**: System MUST handle query embedding failures gracefully with clear error messages

**Similarity Search**

- **FR-005**: System MUST perform vector similarity search against the `rag_embedding` collection in Qdrant
- **FR-006**: System MUST return results ranked by similarity score (highest first)
- **FR-007**: System MUST support configurable result limit (default: 5, max: 20)
- **FR-008**: System MUST support configurable similarity threshold (default: 0.5, range: 0.0-1.0)
- **FR-009**: System MUST use Cosine similarity metric consistent with collection configuration

**Result Formatting**

- **FR-010**: System MUST return for each result: similarity_score, chunk_text, source_url, title, section, chunk_position
- **FR-011**: System MUST preserve all metadata stored during ingestion in retrieval results
- **FR-012**: System MUST return results in a structured format suitable for RAG context building
- **FR-013**: System MUST include query processing time in response metadata

**Error Handling**

- **FR-014**: System MUST return empty result set (not error) when no matches meet threshold
- **FR-015**: System MUST return appropriate error response when Qdrant connection fails
- **FR-016**: System MUST return appropriate error response when Cohere API fails
- **FR-017**: System MUST handle missing or empty collection gracefully with descriptive error

**Filtering & Search Options**

- **FR-018**: System MUST support filtering results by source_url using prefix matching (e.g., filter `"/docs/module-1"` matches URLs starting with that path); exact match is a special case of prefix match
- **FR-019**: System MUST support filtering results by section name
- **FR-020**: System MUST allow combining multiple filters with AND logic

**Observability**

- **FR-021**: System MUST emit JSON structured logs for each search operation with fields: timestamp, level, query_length, result_count, latency_ms, error (if any)
- **FR-022**: System MUST use the same logging format as 003-embedding-pipeline for consistency

**Pipeline Validation**

- **FR-023**: System MUST provide a validation endpoint/function that checks collection health
- **FR-024**: System MUST report collection statistics: total vectors, dimensions, index status
- **FR-025**: System MUST validate that stored vectors have complete metadata
- **FR-026**: System MUST support running predefined test queries to measure search accuracy
- **FR-027**: System MUST include 5 domain-specific test queries based on robotics book content (e.g., "inverse kinematics", "robot arm control", "sensor fusion", "motion planning", "coordinate transforms")
- **FR-028**: System MUST define a golden test set with ground-truth mappings for validation (see Golden Test Set below)

### Golden Test Set

The following test queries with expected source URL patterns constitute the ground-truth for measuring SC-002 (80% relevance):

| Query | Expected Source URL Pattern | Rationale |
|-------|----------------------------|-----------|
| "What is inverse kinematics?" | `/docs/module1-ros2-fundamentals` or `/docs/module3-advanced-robotics` | Robot manipulation and control concepts |
| "How does robot arm control work?" | `/docs/module1-ros2-fundamentals/chapter3` or `/docs/module3-advanced-robotics/chapter8` | Manipulation chapters |
| "Explain sensor fusion techniques" | `/docs/module4-vla-systems` or `/docs/module1-ros2-fundamentals` | VLA systems and ROS2 sensor topics |
| "What is motion planning for robots?" | `/docs/module1-ros2-fundamentals/chapter2` or `/docs/module2-simulation` | Navigation and simulation chapters |
| "How do coordinate transforms work?" | `/docs/module1-ros2-fundamentals` or `/docs/introduction` | ROS2 fundamentals and introduction |

**Negative Test Query** (out-of-domain):
| Query | Expected Behavior |
|-------|-------------------|
| "What is the best pizza recipe?" | Empty results OR all results have similarity_score < 0.5 |

**Validation Rule**: A query passes if ANY result in top-5 has source_url containing the expected pattern AND similarity_score ≥ 0.6. Overall validation passes if ≥4 of 5 queries (80%) pass. The negative test must return empty or low-confidence results.

### Key Entities

- **Query**: A natural language search input from the user; attributes include query_text, embedding (1024-dim vector), and processing_time
- **SearchResult**: A single retrieved chunk with relevance information; attributes include similarity_score, chunk_text, source_url, title, section, chunk_position
- **SearchResponse**: The complete response to a query; attributes include results array, total_results, query_time, and any warnings
- **ValidationReport**: Output of pipeline validation; attributes include vector_count, metadata_completeness, sample_query_results, anomalies

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Similarity search returns results in under 2 seconds for 95% of queries
- **SC-002**: Top-5 search results for domain-relevant queries achieve 80% relevance, where relevance is defined as: the expected source document appears in top-5 results with similarity score ≥ 0.6 (measured against golden test set of 5 queries with known ground-truth source URLs)
- **SC-003**: 100% of retrieved results include complete metadata (source_url, title, section, chunk_position, chunk_text)
- **SC-004**: System correctly returns empty results for out-of-domain queries (no false positives above threshold)
- **SC-005**: Validation suite confirms vector count matches expected chunk count (within 5% margin)
- **SC-006**: System handles 10 concurrent search requests without errors; p95 latency under concurrent load ≤ 3 seconds (≤1.5x single-request latency)
- **SC-007**: Query embedding generation completes in under 500ms
- **SC-008**: System gracefully handles external service failures with clear error messages (no unhandled exceptions)

## Constraints

### Input Constraints
- **IC-001**: Query text must be non-empty string
- **IC-002**: Query text maximum length: 8000 tokens (~32,000 characters using ~4 chars/token heuristic; truncate with warning if exceeded)
- **IC-003**: Result limit range: 1-20 (default: 5)
- **IC-004**: Similarity threshold range: 0.0-1.0 (default: 0.5)

### Processing Constraints
- **PC-001**: Query embedding model: Cohere `embed-english-v3.0` (1024 dimensions)
- **PC-002**: Query embedding input_type: `search_query` (different from `search_document` used in ingestion)
- **PC-003**: Distance metric: Cosine similarity (matching collection configuration)
- **PC-004**: Connection timeout: 10 seconds for Qdrant operations
- **PC-005**: Embedding timeout: 30 seconds for Cohere API calls

### Output Constraints
- **OC-001**: Response format: Structured object with results array and metadata
- **OC-002**: Each result must include all metadata fields from ingestion
- **OC-003**: Similarity scores normalized to 0.0-1.0 range
- **OC-004**: Results ordered by similarity score descending

### Operational Constraints
- **OpC-001**: Qdrant deployment: Same Qdrant Cloud cluster as embedding pipeline
- **OpC-002**: Collection name: `rag_embedding` (must exist from embedding pipeline)
- **OpC-003**: Credentials: Same environment variables as embedding pipeline (COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY)
- **OpC-004**: Retry policy: 3 attempts with exponential backoff for transient failures
- **OpC-005**: API exposure: Python module with async functions (no separate REST endpoint; RAG backend calls directly)

## Clarifications

### Session 2025-12-16

- Q: What logging/metrics should be emitted for operational monitoring? → A: JSON structured logs with fields: timestamp, level, query_length, result_count, latency_ms, error (matching 003-embedding-pipeline format)
- Q: How will the search functionality be exposed to callers? → A: Python module with async functions callable directly by the RAG chatbot backend (no separate REST API)
- Q: What test queries should the validation suite use? → A: 5 domain-specific queries based on robotics book content (e.g., "inverse kinematics", "robot arm control", "sensor fusion", "motion planning", "coordinate transforms")

### Spec Review Refinements 2025-12-16

Applied HIGH priority refinements from spec-2-retrieval-reviewer agent:
- **GAP-001**: SC-002 now defines relevance as "expected source document in top-5 with score ≥ 0.6"
- **GAP-003**: SC-006 now quantifies concurrent latency as "p95 ≤ 3 seconds (≤1.5x single-request)"
- **GAP-007**: FR-018 now specifies "prefix matching" for URL filters with example
- **GAP-010**: Added Golden Test Set with 5 queries, expected URL patterns, and validation rule (≥4/5 = 80% pass)

## Assumptions

- The embedding pipeline (003-embedding-pipeline) has successfully run and populated the `rag_embedding` collection
- The Qdrant Cloud cluster is active and accessible (not suspended due to inactivity)
- Cohere API key has sufficient quota for query embeddings
- Query volume is within Qdrant Cloud free tier limits
- Users understand that search quality depends on the quality of ingested content
- The 1024-dimensional Cohere embeddings support effective semantic similarity matching

## Not Building (Out of Scope)

- Hybrid search combining vector and keyword search
- Query expansion or rewriting
- Relevance feedback / learning to rank
- Caching of query embeddings or results
- User authentication for search API
- Rate limiting for search API
- Multi-collection search
- Cross-language search support
- Result re-ranking with ML models
- Search analytics or query logging
- Streaming search results
- Batch query processing
- Custom embedding models or fine-tuning
