---
id: 0003
title: ChatKit Integration Planning
stage: plan
date: 2025-12-18
surface: agent
model: claude-opus-4-5-20251101
feature: 006-chatkit-frontend
branch: 006-chatkit-frontend
user: developer
command: /sp.plan
labels: ["planning", "chatkit", "frontend", "integration", "architecture"]
links:
  spec: specs/006-chatkit-frontend/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-chatkit-frontend/research.md
  - specs/006-chatkit-frontend/data-model.md
  - specs/006-chatkit-frontend/contracts/frontend-api.yaml
  - specs/006-chatkit-frontend/quickstart.md
  - specs/006-chatkit-frontend/plan.md
tests:
  - E2E smoke test checklist defined (8 tests)
---

## Prompt

use spec4-integration-planner

- Create: end-to-end architecture sketch for (Docusaurus book + embedded ChatKit UI ↔ FastAPI agent API ↔ Qdrant retrieval ↔ Neon Postgres via database.py), including selected-text-only request flow.
- Contract: define API endpoints + payload schema (message, session_id, selected_text, stream flag) and response schema (answer + citations + errors), plus env-based API base URL config for dev/prod.
- Decisions to document: widget placement (global vs per-page), streaming vs non-streaming, session_id storage (cookie vs localStorage), and CORS policy (strict allowlist for localhost + deployed book domain).
- Quality validation: enforce "selected-text-only" gating + safe fallbacks when retrieval is empty; define minimal logging (request id, session id) without leaking secrets.
- Testing strategy: E2E smoke checklist—UI renders, no CORS errors, chat completes, citations render, history persists/reloads, selected-text-only is enforced.

## Response snapshot

Generated comprehensive Spec-4 technical plan for ChatKit frontend integration with FastAPI backend:

**Key Architectural Decisions:**
1. **Widget Placement**: Global floating widget via `src/theme/Layout/index.tsx` wrapper
2. **Streaming**: SSE via `/chat/stream` endpoint with non-streaming fallback
3. **Session Storage**: Client-generated UUID v4 in localStorage (`chatkit_session_id`)
4. **State Management**: React Context + useReducer (per constraint FC-005)
5. **CORS Policy**: Strict allowlist (no wildcards in production)

**Artifacts Generated:**
- `research.md`: Phase 0 decisions and architecture analysis
- `data-model.md`: TypeScript interfaces for frontend state and API contracts
- `contracts/frontend-api.yaml`: OpenAPI specification for frontend-backend contract
- `quickstart.md`: Implementation guide with code examples
- `plan.md`: Complete technical plan with component architecture and testing strategy

**API Contracts Defined:**
- POST `/chat` - Non-streaming Q&A
- POST `/chat/stream` - SSE streaming
- GET `/history/{session_id}` - Conversation history
- GET `/health` - Service health check

**CORS Configuration Required:**
```
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://hackathon-i-physical-ai-humanoid-ro-dun.vercel.app
```

## Outcome

- Impact: Complete technical architecture and implementation guide for Spec-4 frontend integration
- Tests: E2E smoke test checklist with 8 tests defined
- Files: 5 planning artifacts created in specs/006-chatkit-frontend/
- Next prompts: Run `/sp.tasks` to generate atomic implementation tasks
- Reflection: Used spec4-integration-planner agent effectively; all NEEDS CLARIFICATION items resolved

## Evaluation notes (flywheel)

- Failure modes observed: None - planning completed successfully
- Graders run and results (PASS/FAIL): N/A (planning phase)
- Prompt variant (if applicable): spec4-integration-planner agent
- Next experiment (smallest change to try): Implement Phase 1 components following quickstart.md order
