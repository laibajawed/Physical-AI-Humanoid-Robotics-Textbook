# Implementation Plan: RAG Agent API

**Branch**: `005-rag-agent-api` | **Date**: 2025-12-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-rag-agent-api/spec.md`

## Summary

Build a FastAPI backend that hosts an OpenAI Agents SDK agent which answers questions about the Physical AI & Robotics textbook by retrieving relevant chunks from Qdrant and grounding responses in those sources. The agent supports both full-book search and selected-text-only mode, with structured citations, session-based conversation history, and graceful degradation when services are unavailable.

**Technical Approach**:
- FastAPI for async REST API with SSE streaming support
- OpenAI Agents SDK with Gemini 2.0 Flash via OpenAI-compatible endpoint
- `@function_tool` decorator wrapping existing `retrieve.search_similar()` function
- Dynamic agent instructions for selected-text mode enforcement
- Neon Postgres for session/conversation history storage

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- FastAPI 0.115.0+ (async REST framework)
- OpenAI Agents SDK (`openai-agents>=0.2.0`)
- OpenAI Python SDK (`openai>=1.60.0`) for AsyncOpenAI client
- Qdrant Client (`qdrant-client>=1.16.2`) - existing
- Cohere (`cohere>=5.20.0`) - existing for embeddings
- SQLAlchemy 2.0+ with asyncpg (Neon Postgres)
- Pydantic 2.10+ (request/response validation)
- Uvicorn (ASGI server)

**Storage**:
- Qdrant Cloud: Vector storage (`rag_embedding` collection, 1024-dim Cohere vectors)
- Neon Serverless Postgres: Session and conversation history

**Testing**: pytest + pytest-asyncio

**Target Platform**: Linux/Windows server, containerizable

**Project Type**: Backend API service (single project structure)

**Performance Goals**:
- p95 response latency < 3 seconds
- 10 concurrent requests without errors
- p95 latency under load <= 5 seconds

**Constraints**:
- Connection timeout: Qdrant 10s, Gemini 30s, Postgres 5s
- Max concurrent requests: 10 (429 after)
- Max query length: 8000 tokens (~32000 chars)
- Max selected text: 16000 tokens (~64000 chars)

**Scale/Scope**: Single-region deployment, light production traffic

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Compliance | Notes |
|-----------|------------|-------|
| **CODE QUALITY** | PASS | Python 3.11 with type hints, Pydantic for validation, existing retrieve.py patterns |
| **USER EXPERIENCE** | PASS | Fast responses (<3s), streaming for long answers, graceful degradation |
| **CONTENT ORGANIZATION** | N/A | Backend API, not content |
| **DESIGN STANDARDS** | N/A | Backend API, not UI |

**Additional Quality Checks**:
- Zero unnecessary external dependencies (reusing existing SDK patterns)
- Async-first architecture for performance
- Structured JSON logging for observability
- No secrets in code (environment variables)
- Type-safe request/response models with Pydantic

## Project Structure

### Documentation (this feature)

specs/005-rag-agent-api/
- spec.md              # Feature specification
- plan.md              # This file
- research.md          # Phase 0 output - SDK wiring, decisions
- data-model.md        # Phase 1 output - entity definitions
- quickstart.md        # Phase 1 output - setup instructions
- contracts/
  - openapi.yaml       # Phase 1 output - API contract
- tasks.md             # Phase 2 output (/sp.tasks command)

### Source Code (repository root)

backend/
- app.py              # FastAPI application with routes (NEW)
- agent.py            # OpenAI Agents SDK agent definition (NEW)
- db.py               # Neon Postgres session/history operations (NEW)
- retrieve.py         # Existing semantic search (KEEP)
- main.py             # Existing embedding ingestion (KEEP)
- setup_indexes.py    # Existing Qdrant index setup (KEEP)
- models/
  - __init__.py       # Export all models (EXTEND)
  - query.py          # Existing query models (KEEP)
  - response.py       # Existing + chat response models (EXTEND)
  - request.py        # API request models (NEW)
  - session.py        # Session/conversation models (NEW)
  - health.py         # Health check models (NEW)
- tests/
  - test_api.py       # API endpoint tests (NEW)
  - test_agent.py     # Agent behavior tests (NEW)
  - test_db.py        # Database operation tests (NEW)
- .env
- pyproject.toml      # Dependencies (UPDATE)

**Structure Decision**: Single backend project extending existing structure. New files (app.py, agent.py, db.py) integrate with existing retrieve.py module.

## Key Implementation Decisions

### 1. Streaming vs Non-Streaming
**Decision**: Implement both /chat (non-streaming) and /chat/stream (SSE)
**Rationale**: Non-streaming for simple integrations, streaming for better UX
**Reference**: research.md section 2

### 2. Tool Interface
**Decision**: @function_tool wrapper around existing retrieve.search()
**Rationale**: Reuses tested code, returns JSON string per SDK requirements
**Reference**: research.md section 3

### 3. Selected-Text Enforcement
**Decision**: Dynamic agent instructions (no tool in selected-text mode)
**Rationale**: Simpler than two agents, explicit LLM instruction
**Reference**: research.md section 5

### 4. Citation Validation
**Decision**: Citations extracted from tool results only, never generated
**Rationale**: Prevents hallucinated citations
**Reference**: research.md section 8

### 5. Error/Fallback Behavior
**Decision**: Graceful degradation returning retrieval-only results
**Rationale**: Better UX than complete failure when Gemini unavailable
**Reference**: research.md section 6

## Complexity Tracking

No constitution violations requiring justification.

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gemini API unavailable | High | Graceful degradation returns retrieval-only results |
| Qdrant timeout | High | 3x retry with exponential backoff, 503 response |
| Citation hallucination | Medium | Extract citations from tool results only |
| Session data loss | Low | Postgres with durability guarantees |
| Rate limit exceeded | Low | 429 response with retry-after header |

## Testing Strategy

### Smoke Tests
1. POST /chat - basic question returns answer + sources
2. POST /chat (selected_text) - no Qdrant queries, answer from selection
3. GET /health - returns service status
4. POST /chat/stream - SSE events received
5. Rate limit - 11th concurrent request gets 429

### Integration Tests
1. Full flow: question -> retrieval -> agent -> response
2. Session continuity: multiple requests same session_id
3. Conversation history retrieval
4. Out-of-scope question handling

## ADR Candidates

Potential ADRs (suggest documenting if team agrees):
1. ADR: Gemini via OpenAI-compatible endpoint - Why use this over direct Gemini SDK
2. ADR: Dynamic agent instructions for mode switching - Why not multiple agents
3. ADR: Citation extraction from tool results - Why not let LLM generate citations

Run /sp.adr <title> to document any of these decisions.

## Next Steps

1. Run /sp.tasks to generate atomic implementation tasks
2. Implement in order: models -> agent -> app -> tests
3. Verify with /sp.verify before marking complete
