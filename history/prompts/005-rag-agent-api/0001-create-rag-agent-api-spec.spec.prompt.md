---
id: 0001
title: Create RAG Agent API Specification
stage: spec
date: 2025-12-16
surface: agent
model: claude-opus-4-5-20251101
feature: 005-rag-agent-api
branch: 005-rag-agent-api
user: developer
command: /sp.specify
labels: ["rag", "openai-agents-sdk", "fastapi", "qdrant", "gemini"]
links:
  spec: specs/005-rag-agent-api/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-rag-agent-api/spec.md
  - specs/005-rag-agent-api/checklists/requirements.md
tests:
  - N/A (specification phase)
---

## Prompt

/sp.specify Spec 3: RAG Agent API (OpenAI Agents SDK + FastAPI + Qdrant)

Goal:
Build a FastAPI backend that hosts an OpenAI Agents SDK agent which answers questions about the book by retrieving relevant chunks from Qdrant and grounding responses in those sources.

Target audience:
Backend developers implementing an agentic RAG layer on top of the existing Qdrant retrieval pipeline.

Focus:
- Implement an agent with a retrieval tool that queries Qdrant (top-k + optional metadata filters) and returns cited sources.
- Expose API endpoints for chat (and optionally streaming), returning answer + sources (url/section/chunk refs).
- Support a "selected-text only" mode by accepting user-selected text (or a selection scope) and restricting grounding strictly to that selection.

Success criteria:
- For general questions, the agent retrieves from Qdrant and answers with source metadata for citations.
- For selected-text mode, responses are grounded only in the provided selection (or explicitly say "not found in selection")

Use context7 mcp server to fetch the OpenAI Agents SDK documentation. Analyze the .specify/memory/openai-knowledge.md and .specify/memory/specify_prompt.md files in order to take the context from them. Make sure to just make one file for agent named agent.py for agent persisting retrieval function in order to respond user queries. Also, Make sure to use OpenAI Agents SDK (with Gemini API via OpenAI-compatible endpoint).

## Response snapshot

Created comprehensive specification for RAG Agent API (005-rag-agent-api) with:

**User Stories (5)**:
- P1: General Book Q&A - Core RAG functionality with citations
- P1: Selected-Text-Only Mode - Restricted context grounding
- P1: Source Citation/Attribution - Trustworthy responses
- P2: Out-of-Scope Handling - Graceful decline for unrelated questions
- P2: Health/Monitoring - Operational observability

**Functional Requirements (25)**: Covering agent configuration (FR-001 to FR-005), retrieval tool (FR-006 to FR-010), API endpoints (FR-011 to FR-014), selected-text mode (FR-015 to FR-018), response quality (FR-019 to FR-022), and error handling (FR-023 to FR-025).

**Key Technical Decisions** (documented in Constraints section per user request):
- Single agent file: `backend/src/agent.py`
- OpenAI Agents SDK with Gemini 2.0 Flash via OpenAI-compatible endpoint
- `@function_tool` decorated retrieval function querying Qdrant
- Depends on 004-embedding-retrieval module

**Success Criteria (8)**: Measurable outcomes including 90% accuracy, 3-second response time, 100% citation coverage, and selected-text mode isolation.

## Outcome

- Impact: High - Establishes the core agentic RAG layer connecting retrieval pipeline to user-facing chat
- Tests: N/A (specification phase - tests will be defined during planning)
- Files: 2 files created (spec.md, checklists/requirements.md)
- Next prompts: /sp.plan to create technical architecture, or /sp.clarify if refinement needed
- Reflection: Spec balances user-facing value (Q&A, citations) with technical constraints (Gemini API, single agent file) while maintaining clear boundaries via Out of Scope section

## Evaluation notes (flywheel)

- Failure modes observed: None - all validation checks passed
- Graders run and results (PASS/FAIL): Requirements checklist 16/16 PASS
- Prompt variant (if applicable): Standard /sp.specify with custom context files
- Next experiment (smallest change to try): None needed - proceed to /sp.plan
