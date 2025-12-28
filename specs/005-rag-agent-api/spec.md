# Feature Specification: RAG Agent API

**Feature Branch**: `005-rag-agent-api`
**Created**: 2025-12-16
**Status**: Draft
**Input**: User description: "Build a FastAPI backend that hosts an OpenAI Agents SDK agent which answers questions about the book by retrieving relevant chunks from Qdrant and grounding responses in those sources."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - General Book Question Answering (Priority: P1)

As a student or educator using the Physical AI & Humanoid Robotics textbook chatbot, I want to ask questions about the book content and receive accurate, source-cited answers so that I can quickly find relevant information without reading entire chapters.

**Why this priority**: This is the core RAG functionality. Without accurate question-answering grounded in source content, the entire system has no value. This validates that the agent properly retrieves context and generates relevant responses.

**Independent Test**: Can be fully tested by asking a question like "What is inverse kinematics?" and verifying the response includes relevant content from the book with proper source citations.

**Acceptance Scenarios**:

1. **Given** the Qdrant collection contains book content embeddings, **When** I submit a question about robotics concepts, **Then** I receive an answer that accurately reflects the book content.
2. **Given** I ask a question covered in the book, **When** the agent responds, **Then** the response includes source citations (chapter/section references with URLs).
3. **Given** a well-formed question, **When** I submit it via the API, **Then** I receive a complete response within 3 seconds.

---

### User Story 2 - Selected-Text-Only Mode (Priority: P1)

As a student reading a specific section of the book, I want to ask questions about only my selected/highlighted text so that I get answers grounded strictly in that context rather than the entire book.

**Why this priority**: This is a differentiating feature that supports focused learning. Students often need clarification on specific passages without interference from other sections.

**Independent Test**: Can be tested by providing selected text about "robot arm control" and asking "explain this in simpler terms" - the response should only reference the provided text, not the entire book.

**Acceptance Scenarios**:

1. **Given** I provide selected text along with my question, **When** the agent processes the query, **Then** the response is grounded only in the provided selection.
2. **Given** I ask something not covered in my selected text, **When** the agent responds, **Then** it explicitly states "not found in selection" or similar message.
3. **Given** selected-text mode is active, **When** I receive a response, **Then** citations reference the provided selection rather than general book chapters.

---

### User Story 3 - Source Citation and Attribution (Priority: P1)

As an educator or researcher, I want every answer to include clear source citations so that I can verify information and direct students to relevant book sections.

**Why this priority**: Trustworthy RAG requires source attribution. Without citations, users cannot verify answers or explore topics further in the source material.

**Independent Test**: Can be tested by asking any book-related question and verifying the response includes structured citation data (URL, section, chunk reference).

**Acceptance Scenarios**:

1. **Given** the agent retrieves chunks from Qdrant, **When** it generates a response, **Then** each relevant source chunk is cited with source_url, title, and section.
2. **Given** a response uses information from multiple chunks, **When** displayed, **Then** all contributing sources are listed.
3. **Given** a source citation includes a URL, **When** I follow that URL, **Then** I reach the relevant book section.

---

### User Story 4 - Graceful Handling of Out-of-Scope Questions (Priority: P2)

As a user, I want the chatbot to gracefully decline questions outside the book's scope so that I don't receive hallucinated or inaccurate responses.

**Why this priority**: Prevents misinformation. The agent should be honest about its knowledge boundaries rather than guessing at answers not in the source material.

**Independent Test**: Can be tested by asking unrelated questions like "What's the capital of France?" and verifying the agent indicates the question is outside its knowledge scope.

**Acceptance Scenarios**:

1. **Given** I ask a question unrelated to robotics/book content, **When** no relevant chunks are retrieved, **Then** the agent responds indicating it cannot answer based on available sources.
2. **Given** retrieved chunks have low similarity scores (below threshold), **When** the agent responds, **Then** it indicates low confidence or lack of relevant information.
3. **Given** an out-of-scope question, **When** the agent declines, **Then** it suggests the user try a robotics-related question.

---

### User Story 5 - API Health and Monitoring (Priority: P2)

As a backend developer, I want health check endpoints and structured logging so that I can monitor system status and debug issues in production.

**Why this priority**: Operational reliability. Production systems need observability for debugging and monitoring service health.

**Independent Test**: Can be tested by calling the health endpoint and verifying it returns system status including Qdrant connectivity.

**Acceptance Scenarios**:

