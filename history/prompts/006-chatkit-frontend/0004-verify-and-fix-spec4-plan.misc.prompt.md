---
id: 0004
title: Verify and Fix Spec-4 Plan
stage: misc
date: 2025-12-18
surface: agent
model: claude-opus-4-5-20251101
feature: 006-chatkit-frontend
branch: 006-chatkit-frontend
user: developer
command: verify Spec-4 plan
labels: ["verification", "bugfix", "planning", "schema", "docusaurus"]
links:
  spec: specs/006-chatkit-frontend/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-chatkit-frontend/data-model.md
  - specs/006-chatkit-frontend/contracts/frontend-api.yaml
  - specs/006-chatkit-frontend/quickstart.md
  - specs/006-chatkit-frontend/plan.md
tests:
  - Verification checklist (9 areas reviewed)
---

## Prompt

verify Spec-4 plan using spec4-integration-planner

yes (fix the critical issues)

## Response snapshot

**Verification Summary**: PASS WITH MINOR ISSUES (95% complete)

**Two Critical Issues Identified and Fixed:**

1. **History Entry Schema Mismatch** (FIXED)
   - Issue: Frontend expected `{role, content}` but backend returns `{query, response}`
   - Fix: Updated `data-model.md`, `contracts/frontend-api.yaml`, `quickstart.md` to use correct schema
   - Added `transformHistoryToMessages()` helper to convert backend format to UI format

2. **Environment Variable Pattern** (FIXED)
   - Issue: Plan used `NEXT_PUBLIC_BACKEND_URL` but Docusaurus is NOT Next.js
   - Fix: Updated to use `docusaurus.config.ts` customFields pattern:
     ```typescript
     customFields: {
       backendUrl: process.env.BACKEND_URL || 'http://localhost:8000',
     }
     ```
   - Added `useBackendUrl()` hook for React component access

**Files Modified:**
- `data-model.md`: Fixed HistoryEntry interface, added transformation helper
- `contracts/frontend-api.yaml`: Fixed HistoryEntry schema, updated env docs
- `quickstart.md`: Fixed config pattern, API client to use backendUrl parameter
- `plan.md`: Fixed env configuration section, added history transformation docs

## Outcome

- Impact: All critical issues fixed; plan now 100% aligned with backend
- Tests: Verification checklist passed (9/9 areas)
- Files: 4 files updated with corrections
- Next prompts: Run `/sp.tasks` to generate implementation tasks
- Reflection: Verification step caught important schema mismatches that would have caused runtime errors

## Evaluation notes (flywheel)

- Failure modes observed: Schema mismatch between frontend types and backend models; Next.js pattern used in Docusaurus context
- Graders run and results (PASS/FAIL): Verification PASS after fixes
- Prompt variant (if applicable): spec4-integration-planner agent
- Next experiment (smallest change to try): Add backend schema validation tests to catch mismatches earlier
