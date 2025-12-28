# Tasks: Embedding Pipeline Setup

**Input**: Design documents from `/specs/003-embedding-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required)

**Tests**: Tests are OPTIONAL for this feature - none explicitly requested in spec.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single-file project**: `backend/main.py` (all pipeline code)
- **Tests**: `backend/tests/test_main.py`
- **Config**: `backend/pyproject.toml`, `backend/.env.example`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: UV project initialization and environment configuration

- [x] T001 Create `backend/` directory structure per plan.md
- [x] T002 Initialize UV project with `uv init` in `backend/`
- [x] T003 [P] Create `backend/.python-version` with Python 3.11 specification
- [x] T004 [P] Add production dependencies via `uv add cohere qdrant-client httpx beautifulsoup4 lxml python-dotenv`
- [x] T005 [P] Add dev dependencies via `uv add --dev pytest pytest-asyncio`
- [x] T006 Run `uv sync` to create virtual environment and lock file
- [x] T007 [P] Create `backend/.env.example` with COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY placeholders
- [x] T008 [P] Add `backend/.env` to `.gitignore` if not already present

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 Create empty `backend/main.py` with module docstring and imports skeleton
- [x] T010 Implement environment validation in `backend/main.py` - fail-fast check for COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY
- [x] T011 Implement `log(entry: dict)` JSON structured logging helper in `backend/main.py`
- [x] T012 Implement Cohere client initialization in `backend/main.py` with error handling
- [x] T013 Implement Qdrant client initialization in `backend/main.py` with error handling

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Initial Document Ingestion (Priority: P1) 🎯 MVP

**Goal**: Run the embedding pipeline against the deployed Docusaurus book so all book content becomes searchable via vector similarity

**Independent Test**: Run the pipeline once against live book URLs and verify vectors appear in Qdrant with correct metadata

### Implementation for User Story 1

- [x] T014 [US1] Implement `get_all_urls(base_url: str) -> list[str]` in `backend/main.py`:
  - Primary: Parse sitemap.xml for /docs/** URLs
  - Fallback: Return 13 hardcoded documentation URLs
  - Filter out /search, /tags/*, /blog/*
  - Deduplicate results
- [x] T015 [US1] Implement `extract_text_from_url(url: str) -> tuple[str, str, str]` in `backend/main.py`:
  - Fetch HTML with 30s timeout via httpx
  - Parse with BeautifulSoup + lxml
  - Extract title from <title> or <h1>
  - Extract section from URL path
  - Select content using Docusaurus selectors (article.markdown, main[class*="docMainContainer"], etc.)
  - Skip pages with < 100 chars extracted
  - Return (title, section, text)
- [x] T016 [US1] Implement `chunk_text(text: str, source_url: str) -> list[dict]` in `backend/main.py`:
  - Target chunk size: 1400 chars (~350 tokens)
  - Overlap: 240 chars (~60 tokens)
  - Markdown-aware separators: \n## , \n### , \n#### , \n\n, \n, space
  - Generate deterministic ID: SHA-256(source_url + position)[:32]
  - Return list of dicts with id, text, position
- [x] T017 [US1] Implement `embed(texts: list[str], cohere_client) -> list[list[float]]` in `backend/main.py`:
  - Batch size: 96 texts max per API call
  - Model: embed-english-v3.0
  - input_type: search_document
  - Retry with exponential backoff (1s, 2s, 4s) on failure
  - Return list of 1024-dim vectors
- [x] T018 [US1] Implement `create_collection(qdrant_client, collection_name: str)` in `backend/main.py`:
  - Check if collection exists, skip if so (idempotent)
  - Create with 1024 dimensions, Cosine distance
  - HNSW config: m=16, ef_construct=100
- [x] T019 [US1] Implement `save_chunk_to_qdrant(qdrant_client, chunks, embeddings, metadata, collection_name)` in `backend/main.py`:
  - Build PointStruct for each chunk with payload
  - Use upsert for idempotency
  - Return count of points upserted
- [x] T020 [US1] Implement `main()` orchestration in `backend/main.py`:
  - Load environment variables
  - Initialize clients
  - Create collection
  - Discover URLs
  - Process each URL (extract → chunk → embed → store)
  - Track basic stats (urls processed)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Running `uv run python main.py` should ingest all book content to Qdrant.

---

## Phase 4: User Story 2 - Idempotent Re-runs (Priority: P1)

**Goal**: Re-run the pipeline without creating duplicate vectors so updates can be safely applied when book content changes

**Independent Test**: Run the pipeline twice consecutively and verify the vector count remains stable (no duplicates)

### Implementation for User Story 2

- [x] T021 [US2] Add content_hash computation to `extract_text_from_url()` in `backend/main.py`:
  - Compute SHA-256 of extracted text
  - Return as 4th tuple element: (title, section, text, content_hash)
- [x] T022 [US2] Update `save_chunk_to_qdrant()` in `backend/main.py` to include content_hash in payload
- [x] T023 [US2] Implement document-level change detection in `main()` in `backend/main.py`:
  - Before processing a URL, query Qdrant for existing chunks with that source_url
  - If content_hash matches stored hash, skip re-embedding (early exit)
  - Log skipped documents as "unchanged"
- [x] T024 [US2] Update stats tracking in `main()` to count skipped (unchanged) documents

**Checkpoint**: At this point, User Stories 1 AND 2 should both work. Re-running on unchanged content produces zero new embedding API calls.

---

## Phase 5: User Story 3 - Pipeline Execution Report (Priority: P2)

**Goal**: See a summary report after pipeline execution for verification and troubleshooting

**Independent Test**: Run the pipeline and verify a structured report is produced with expected metrics

### Implementation for User Story 3

- [x] T025 [US3] Enhance stats dictionary in `main()` in `backend/main.py`:
  - Track: urls_processed, urls_skipped (unchanged), urls_failed
  - Track: chunks_created, embeddings_generated, vectors_stored
  - Track: start_time, end_time, duration_seconds
  - Track: failed_urls list with error reasons
- [x] T026 [US3] Add per-document logging in `main()` in `backend/main.py`:
  - Log each URL processed with chunk count
  - Log skipped URLs (unchanged content)
  - Log failed URLs with error message
- [x] T027 [US3] Implement execution report output in `main()` in `backend/main.py`:
  - Print formatted report header
  - Output full stats as JSON
  - Include failed_urls list with error details

**Checkpoint**: Pipeline now produces comprehensive execution reports

---

## Phase 6: User Story 4 - Source Metadata Preservation (Priority: P2)

**Goal**: Each vector includes source metadata so answers can be attributed to specific book sections

**Independent Test**: Query Qdrant for any vector and verify it contains expected metadata fields

### Implementation for User Story 4

- [x] T028 [US4] Verify `save_chunk_to_qdrant()` payload includes all required metadata in `backend/main.py`:
  - source_url (string, valid URL)
  - title (string, non-empty)
  - section (string, extracted from URL path)
  - chunk_position (int, >= 0)
  - chunk_text (string, the chunk content)
  - content_hash (64-char hex string)
- [x] T029 [US4] Implement `extract_section_from_url(url: str) -> str` helper in `backend/main.py`:
  - Parse URL path to extract module/chapter info
  - E.g., "module1-ros2-fundamentals" from /docs/module1-ros2-fundamentals/chapter1-ros2-basics

**Checkpoint**: All vectors now have complete, queryable metadata for RAG attribution

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validation, cleanup, and operational readiness

- [x] T030 [P] Add `if __name__ == "__main__": main()` guard in `backend/main.py`
- [x] T031 [P] Add comprehensive type hints to all functions in `backend/main.py`
- [ ] T032 Run manual validation: execute pipeline against live Docusaurus site
- [ ] T033 Verify Qdrant collection has expected vector count (100-500 chunks)
- [ ] T034 Run sample search query to verify retrieval quality (similarity > 0.7)
- [x] T035 [P] Verify `.env.example` documents all required environment variables

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion - delivers MVP
- **User Story 2 (Phase 4)**: Depends on US1 (adds idempotency to existing pipeline)
- **User Story 3 (Phase 5)**: Can start after Foundational - enhances reporting
- **User Story 4 (Phase 6)**: Can start after Foundational - enhances metadata
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Core pipeline - no dependencies on other stories
- **User Story 2 (P1)**: Adds change detection to US1 - depends on US1 for base pipeline
- **User Story 3 (P2)**: Adds reporting - depends on US1 for base pipeline, independent of US2
- **User Story 4 (P2)**: Adds metadata - depends on US1 for base pipeline, independent of US2/US3

### Within Each User Story

- Foundation MUST complete before any story implementation
- Functions are implemented in dependency order (helpers before orchestration)
- `main()` is updated last in each story phase

### Parallel Opportunities

- T003, T004, T005 can run in parallel (Setup phase)
- T007, T008 can run in parallel (env file setup)
- T030, T031, T035 can run in parallel (Polish phase)
- US3 and US4 can run in parallel (both P2, independent of each other)

---

## Parallel Example: Setup Phase

```bash
# After T001 creates directory and T002 initializes UV:
Task: "Create backend/.python-version with Python 3.11 specification" [T003]
Task: "Add production dependencies via uv add" [T004]
Task: "Add dev dependencies via uv add" [T005]
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T008)
2. Complete Phase 2: Foundational (T009-T013)
3. Complete Phase 3: User Story 1 (T014-T020)
4. **STOP and VALIDATE**: Test by running `uv run python main.py`
5. Verify vectors appear in Qdrant Cloud dashboard

### Full Feature (All Stories)

1. Complete Setup + Foundational → Foundation ready
2. Complete User Story 1 → Verify basic ingestion works
3. Complete User Story 2 → Verify idempotent re-runs
4. Complete User Story 3 → Verify execution report
5. Complete User Story 4 → Verify metadata in vectors
6. Complete Polish → Production ready

### Suggested Single-Developer Order

Since this is a single-file project:
1. T001 → T008 (Setup)
2. T009 → T013 (Foundation)
3. T014 → T020 (US1 - MVP)
4. T021 → T024 (US2 - Idempotency)
5. T025 → T027 (US3 - Reporting)
6. T028 → T029 (US4 - Metadata)
7. T030 → T035 (Polish)

---

## Notes

- All code goes in single file: `backend/main.py`
- [P] tasks can run in parallel when marked
- [Story] labels map tasks to user stories for traceability
- User Story 1 is a complete MVP - stop there if time constrained
- Each user story adds value without breaking previous stories
- Commit after each task or logical group
- Expected total: ~35 tasks, ~100-500 vectors stored