1. **Given** the server is running, **When** I call /health, **Then** I receive status information including Qdrant connection status.
2. **Given** any API request is processed, **When** logged, **Then** logs include timestamp, request_id, latency_ms, and error (if any) in JSON format.
3. **Given** Qdrant is unavailable, **When** I call /health, **Then** the health check indicates degraded status.

---

### User Story 6 - Conversation History & Session Management (Priority: P2)

As a returning user, I want my conversation history to be preserved across sessions so that I can continue previous discussions and reference past answers.

**Why this priority**: Enhances user experience by providing continuity. Users can build on previous questions without re-establishing context.

**Independent Test**: Can be tested by starting a conversation, closing the browser, returning, and verifying previous messages are displayed.

**Acceptance Scenarios**:

1. **Given** I have an anonymous session ID (client-generated), **When** I send a message, **Then** the conversation is stored in Neon Postgres with my session_id.
2. **Given** I return with the same session_id, **When** I load the chat, **Then** I see my previous conversation history.
3. **Given** conversation history exists, **When** the agent processes a new query, **Then** it has access to recent conversation context for continuity.

---

### Edge Cases

- What happens when the query text is empty or whitespace only?
  - System returns a 400 error with message "Query cannot be empty"

- What happens when Qdrant Cloud is temporarily unavailable?
  - System returns a 503 error with message "Vector database unavailable" and implements retry with exponential backoff (3 attempts)

- What happens when the Gemini API fails or is rate-limited after retry attempts exhausted?
  - System returns retrieval results only with message "AI summarization unavailable" (graceful degradation)

- What happens when retrieved chunks have no relevant content?
  - Agent responds with "I couldn't find relevant information in the book to answer this question"

- What happens when retrieved chunks have similarity scores between 0.3 and 0.5?
  - Include low-confidence results with a `low_confidence: true` warning flag in response metadata

- What happens when selected text is provided but is too short to be meaningful?
  - System processes the request but may indicate insufficient context for a complete answer

- What happens when the question and selected text are in different languages?
  - System processes in English; non-English content may receive degraded response quality

- What happens with extremely long queries (>8000 tokens)?
  - Query is truncated to model limits with a warning in the response metadata

- What happens when more than 10 concurrent requests arrive?
  - System returns 429 Too Many Requests with retry-after header (hard limit)

- What happens when session_id is missing or invalid?
  - System creates a new anonymous session and returns the new session_id in response

## Requirements *(mandatory)*

### Functional Requirements

**Agent Configuration**

- **FR-001**: System MUST implement a single agent file (`agent.py`) containing the RAG retrieval agent with Qdrant query capability
- **FR-002**: System MUST use OpenAI Agents SDK with Gemini API via OpenAI-compatible endpoint (`https://generativelanguage.googleapis.com/v1beta/openai/`)
- **FR-003**: System MUST configure the agent model using `OpenAIChatCompletionsModel` with:
  - `model="gemini-2.0-flash"`
  - `openai_client=AsyncOpenAI(api_key=GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")`
- **FR-004**: System MUST configure `RunConfig` with `tracing_disabled=True` for privacy
- **FR-005**: System MUST load `GEMINI_API_KEY` from environment variables via `python-dotenv`

**Retrieval Tool**

- **FR-006**: System MUST implement a `@function_tool` decorated retrieval function with the following signature:
  ```python
  @function_tool
  async def search_book_content(
      query: str,
      limit: int = 5,
      score_threshold: float = 0.5
  ) -> str:
      """Search the Physical AI & Robotics book for relevant content.

      Args:
          query: Natural language search query
          limit: Maximum results to return (1-10)
          score_threshold: Minimum similarity score (0.0-1.0)

      Returns:
          JSON string with retrieved chunks and metadata
      """
  ```
- **FR-006a**: The retrieval function MUST return a JSON string in this format:
  ```json
  {
    "results": [
      {
        "chunk_text": "...",
        "source_url": "...",
        "title": "...",
        "section": "...",
        "similarity_score": 0.85,
        "chunk_position": 1
      }
    ],
    "total_results": 5,
    "message": "Found 5 relevant passages"
  }
  ```
- **FR-007**: Retrieval tool MUST accept query text and return top-k results (default k=5, configurable 1-10)
- **FR-008**: Retrieval tool MUST support optional metadata filters (source_url prefix, section name)
- **FR-009**: Retrieval tool MUST return structured results with: similarity_score, chunk_text, source_url, title, section, chunk_position
- **FR-010**: Retrieval tool MUST use the existing Qdrant collection (`rag_embedding`) and retrieval functions from retrieve.py
- **FR-010a**: System MUST generate query embeddings using Cohere `embed-english-v3.0` model with `input_type="search_query"` to match stored vectors (1024 dimensions)
- **FR-010b**: System MUST NOT use Gemini for query embedding generation; Gemini is used only for response generation via the agent
- **FR-010c**: When similarity scores fall between 0.3-0.5, results MUST be included with `low_confidence: true` flag in metadata

