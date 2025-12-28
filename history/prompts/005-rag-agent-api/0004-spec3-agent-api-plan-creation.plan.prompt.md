---
id: "0004"
title: "Spec-3 Agent API Plan Creation"
stage: plan
date: 2025-12-17
surface: agent
model: claude-opus-4-5
feature: 005-rag-agent-api
branch: 005-rag-agent-api
user: user
command: /sp.plan
labels: ["openai-agents-sdk", "fastapi", "qdrant", "gemini", "rag", "planning"]
links:
  spec: specs/005-rag-agent-api/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-rag-agent-api/research.md
  - specs/005-rag-agent-api/data-model.md
  - specs/005-rag-agent-api/contracts/openapi.yaml
  - specs/005-rag-agent-api/quickstart.md
  - specs/005-rag-agent-api/plan.md
tests:
  - N/A (planning phase)
---

## Prompt

use the spec-3 planner agent

* Create: architecture sketch for (FastAPI service > OpenAI Agents SDK agent > Qdrant retrieval tool > response with citations + selected-text-only mode);
define minimal endpoint(s) + response schema.
* Research approach: research-concurrent; if Agents SDK details aren't in context, use Context7 MCP to fetch official OpenAI Agents SDK docs before
finalizing tool wiring.
* Decisions needing documentation: streaming vs non-streaming; tool interface (inputs/outputs); citation payload shape; selected-text-only enforcement
strategy; error/fallback behavior.
* Quality validation: logging/tracing plan + "no hallucinated citations" rule; handle empty/low-confidence retrieval safely.
* Testing strategy: API smoke tests for chat + selected-text; Qdrant connectivity check; deterministic test prompts with expected cited sources.
* - you can create agent.py file in backend folder in this file you can get embedding from qdrant you have qdrant url and qdran api and you have also qdrant
collection name

## Response snapshot

Created comprehensive planning artifacts for Spec-3 RAG Agent API:

1. **research.md**: Documented 10 key decisions including:
   - OpenAI Agents SDK integration with Gemini via OpenAI-compatible endpoint
   - Both streaming (/chat/stream) and non-streaming (/chat) endpoints
   - @function_tool decorator wrapping existing retrieve.search()
   - Dynamic agent instructions for selected-text mode enforcement
   - Graceful degradation when Gemini unavailable
   - Citation validation from tool results only (no hallucination)
   - JSON structured logging with request correlation
   - Tiered response strategy for low-confidence retrieval

2. **data-model.md**: Defined all entity schemas:
   - ChatRequest, ChatResponse, SourceCitation, SelectedTextCitation
   - Session, ConversationRecord for history
   - HealthResponse, ErrorResponse
   - SQL schemas for Neon Postgres tables

3. **contracts/openapi.yaml**: Complete OpenAPI 3.1 specification with:
   - POST /chat, POST /chat/stream, GET /health, GET /history/{session_id}
   - All request/response schemas with examples
   - Error codes and responses

4. **quickstart.md**: Setup and testing instructions

5. **plan.md**: Updated with Technical Context, Constitution Check, Architecture diagram, Key Decisions, Risk Analysis, Testing Strategy

## Outcome

- Impact: Complete technical plan ready for task generation
- Tests: N/A (planning phase - tests defined in plan)
- Files: 5 files created/updated in specs/005-rag-agent-api/
- Next prompts: Run /sp.tasks to generate implementation tasks
- Reflection: Context7 MCP research was valuable for SDK wiring patterns; existing retrieve.py integration will simplify implementation

## Evaluation notes (flywheel)

- Failure modes observed: None - planning completed successfully
- Graders run and results (PASS/FAIL): N/A (planning phase)
- Prompt variant (if applicable): spec3-agent-api-planner agent + concurrent Context7 research
- Next experiment (smallest change to try): Validate Gemini OpenAI-compatible endpoint with actual API call before implementation
