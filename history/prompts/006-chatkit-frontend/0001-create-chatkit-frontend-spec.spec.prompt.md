---
id: 0001
title: Create ChatKit Frontend Spec
stage: spec
date: 2025-12-18
surface: agent
model: claude-opus-4-5-20251101
feature: 006-chatkit-frontend
branch: 006-chatkit-frontend
user: architect
command: /sp.specify
labels: ["chatkit", "frontend", "docusaurus", "cors", "integration", "rag"]
links:
  spec: specs/006-chatkit-frontend/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-chatkit-frontend/spec.md
  - specs/006-chatkit-frontend/checklists/requirements.md
tests:
  - N/A (specification phase)
---

## Prompt

Spec 4: Docusaurus ChatKit Frontend + Integration (FastAPI + Neon + CORS)

Goal:
Build the RAG chatbot frontend inside the Docusaurus book using ChatKit, then integrate it with the existing FastAPI + OpenAI Agents backend, including Neon Postgres chat history (database.py) and browser-safe CORS.

Target audience:
Readers of the published book (embedded chatbot) and developers maintaining the full-stack RAG experience.

Focus:
- Implement ChatKit UI embedded in Docusaurus (widget/page) and connect it to backend chat endpoint(s).
- Add selected-text-only UX: capture highlighted text from the book and send it with the user question.
- Add session + history: frontend manages a session_id; backend persists/retrieves history via Neon Postgres (database.py).
- Enable CORS for local dev + production (origin allowlist), so frontend can call FastAPI safely.

Success criteria:
- Chat UI works locally and after deployment; requests reach backend without CORS errors.
- Responses render with citations/sources; errors/empty retrieval handled gracefully.
- Selected-text-only mode works end-to-end (selection captured → sent → enforced → shown).
- Chat history persists per session_id (save + reload works) using Neon via database.py.

Constraints:
- Frontend: Docusaurus + ChatKit.
- Backend: existing FastAPI agent endpoints + Qdrant retrieval; Neon Postgres used for persistence.
- CORS must be allowlist-based (dev localhost + production book domain), not wide-open in production.

Not building:
- Full auth/accounts, multi-tenant RBAC, billing, analytics dashboard.
- New ingestion/embedding/vector schema changes (handled in earlier specs).
- Major UI redesign beyond a clean embedded chat experience.

## Response snapshot

Created comprehensive specification for Spec 4 (006-chatkit-frontend):

**Key Deliverables:**
1. Feature branch `006-chatkit-frontend` created and checked out
2. Spec file at `specs/006-chatkit-frontend/spec.md` with:
   - 6 prioritized user stories (P1: core chat, citations, selected-text; P2: history, errors, responsive)
   - 28 functional requirements covering UI, backend integration, selection mode, sessions, errors, CORS
   - 8 measurable success criteria (all technology-agnostic)
   - 7 edge cases with explicit handling behaviors
   - Clear constraints for frontend (Docusaurus/ChatKit), backend (existing FastAPI), and integration
   - File structure showing component organization
3. Quality checklist at `specs/006-chatkit-frontend/checklists/requirements.md` - all 16 items pass

**Spec Highlights:**
- P1 features enable core RAG chatbot value: ask questions, see sources, use selected-text mode
- CORS requirements explicitly defined (FR-025 through FR-028) for secure origin allowlist
- Session management via localStorage with backend persistence via existing db.py
- Error handling covers CORS, network, streaming interruption, rapid submission

## Outcome

- Impact: Created complete, validated specification for ChatKit frontend integration
- Tests: N/A (specification phase, no tests yet)
- Files: 2 files created (spec.md, requirements.md checklist)
- Next prompts: `/sp.clarify` for any ambiguities, then `/sp.plan` for technical architecture
- Reflection: Spec leverages existing backend infrastructure (app.py, db.py) - minimal backend changes needed

## Evaluation notes (flywheel)

- Failure modes observed: None - spec passed all 16 quality checklist items
- Graders run and results (PASS/FAIL): Manual validation PASS
- Prompt variant (if applicable): Standard /sp.specify workflow
- Next experiment (smallest change to try): Run /sp.plan to validate architectural feasibility
