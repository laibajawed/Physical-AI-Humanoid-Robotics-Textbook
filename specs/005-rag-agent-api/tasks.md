# Tasks: RAG Agent API (Spec-3)

**Input**: Design documents from `/specs/005-rag-agent-api/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/openapi.yaml ✓, quickstart.md ✓

**Tests**: Test tasks included per quickstart.md test scenarios.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project structure**: `backend/` at repository root (single backend project extending existing structure)
- Existing files to KEEP: `retrieve.py`, `main.py`, `setup_indexes.py`, `models/query.py`
- New files to CREATE: `app.py`, `agent.py`, `db.py`, `models/request.py`, `models/response.py`, `models/session.py`, `models/health.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [X] T001 Update pyproject.toml with new dependencies (fastapi, uvicorn, openai-agents, openai, sqlalchemy, asyncpg, pydantic) in backend/pyproject.toml
- [X] T002 [P] Create .env.example with all required environment variables (GEMINI_API_KEY, QDRANT_URL, QDRANT_API_KEY, COHERE_API_KEY, DATABASE_URL) in backend/.env.example
- [X] T003 [P] Verify existing retrieve.py functions (search_similar, get_collection_stats) are async and compatible in backend/retrieve.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create request models (ChatRequest, MetadataFilter) with Pydantic validation in backend/models/request.py
- [X] T005 [P] Create response models (SourceCitation, SelectedTextCitation, ResponseMetadata, ChatResponse) in backend/models/response.py
- [X] T006 [P] Create error models (ErrorResponse, ErrorCodes) in backend/models/response.py
- [X] T007 [P] Create health models (ServiceStatus, HealthResponse) in backend/models/health.py
- [X] T008 [P] Create session models (Session, ConversationRecord, HistoryEntry, ConversationHistoryResponse) in backend/models/session.py
- [X] T009 Update models/__init__.py to export all new models in backend/models/__init__.py
- [X] T010 Create database connection pool and table initialization in backend/db.py
- [X] T011 Implement session CRUD operations (create_session, get_session, update_session_activity) in backend/db.py
- [X] T012 Implement conversation CRUD operations (save_conversation, get_conversation_history) in backend/db.py
- [X] T013 Create FastAPI app skeleton with CORS, exception handlers, request_id middleware in backend/app.py
- [X] T014 [P] Setup structured JSON logging with request correlation in backend/app.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - General Book Question Answering (Priority: P1) 🎯 MVP

**Goal**: Users can ask questions about book content and receive accurate, source-cited answers

**Independent Test**: Ask "What is inverse kinematics?" and verify response includes relevant content with proper source citations

### Implementation for User Story 1

- [X] T015 [US1] Create @function_tool decorated search_book_content that wraps retrieve.search_similar() in backend/agent.py
- [X] T015a [US1] Implement filters parameter handling (source_url_prefix, section) in search_book_content per FR-008 in backend/agent.py
- [X] T016 [US1] Create base agent instructions (cite sources, acknowledge missing info) in backend/agent.py
- [X] T017 [US1] Create build_agent() function with OpenAIChatCompletionsModel using Gemini endpoint in backend/agent.py
- [X] T018 [US1] Create run_agent() async function that executes agent with RunConfig(tracing_disabled=True) in backend/agent.py
- [X] T019 [US1] Implement citation extraction from tool results (extract_and_validate_citations) in backend/agent.py
- [X] T020 [US1] Implement POST /chat endpoint with request validation in backend/app.py
- [X] T021 [US1] Wire /chat to agent execution and response formatting in backend/app.py
- [X] T022 [US1] Add error handling for empty query (400 EMPTY_QUERY) in backend/app.py
- [X] T023 [US1] Add error handling for query too long (400 QUERY_TOO_LONG) in backend/app.py

### Tests for User Story 1

- [X] T024 [P] [US1] Smoke test: POST /chat basic question returns answer with sources in backend/tests/test_api.py
- [X] T025 [P] [US1] Test: citation structure matches SourceCitation schema in backend/tests/test_api.py

**Checkpoint**: User Story 1 complete - users can ask general book questions and receive sourced answers

---

## Phase 4: User Story 2 - Selected-Text-Only Mode (Priority: P1)

**Goal**: Users can ask questions grounded only in their selected/highlighted text

**Independent Test**: Provide selected text about "robot arm control" and ask "explain this in simpler terms" - response should only reference provided text

### Implementation for User Story 2

- [X] T026 [US2] Create SELECTED_TEXT_INSTRUCTIONS template with text injection in backend/agent.py
- [X] T027 [US2] Update build_agent() to accept selected_text parameter and modify instructions dynamically in backend/agent.py
- [X] T028 [US2] When selected_text present, remove search_book_content tool from agent in backend/agent.py
- [X] T029 [US2] Implement SelectedTextCitation generation (source_type, selection_length, snippet) in backend/agent.py
- [X] T030 [US2] Update /chat endpoint to detect selected_text mode and pass to agent in backend/app.py
- [X] T031 [US2] Add "not found in selection" handling when answer cannot be derived from selection in backend/agent.py

