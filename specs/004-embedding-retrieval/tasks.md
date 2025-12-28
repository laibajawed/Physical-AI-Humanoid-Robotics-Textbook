# Tasks: Embedding Retrieval & Similarity Search Validation

**Input**: Design documents from `/specs/004-embedding-retrieval/`
**Prerequisites**: plan.md (✅), spec.md (✅), research.md (✅), data-model.md (✅), quickstart.md (✅)

**Tests**: Not explicitly requested in spec - tests included only where validation suite is specified (FR-023 to FR-028).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend module**: `backend/` at repository root (extends 003-embedding-pipeline)
- Models in `backend/models/`
- Tests in `backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and module structure

- [ ] T001 Add pytest-asyncio>=0.23.0 to backend/pyproject.toml or backend/requirements.txt
- [ ] T002 Create backend/models/ directory structure with `__init__.py` in backend/models/__init__.py
- [ ] T003 [P] Create backend/tests/ directory structure with `__init__.py` in backend/tests/__init__.py
- [ ] T004 [P] Create backend/retrieve.py with module docstring and imports (cohere, qdrant-client, asyncio, dotenv)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and shared utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create SearchResult dataclass in backend/models/response.py with fields: similarity_score, chunk_text, source_url, title, section, chunk_position
- [ ] T006 [P] Create SearchResponse dataclass in backend/models/response.py with fields: results, total_results, query_time_ms, warnings
- [ ] T007 [P] Create CollectionStats dataclass in backend/models/response.py with fields: vector_count, dimensions, index_status, points_count, segments_count, disk_data_size_bytes, ram_data_size_bytes
- [ ] T008 [P] Create ValidationReport dataclass in backend/models/response.py with fields: passed, total_queries, passed_queries, failed_queries, vector_count, metadata_completeness
- [ ] T009 [P] Create GoldenTestQuery dataclass in backend/models/query.py with fields: query_text, expected_url_patterns, min_score
- [ ] T010 Add JSON structured logging helper function `log_search()` in backend/retrieve.py matching main.py format (timestamp, level, stage, message, query_length, result_count, latency_ms, error)
- [ ] T011 Add async client initialization functions `_get_cohere_client()` and `_get_qdrant_client()` in backend/retrieve.py using environment variables
- [ ] T012 Add retry helper function `_retry_with_backoff()` in backend/retrieve.py for transient failures (max 3 retries, exponential backoff)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Basic Similarity Search (Priority: P1) 🎯 MVP

**Goal**: Submit natural language queries and receive ranked relevant text chunks with similarity scores

**Independent Test**: Submit query "What is inverse kinematics?" and verify relevant chunks from robotics book are returned with similarity scores in <2s

### Implementation for User Story 1

- [ ] T013 [US1] Implement async `_generate_query_embedding()` function in backend/retrieve.py using Cohere embed-english-v3.0 with input_type="search_query"
- [ ] T014 [US1] Implement async `_search_qdrant()` helper in backend/retrieve.py that queries rag_embedding collection with score threshold
- [ ] T015 [US1] Implement main async `search()` function in backend/retrieve.py with signature: `search(query_text: str, limit: int = 5, score_threshold: float = 0.5) -> SearchResponse`
- [ ] T016 [US1] Add query validation in `search()`: reject empty/whitespace queries with ValueError
- [ ] T017 [US1] Add query length handling: truncate queries >32000 characters (~8000 tokens) with warning in response
- [ ] T018 [US1] Add timing measurement in `search()` to populate query_time_ms field
- [ ] T019 [US1] Add JSON structured logging for search operations (query_length, result_count, latency_ms)

**Checkpoint**: User Story 1 complete - basic search works independently, returns ranked results with scores

---

## Phase 4: User Story 2 - Source Attribution & Metadata Verification (Priority: P1)

**Goal**: Each retrieved chunk includes complete source metadata for citations

**Independent Test**: Run any search and verify each result contains: source_url, title, section, chunk_position, chunk_text

### Implementation for User Story 2

- [ ] T020 [US2] Update `_search_qdrant()` to extract all payload fields from Qdrant results in backend/retrieve.py
- [ ] T021 [US2] Map Qdrant payload fields to SearchResult dataclass fields in backend/retrieve.py
- [ ] T022 [US2] Add metadata validation: warn if any result has missing/empty metadata fields in response.warnings

**Checkpoint**: User Story 2 complete - all results include complete, traceable metadata

---

## Phase 5: User Story 3 - Empty & Low-Confidence Result Handling (Priority: P1)

**Goal**: Gracefully handle queries with no results or low-confidence matches

**Independent Test**: Submit "best pizza recipe" query and verify empty results or all results below 0.5 threshold

### Implementation for User Story 3

- [ ] T023 [US3] Implement score threshold filtering in `_search_qdrant()` to exclude results below threshold in backend/retrieve.py
- [ ] T024 [US3] Handle empty collection case: return empty SearchResponse (not error) when collection has no vectors
- [ ] T025 [US3] Handle no-matches case: return empty results list with total_results=0 when no vectors meet threshold
- [ ] T026 [US3] Add connection error handling with clear messages for Qdrant unavailable (ConnectionError after 3 retries)
- [ ] T027 [US3] Add Cohere error handling with clear messages for embedding failures (ConnectionError after 3 retries)
- [ ] T028 [US3] Add timeout handling: TimeoutError after 10s for Qdrant, 30s for Cohere per spec PC-004/PC-005

**Checkpoint**: User Story 3 complete - edge cases handled gracefully without crashes

---

## Phase 6: User Story 4 - End-to-End Pipeline Validation (Priority: P2)

**Goal**: Run validation tests confirming entire pipeline works correctly

**Independent Test**: Run validation suite and verify it produces pass/fail report with vector count, metadata completeness, search accuracy

### Implementation for User Story 4

- [ ] T029 [US4] Implement async `get_collection_stats()` function in backend/retrieve.py returning CollectionStats
- [ ] T030 [US4] Define GOLDEN_TEST_SET constant in backend/retrieve.py with 5 test queries from spec (inverse kinematics, robot arm control, sensor fusion, motion planning, coordinate transforms)
- [ ] T031 [US4] Add negative test query "What is the best pizza recipe?" to validation set with expected empty/low-confidence results
- [ ] T032 [US4] Implement async `_check_metadata_completeness()` helper that samples vectors and calculates % with all required fields
- [ ] T033 [US4] Implement async `validate_pipeline()` function in backend/retrieve.py that runs golden test set
- [ ] T034 [US4] Implement validation logic: query passes if ANY top-5 result has source_url containing expected pattern AND score ≥0.6
- [ ] T035 [US4] Implement overall pass criteria: ≥4/5 queries pass (80%) AND negative test returns empty/low-confidence
- [ ] T036 [US4] Generate ValidationReport with: passed, total_queries, passed_queries, failed_queries, vector_count, metadata_completeness

**Checkpoint**: User Story 4 complete - validation suite confirms pipeline integrity

---

## Phase 7: User Story 5 - Configurable Search Parameters (Priority: P2)

**Goal**: Configure search parameters (result count, similarity threshold, filters) for different use cases

**Independent Test**: Run same query with different parameters and verify results change accordingly

### Implementation for User Story 5

- [ ] T037 [US5] Add `source_url_filter: str | None = None` parameter to `search()` function in backend/retrieve.py
- [ ] T038 [US5] Add `section_filter: str | None = None` parameter to `search()` function in backend/retrieve.py
- [ ] T039 [US5] Implement Qdrant Filter with MatchText for source_url prefix matching (e.g., "/docs/module1" matches all module1 URLs)
- [ ] T040 [US5] Implement Qdrant Filter with MatchValue for section exact matching
- [ ] T041 [US5] Implement combined filter (AND logic) when both source_url_filter and section_filter provided
- [ ] T042 [US5] Add parameter validation: limit must be 1-20, score_threshold must be 0.0-1.0

**Checkpoint**: User Story 5 complete - search is fully configurable for different RAG scenarios

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 Add module-level __all__ export list in backend/retrieve.py exposing: search, get_collection_stats, validate_pipeline
- [ ] T044 Add module-level __all__ export list in backend/models/__init__.py exposing all dataclasses
- [ ] T045 Update backend/models/response.py with proper type hints and docstrings
- [ ] T046 Update backend/models/query.py with proper type hints and docstrings
- [ ] T047 Verify all functions have async/await pattern for non-blocking I/O
- [ ] T048 Run quickstart.md validation scenarios manually to confirm API works as documented
- [ ] T049 [P] Validate SC-006: run 10 concurrent search() calls using asyncio.gather() and verify p95 latency ≤3s with no errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1, US2, US3 (P1 stories) can proceed in parallel or sequentially
  - US4, US5 (P2 stories) can proceed after P1 stories or in parallel with them
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - Builds on US1's search function
- **User Story 3 (P1)**: Can start after Foundational - Extends US1's error handling
- **User Story 4 (P2)**: Requires US1 search function to be working (for golden test queries)
- **User Story 5 (P2)**: Can start after Foundational - Extends US1's search parameters

### Within Each User Story

- Models/dataclasses before functions using them
- Helper functions before main functions
- Core implementation before integration
- Logging after core functionality works

### Parallel Opportunities

- T002, T003, T004 can run in parallel (different files)
- T005, T006, T007, T008, T009 can run in parallel (different dataclasses in same/related files)
- T010, T011, T012 can run in parallel (different helper functions)
- User stories US1, US2, US3 can run in parallel after Foundational phase

---

## Parallel Example: Foundational Phase

```bash
# Launch all dataclass definitions together:
Task: "Create SearchResult dataclass in backend/models/response.py"
Task: "Create SearchResponse dataclass in backend/models/response.py"
Task: "Create CollectionStats dataclass in backend/models/response.py"
Task: "Create ValidationReport dataclass in backend/models/response.py"
Task: "Create GoldenTestQuery dataclass in backend/models/query.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Basic Search)
4. Complete Phase 4: User Story 2 (Metadata)
5. Complete Phase 5: User Story 3 (Error Handling)
6. **STOP and VALIDATE**: Test basic search works with proper metadata and error handling
7. Deploy/demo if ready - RAG chatbot can now use retrieval

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Basic search works (MVP!)
3. Add User Story 2 → Test independently → Metadata attribution works
4. Add User Story 3 → Test independently → Error handling robust
5. Add User Story 4 → Test independently → Validation suite confirms quality
6. Add User Story 5 → Test independently → Configurable for different use cases
7. Each story adds value without breaking previous stories

---

## Success Criteria Mapping

| Task | Success Criteria |
|------|------------------|
| T015, T018 | SC-001: Search returns in <2s p95 |
| T033-T036 | SC-002: 80% relevance on golden test set |
| T020-T022 | SC-003: 100% metadata completeness |
| T023-T025 | SC-004: Empty results for out-of-domain queries |
| T029, T032 | SC-005: Vector count matches expected chunks |
| T015 (async) | SC-006: 10 concurrent requests handled |
| T013 | SC-007: Embedding generation <500ms |
| T026-T028 | SC-008: Graceful error handling |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Extends existing backend/ structure from 003-embedding-pipeline
