---
id: 0002
title: Clarify Authentication Spec
stage: spec
date: 2025-12-23
surface: agent
model: claude-opus-4-5-20251101
feature: 007-authentication-integration
branch: main
user: developer
command: /sp.clarify
labels: ["authentication", "clarification", "jwt", "session-management", "cross-domain"]
links:
  spec: specs/007-authentication-integration/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/007-authentication-integration/spec.md
tests:
  - null
---

## Prompt

/sp.clarify

(Run clarification workflow on the authentication integration spec to identify and resolve ambiguities before planning phase.)

## Response snapshot

Performed structured ambiguity scan across 10 taxonomy categories. Identified 4 areas requiring clarification:

**Questions Asked & Answered (4/5 max):**

1. **Cross-Domain JWT Transmission**: How to pass JWT from Vercel (frontend) to Railway (backend)?
   → Frontend reads JWT cookie and adds `Authorization: Bearer <token>` header to FastAPI requests.

2. **Post-Signup Redirect**: Where should users go after creating an account?
   → Redirect to `/docs/introduction` (book start).

3. **Email Verification**: Required before accessing protected content?
   → No, users can access immediately after signup (reduces friction for MVP).

4. **Session Duration**: What expiry times for Remember Me ON/OFF?
   → Remember Me OFF: 1 hour (browser session), Remember Me ON: 30 days.

**Spec Sections Updated:**
- Added `### Session 2025-12-23` under Clarifications & Decisions
- Updated User Story 1 acceptance scenario (redirect destination)
- Updated FR-017 (explicit cross-domain JWT handling)
- Updated NFR-002 (session duration values)
- Clarified "Not Building" section (email verification status)
- Updated Test Scenario 1 (expected redirect)

## Outcome

- ✅ Impact: All critical ambiguities resolved; spec ready for planning phase
- 🧪 Tests: N/A (clarification phase)
- 📁 Files: specs/007-authentication-integration/spec.md (updated)
- 🔁 Next prompts: /sp.plan
- 🧠 Reflection: Cross-domain cookie/JWT handling was the highest-impact clarification; essential for hybrid architecture to work correctly

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): standard /sp.clarify
- Next experiment: Verify Better Auth cookie access pattern during implementation