**API Endpoints**

- **FR-011**: System MUST expose POST `/chat` endpoint accepting JSON with `query` (required), `selected_text` (optional), and `session_id` (optional) fields
- **FR-012**: System MUST return JSON response with `answer`, `sources` (array of citation objects), `metadata` (query_time, retrieval_count), and `session_id`
- **FR-013**: System MUST expose GET `/health` endpoint returning system status, Qdrant connectivity, and Neon Postgres connectivity
- **FR-014**: System SHOULD support streaming responses via `/chat/stream` endpoint using Server-Sent Events (SSE)
- **FR-014a**: System MUST expose GET `/history/{session_id}` endpoint to retrieve conversation history
- **FR-014b**: System MUST return 429 Too Many Requests with `retry-after` header when concurrent request limit (10) is exceeded

**Selected-Text Mode**

- **FR-015**: When `selected_text` is provided, System MUST restrict agent grounding to that text only
- **FR-015a**: In selected-text mode, the agent instructions MUST be augmented to include:
  - The selected_text injected as context with clear delimiters
  - Explicit instruction to answer ONLY from the provided selection
  - Instruction NOT to use the search_book_content tool when selected_text is present
- **FR-016**: In selected-text mode, System MUST NOT query Qdrant for additional context (enforced via conditional agent instructions)
- **FR-017**: In selected-text mode, if answer cannot be found in selection, System MUST respond with explicit "not found in selection" message
- **FR-018**: Citations in selected-text mode MUST reference the provided text scope with first 200 chars as snippet

**Response Quality**

- **FR-019**: Agent instructions MUST direct it to always cite sources when answering
- **FR-020**: Agent instructions MUST direct it to acknowledge when information is not available in sources
- **FR-021**: Agent MUST not hallucinate information outside retrieved context
- **FR-022**: Response MUST include structured source citations parseable by frontend
- **FR-022a**: When Gemini is unavailable after retries, System MUST return retrieval results with message "AI summarization unavailable"

**Session & Conversation History**

- **FR-026**: System MUST accept optional `session_id` (UUID v4) in chat requests
- **FR-027**: If no session_id provided, System MUST generate a new UUID v4 session_id and return it
- **FR-028**: System MUST store conversation history in Neon Postgres `conversations` table
- **FR-029**: Conversation records MUST include: session_id, timestamp, query, response, sources (JSON), metadata
- **FR-030**: System MUST retrieve recent conversation context (last 5 exchanges) when processing queries with existing session_id
- **FR-031**: System MUST provide conversation history via GET `/history/{session_id}` endpoint

**Error Handling**

- **FR-023**: System MUST return appropriate HTTP status codes (400 for bad input, 429 for rate limit, 503 for service unavailable, 500 for internal errors)
- **FR-024**: System MUST implement retry with exponential backoff for transient Qdrant/Gemini failures (3 attempts)
- **FR-025**: System MUST log all errors with request context in JSON structured format
- **FR-025a**: All request_id values MUST be UUID v4 format

### Key Entities

- **ChatRequest**: User's input for conversation; attributes include query (required string), selected_text (optional string), session_id (optional UUID v4), filters (optional object with source_url_prefix, section)
- **ChatResponse**: Complete response to user; attributes include answer (string), sources (array of SourceCitation), metadata (object with query_time_ms, retrieval_count, mode, low_confidence), session_id (UUID v4)
- **SourceCitation**: Reference to source material; attributes include source_url, title, section, chunk_position, similarity_score, snippet (brief excerpt)
- **SelectedTextCitation**: Reference for selected-text mode; attributes include source_type, selection_length, snippet (first 200 chars), relevance_note
- **RetrievalResult**: Internal result from Qdrant query; attributes include similarity_score, chunk_text, and all metadata fields
- **ErrorResponse**: Structured error for API failures; attributes include error_code (string), message (string), request_id (UUID v4), details (optional object)
- **ConversationRecord**: Stored chat exchange; attributes include id (auto), session_id (UUID v4), timestamp (ISO 8601), query (string), response (string), sources (JSON), metadata (JSON)
- **Session**: User session tracking; attributes include session_id (UUID v4), created_at (timestamp), last_active (timestamp)

### Entity Schemas