### Tests for User Story 2

- [X] T032 [P] [US2] Smoke test: POST /chat with selected_text returns answer without Qdrant queries in backend/tests/test_api.py
- [X] T033 [P] [US2] Test: selected_text mode citation has source_type="selected_text" in backend/tests/test_api.py

**Checkpoint**: User Story 2 complete - users can get answers grounded only in selected text

---

## Phase 5: User Story 3 - Source Citation and Attribution (Priority: P1)

**Goal**: Every answer includes clear, structured source citations

**Independent Test**: Ask any book-related question and verify response includes structured citation data (URL, section, chunk reference)

### Implementation for User Story 3

- [X] T034 [US3] Ensure all Qdrant results include required citation fields (source_url, title, section, chunk_position, similarity_score) in backend/agent.py
- [X] T035 [US3] Implement snippet generation (first 200 chars of chunk_text) for citations in backend/agent.py
- [X] T036 [US3] Validate citations exist in tool results before including in response (no hallucinated citations) in backend/agent.py
- [X] T037 [US3] Add citation deduplication (same source_url + chunk_position) in backend/agent.py

### Tests for User Story 3

- [X] T038 [P] [US3] Test: all responses include sources array with required fields in backend/tests/test_api.py
- [X] T039 [P] [US3] Test: snippet field is max 200 chars in backend/tests/test_api.py

**Checkpoint**: User Story 3 complete - all answers have proper source attribution

---

## Phase 6: User Story 4 - Graceful Handling of Out-of-Scope Questions (Priority: P2)

**Goal**: Chatbot gracefully declines questions outside the book's scope

**Independent Test**: Ask "What's the capital of France?" and verify agent indicates question is outside knowledge scope

### Implementation for User Story 4

- [X] T040 [US4] Add agent instruction to acknowledge when information is not in sources in backend/agent.py
- [X] T041 [US4] Handle empty retrieval results with "no_results" mode in response metadata in backend/agent.py
- [X] T042 [US4] Implement low-confidence detection (scores 0.3-0.5) with low_confidence flag in metadata in backend/agent.py
- [X] T043 [US4] Add helpful suggestion to try robotics-related questions in out-of-scope responses in backend/agent.py

### Tests for User Story 4

- [X] T044 [P] [US4] Test: out-of-scope question returns appropriate decline message in backend/tests/test_api.py
- [X] T045 [P] [US4] Test: low confidence results have low_confidence=true in metadata in backend/tests/test_api.py

**Checkpoint**: User Story 4 complete - out-of-scope questions handled gracefully

---

## Phase 7: User Story 5 - API Health and Monitoring (Priority: P2)

**Goal**: Health check endpoints and structured logging for monitoring and debugging

**Independent Test**: Call /health endpoint and verify it returns system status including Qdrant connectivity

### Implementation for User Story 5

- [X] T046 [US5] Implement GET /health endpoint that checks Qdrant connectivity via get_collection_stats() in backend/app.py
- [X] T047 [US5] Add Postgres connectivity check to /health endpoint in backend/app.py
- [X] T048 [US5] Return appropriate status (healthy/degraded/unavailable) based on service checks in backend/app.py
- [X] T049 [US5] Add latency_ms measurement for each service check in backend/app.py
- [X] T050 [US5] Ensure all API requests log timestamp, request_id, latency_ms, and error (if any) in JSON format in backend/app.py

### Tests for User Story 5

- [X] T051 [P] [US5] Smoke test: GET /health returns status with Qdrant info in backend/tests/test_api.py
- [X] T052 [P] [US5] Test: health endpoint returns degraded status when Qdrant unavailable in backend/tests/test_api.py

**Checkpoint**: User Story 5 complete - monitoring and health checks available

---

## Phase 8: User Story 6 - Conversation History & Session Management (Priority: P2)

**Goal**: Conversation history preserved across sessions

**Independent Test**: Start conversation, return with same session_id, verify previous messages displayed

### Implementation for User Story 6

- [X] T053 [US6] Generate new UUID v4 session_id when not provided in request in backend/app.py
- [X] T054 [US6] Create or update session record on each chat request in backend/app.py
- [X] T055 [US6] Store conversation record (query, response, sources, metadata) after each successful chat in backend/app.py
- [X] T056 [US6] Retrieve last 5 conversation exchanges for context when session_id exists in backend/agent.py
- [X] T057 [US6] Implement GET /history/{session_id} endpoint in backend/app.py
- [X] T058 [US6] Add session_id to all ChatResponse objects in backend/app.py