**SourceCitation Schema** (JSON):
```json
{
  "source_url": "string (required) - Full URL to the book section",
  "title": "string (required) - Document/chapter title",
  "section": "string (required) - Section or heading name",
  "chunk_position": "integer (required) - Position of chunk within document",
  "similarity_score": "float (required) - Cosine similarity score 0.0-1.0",
  "snippet": "string (required) - First 200 chars of chunk_text for preview"
}
```

**Selected-Text Citation Schema** (JSON):
```json
{
  "source_type": "selected_text",
  "selection_length": "integer - Character count of provided selection",
  "snippet": "string - First 200 chars of selection for preview",
  "relevance_note": "string - How the selection relates to the answer"
}
```

**ErrorResponse Schema** (JSON):
```json
{
  "error_code": "string (required) - Machine-readable code (e.g., EMPTY_QUERY, SERVICE_UNAVAILABLE, RATE_LIMITED)",
  "message": "string (required) - Human-readable error description",
  "request_id": "string (required) - UUID v4 for request tracing",
  "details": "object (optional) - Additional context (e.g., retry_after_seconds)"
}
```

**ConversationRecord Schema** (Postgres):
```sql
CREATE TABLE conversations (
  id SERIAL PRIMARY KEY,
  session_id UUID NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  query TEXT NOT NULL,
  response TEXT NOT NULL,
  sources JSONB,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_session ON conversations(session_id);
CREATE INDEX idx_conversations_timestamp ON conversations(timestamp DESC);
```