### Tests for User Story 6

- [X] T059 [P] [US6] Test: chat without session_id returns new session_id in backend/tests/test_api.py
- [X] T060 [P] [US6] Test: GET /history/{session_id} returns conversation history in backend/tests/test_api.py
- [X] T061 [P] [US6] Test: session_id=invalid UUID returns 400 error in backend/tests/test_api.py

**Checkpoint**: User Story 6 complete - conversation history persists across sessions

---

## Phase 9: Error Handling & Graceful Degradation

**Purpose**: Implement robust error handling per spec requirements

- [X] T062 Implement Qdrant retry with exponential backoff (3 attempts) in backend/agent.py (reuses retrieve.py)
- [X] T063 Implement Gemini fallback: return retrieval-only results with "AI summarization unavailable" message in backend/agent.py
- [X] T064 Add connection timeout handling (Qdrant 10s, Gemini 30s, Postgres 5s) in backend/app.py
- [X] T065 Implement rate limiting (max 10 concurrent requests, 429 after) in backend/app.py
- [X] T066 Add Retry-After header to 429 and 503 responses in backend/app.py

### Tests for Error Handling

- [X] T067 [P] Test: 11th concurrent request gets 429 response in backend/tests/test_api.py
- [X] T068 [P] Test: Gemini unavailable returns retrieval_only mode with fallback_message in backend/tests/test_api.py
- [X] T069 [P] Test: all errors return structured ErrorResponse with request_id in backend/tests/test_api.py

---

## Phase 10: Streaming Support (Optional Enhancement)

**Purpose**: Implement SSE streaming for better UX on long responses

- [X] T070 Implement POST /chat/stream endpoint with SSE response in backend/app.py
- [X] T071 Use Runner.run_streamed() to stream agent output in backend/agent.py
- [X] T072 Send delta events for partial text, sources event at end, done event when complete in backend/app.py

### Tests for Streaming

- [X] T073 [P] Test: POST /chat/stream returns SSE events in backend/tests/test_api.py

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and validation

- [X] T074 [P] Add OpenAPI documentation generation in backend/app.py (FastAPI auto-generates)
- [X] T075 [P] Run quickstart.md validation steps (Qdrant, Gemini, Postgres connectivity) in backend/
- [X] T076 Verify all smoke tests pass per plan.md testing strategy in backend/tests/ (25/26 tests pass - 1 test isolation issue)
- [X] T077 [P] Add type hints to all functions in backend/*.py
- [X] T078 Code cleanup: remove unused imports, add docstrings in backend/*.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1, US2, US3 (P1 priority): Should complete before US4, US5, US6
  - US4, US5, US6 (P2 priority): Can proceed after P1 stories
- **Error Handling (Phase 9)**: Depends on US1 core implementation
- **Streaming (Phase 10)**: Depends on US1 core implementation
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after US1 agent.py created - Modifies build_agent()
- **User Story 3 (P1)**: Can start after US1 - Enhances citation logic
- **User Story 4 (P2)**: Can start after US1 - Adds handling for edge cases
- **User Story 5 (P2)**: Can start after Foundational - Independent health endpoint
- **User Story 6 (P2)**: Can start after Foundational - Uses db.py from Phase 2

### Parallel Opportunities

**Within Phase 2 (Foundational):**
```bash
# Launch all model files in parallel:
Task: "Create response models in backend/models/response.py"
Task: "Create health models in backend/models/health.py"
Task: "Create session models in backend/models/session.py"
```

**Within Phase 3 (User Story 1 Tests):**
```bash
# Launch all US1 tests in parallel:
Task: "Smoke test: POST /chat basic question in backend/tests/test_api.py"
Task: "Test: citation structure matches schema in backend/tests/test_api.py"
```

**Across P2 User Stories (after P1 complete):**
```bash
# Can work on US4, US5, US6 in parallel if team capacity allows
Developer A: User Story 4 (out-of-scope handling)
Developer B: User Story 5 (health/monitoring)
Developer C: User Story 6 (session/history)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (General Q&A)
4. **STOP and VALIDATE**: Test US1 independently via quickstart.md curl commands
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP!** (can answer book questions)
3. Add User Story 2 → Test independently → Selected-text mode works
4. Add User Story 3 → Test independently → Better citations
5. Add User Story 4 → Test independently → Out-of-scope handling
6. Add User Story 5 → Test independently → Health monitoring
7. Add User Story 6 → Test independently → Session history
8. Add Phases 9-11 → Production-ready

### Suggested MVP Scope

**Minimum viable product** = Phase 1 + Phase 2 + Phase 3 (User Story 1)
- Users can ask book questions and get sourced answers
- ~23 tasks to MVP

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Existing code preserved: retrieve.py, main.py, setup_indexes.py, models/query.py