**Session Schema** (Postgres):
```sql
CREATE TABLE sessions (
  session_id UUID PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_active TIMESTAMPTZ DEFAULT NOW()
);
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agent provides accurate answers for 90% of book-related questions (measured against test set of 10 questions with known answers)
- **SC-002**: Complete response (retrieval + generation) delivered within 3 seconds for 95% of queries
- **SC-003**: 100% of responses include source citations when answering from book content
- **SC-004**: Selected-text mode correctly restricts context in 100% of test cases (no leakage from general book content)
- **SC-005**: Out-of-scope questions receive appropriate "cannot answer" responses 95% of the time (no hallucination)
- **SC-006**: System handles 10 concurrent requests without errors; requests beyond 10 receive 429 response; p95 latency under load ≤ 5 seconds
- **SC-007**: Health endpoint correctly reports Qdrant and Neon Postgres connectivity status
- **SC-008**: All API errors return structured JSON with error code, message, and request_id (UUID v4)
- **SC-009**: Conversation history persists across sessions and is retrievable via `/history/{session_id}`
- **SC-010**: When Gemini unavailable, system returns retrieval-only results (graceful degradation)

## Constraints

### Input Constraints
- **IC-001**: Query text must be non-empty string, max 8000 tokens
- **IC-002**: Selected text (if provided) max 16000 tokens
- **IC-003**: Result limit (k) range: 1-10 (default: 5)
- **IC-004**: Similarity threshold: 0.5 default for high-confidence, 0.3-0.5 for low-confidence with warning
- **IC-005**: session_id must be valid UUID v4 format if provided

### Processing Constraints
- **PC-001**: Model: Gemini 2.0 Flash via OpenAI-compatible endpoint
- **PC-002**: SDK: OpenAI Agents SDK (`openai-agents` package)
- **PC-003**: Vector retrieval from existing retrieve.py module
- **PC-004**: Connection timeout: 10 seconds for Qdrant, 30 seconds for Gemini, 5 seconds for Neon Postgres
- **PC-005**: Max concurrent requests: 10 (hard limit with 429 response)

### Output Constraints
- **OC-001**: Response format: JSON with answer, sources array, metadata object, session_id
- **OC-002**: Each source citation must include source_url, title, section at minimum
- **OC-003**: Streaming responses use SSE format with `data:` prefix
- **OC-004**: All request_id and session_id values use UUID v4 format

### Operational Constraints
- **OpC-001**: Agent logic: `backend/agent.py`
- **OpC-002**: FastAPI application: `backend/app.py`
- **OpC-003**: Database operations: `backend/db.py`
- **OpC-004**: Existing retrieval: `backend/retrieve.py` (keep as-is)
- **OpC-005**: Existing models: `backend/models/` (extend as needed)
- **OpC-006**: Environment variables: GEMINI_API_KEY, QDRANT_URL, QDRANT_API_KEY, COHERE_API_KEY, DATABASE_URL (Neon Postgres)
- **OpC-007**: CORS: Allow configurable origins (default: localhost:3000 for Docusaurus dev)

### Backend File Structure

```
backend/
├── app.py              # FastAPI application with routes (NEW)
├── agent.py            # OpenAI Agents SDK agent definition (NEW)
├── db.py               # Neon Postgres session/history operations (NEW)
├── retrieve.py         # Existing semantic search (KEEP)
├── main.py             # Existing embedding ingestion (KEEP)
├── setup_indexes.py    # Existing Qdrant index setup (KEEP)
├── models/
│   ├── __init__.py
│   ├── query.py        # Existing query models (KEEP)
│   ├── response.py     # Existing response models (EXTEND)
│   ├── session.py      # Session/conversation models (NEW)
│   ├── request.py      # API request models (NEW)
│   └── health.py       # Health check models (NEW)
├── tests/
│   └── ...
├── .env
└── pyproject.toml
```

### Integration with Existing Code

The agent MUST import and use these existing functions from retrieve.py:

- `async def search_similar(query_text: str, limit: int = 5, score_threshold: float = 0.5, filters: dict | None = None) -> list[SearchResult]`
  - Generates query embedding via Cohere and performs Qdrant similarity search
  - Returns list of SearchResult objects with chunk_text, metadata, and similarity_score

- `async def get_collection_stats() -> CollectionStats`
  - Returns collection status including vector count and index health
  - Used by /health endpoint to report Qdrant connectivity

## Clarifications

### Session 2025-12-17

- Q: When retrieved chunks have similarity scores between 0.3 and 0.5 (below threshold but not completely irrelevant), how should the system handle them? → A: Include low-confidence results with a warning flag in response metadata
- Q: When the server receives more than 10 concurrent requests (the SC-006 target), how should it behave? → A: Hard limit - reject with 429 Too Many Requests and retry-after header
- Q: What format should be used for request_id in API responses and error tracking? → A: UUID v4 (e.g., `550e8400-e29b-41d4-a716-446655440000`)
- Q: If the Gemini API is unavailable after retry attempts are exhausted, what should happen? → A: Return retrieval results only with message "AI summarization unavailable"
- Q: In selected-text mode, should the citation include a snippet from the provided selection? → A: Yes - include first 200 chars of selection as snippet (matches Qdrant citation format)
- Q: Should this spec include conversation history and session management with Neon Postgres? → A: Yes - include in this spec (aligned with specify_prompt.md requirements)
- Q: What file structure should we adopt given existing backend code? → A: Hybrid - keep retrieve.py & models/, add agent.py, app.py (FastAPI routes), db.py (Neon sessions)

### Spec Review Session 2025-12-16

Applied refinements from spec-3-api-agent-reviewer agent:

- **GAP-001 (CRITICAL)**: Added FR-010a and FR-010b to clarify that Cohere `embed-english-v3.0` MUST be used for query embeddings (not Gemini) to match stored 1024-dim vectors
- **GAP-002 (HIGH)**: Added SourceCitation JSON schema with all required fields
- **GAP-003 (HIGH)**: Added Selected-Text Citation schema for selected_text mode responses
- **GAP-009 (HIGH)**: Added ErrorResponse schema with error_code, message, request_id, details
- **GAP-012 (HIGH)**: Added Integration section specifying existing retrieve.py function signatures
- **OpC-003**: Updated to include COHERE_API_KEY as required environment variable

## Assumptions

- The embedding pipeline (003-embedding-pipeline) has populated the Qdrant collection with book content
- The retrieval module (retrieve.py) provides working async functions for Qdrant queries
- Gemini API free tier has sufficient quota for development and light production use
- Users have a working GEMINI_API_KEY with access to gemini-2.0-flash model
- The Qdrant Cloud cluster is active and accessible
- Neon Serverless Postgres is accessible and within free tier limits
- Network latency to Qdrant Cloud, Gemini API, and Neon Postgres is reasonable (<500ms typical)

## Not Building (Out of Scope)

- User authentication (sessions are anonymous, identified only by client-generated UUID)
- Rate limiting beyond concurrent request cap (handled by API gateway in production)
- Multiple agent handoffs or multi-agent workflows
- Fine-tuning or custom model training
- Caching layer for responses
- WebSocket-based real-time chat (using SSE instead)
- Frontend UI (handled by separate Chatkit spec)
- Batch query processing
- Multi-language support
- Voice input/output
- Conversation history expiration/cleanup (future enhancement)
- Re-ranking algorithms (retrieval uses raw Qdrant similarity scores)
- Query expansion or rewriting (queries sent to Qdrant as-is)
- Embedding model switching (locked to Cohere embed-english-v3.0)
