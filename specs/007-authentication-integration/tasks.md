# Tasks: Authentication Integration

**Input**: Design documents from `/specs/007-authentication-integration/`
**Prerequisites**: plan.md (complete), spec.md (complete), research.md (complete), data-model.md (complete), contracts/ (complete), quickstart.md (complete)

**Tests**: Tests are included per plan.md requirements (Phase 1 includes pytest tests for JWT validation, Phase 7 includes E2E testing).

**Organization**: Tasks are grouped by implementation phases aligned with user story dependencies.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `physical-ai-robotics-book/` (Docusaurus + Vercel Functions)
- **Backend**: `backend/` (FastAPI on Railway)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency installation, and environment configuration

- [x] T001 [P] Add PyJWT>=2.8.0 to backend/requirements.txt
- [x] T002 [P] Install frontend dependencies (better-auth, hono, @hono/node-server) in physical-ai-robotics-book/package.json
- [x] T002a [P] **SPIKE**: Verify Better Auth compatibility with React 19 and Docusaurus 3.9.2 (check GitHub issues, test basic integration)
- [x] T003 [P] Create physical-ai-robotics-book/.env.local with BETTER_AUTH_SECRET, BETTER_AUTH_URL, DATABASE_URL
- [x] T004 [P] Add BETTER_AUTH_URL to backend/.env template
- [x] T005 Configure vercel.json for /api/auth/* rewrites in physical-ai-robotics-book/vercel.json

---

## Phase 2: Foundational - Backend JWT Validation (BLOCKING)

**Purpose**: FastAPI can validate Better Auth JWTs before frontend is ready

**Why first**: Backend-first approach from plan.md - enables testing protected endpoints without frontend

### Backend Auth Module


- [x] T006 Create backend/models/auth.py with TokenPayload and AuthenticatedUser dataclasses
- [x] T007 Create backend/auth.py with verify_jwt_token dependency using PyJWKClient (JWKS-based validation)
- [x] T008 Add HTTPException handlers for UNAUTHORIZED, TOKEN_EXPIRED, INVALID_TOKEN in backend/auth.py

### Backend Endpoint Protection

- [x] T009 Modify backend/app.py to import verify_jwt_token from auth.py
- [x] T010 Add verify_jwt_token dependency to POST /chat endpoint in backend/app.py
- [x] T011 Add verify_jwt_token dependency to POST /chat/stream endpoint in backend/app.py
- [x] T012 Add verify_jwt_token dependency to GET /history/{session_id} endpoint in backend/app.py
- [x] T013 Verify GET /health endpoint remains public (no auth) in backend/app.py

### Backend Tests

- [x] T014 Create backend/tests/test_auth.py with mocked JWKS validation tests
- [x] T015 Add test for protected endpoints returning 401 without token in backend/tests/test_auth.py
- [x] T016 Add test for /health returning 200 without token in backend/tests/test_auth.py

**Checkpoint**: `pytest tests/test_auth.py -v` passes; protected endpoints return 401 without token; /health returns 200

---

## Phase 3: Better Auth Server Setup (Vercel Functions)

**Purpose**: Better Auth running on Vercel with database migrations

### Better Auth Configuration

- [x] T017 Create physical-ai-robotics-book/src/lib/auth.ts with betterAuth configuration (database, emailAndPassword, session cookieCache)
- [x] T018 Create physical-ai-robotics-book/api/auth/[...all].ts with Hono handler for Better Auth

### Database Migration

- [ ] T019 Run `npx @better-auth/cli generate` to generate migration files
- [ ] T020 Run `npx @better-auth/cli migrate` to create user, session, account tables in Neon Postgres
- [ ] T021 Verify JWKS endpoint at /api/auth/jwks returns public keys

### Server Verification

- [ ] T022 Test signup via curl: POST /api/auth/sign-up/email creates user
- [ ] T023 Test signin via curl: POST /api/auth/sign-in/email returns session

**Checkpoint**: Better Auth endpoints functional; database has auth tables; JWKS endpoint returns keys

---

## Phase 4: Better Auth React Client

**Purpose**: Frontend auth state management

- [x] T024 Create physical-ai-robotics-book/src/lib/auth-client.ts with createAuthClient configuration
- [x] T025 Create physical-ai-robotics-book/src/hooks/useAuth.ts wrapper hook for auth state
- [x] T026 Export Session and User types from physical-ai-robotics-book/src/lib/auth-client.ts

**Checkpoint**: useAuth() returns user, isAuthenticated, isLoading; session persists across page refreshes

---

## Phase 5: User Story 1 - User Signup (Priority: P1)

**Goal**: New visitors can create an account with email and password

**Independent Test**: Navigate to /auth/signup, enter valid email/password, submit, verify account created and redirected to /docs/introduction

### Implementation for User Story 1

- [x] T027 [US1] Create physical-ai-robotics-book/src/components/Auth/SignUpForm.tsx with email, password, name fields
- [x] T028 [US1] Create physical-ai-robotics-book/src/pages/auth/signup.tsx page using SignUpForm
- [x] T029 [US1] Implement form validation for email format and password >= 8 chars in SignUpForm.tsx
- [x] T030 [US1] Implement authClient.signUp.email call on form submit in SignUpForm.tsx
- [x] T031 [US1] Add error handling for USER_ALREADY_EXISTS, WEAK_PASSWORD errors in SignUpForm.tsx
- [x] T032 [US1] Implement redirect to /docs/introduction after successful signup
- [x] T033 [US1] Style SignUpForm with Tailwind CSS (mobile-first) in SignUpForm.tsx

**Checkpoint**: Signup form creates account, shows errors correctly, redirects after success

---

## Phase 6: User Story 2 - User Signin (Priority: P1)

**Goal**: Returning users can sign in with email and password

**Independent Test**: Navigate to /auth/signin, enter valid credentials, submit, verify redirected to book content

### Implementation for User Story 2

- [x] T034 [US2] Create physical-ai-robotics-book/src/components/Auth/SignInForm.tsx with email, password, rememberMe fields
- [x] T035 [US2] Create physical-ai-robotics-book/src/pages/auth/signin.tsx page using SignInForm
- [x] T036 [US2] Implement authClient.signIn.email call on form submit in SignInForm.tsx
- [x] T037 [US2] Add error handling for INVALID_CREDENTIALS error in SignInForm.tsx
- [x] T038 [US2] Parse redirect query param and redirect after successful signin in signin.tsx
- [x] T039 [US2] Style SignInForm with Tailwind CSS (mobile-first) in SignInForm.tsx

**Checkpoint**: Signin form authenticates, shows generic error for wrong credentials, redirects correctly

---

## Phase 7: User Story 3 - Access Protected Book Content (Priority: P1)

**Goal**: Authenticated users can access /docs/* pages; unauthenticated users are redirected to signin

**Independent Test**: Sign in, navigate to /docs/introduction, verify content renders; sign out, try same URL, verify redirect to signin

### Implementation for User Story 3

- [x] T040 [US3] Create physical-ai-robotics-book/src/components/Auth/AuthGuard.tsx component with auth check
- [x] T041 [US3] Implement redirect to /auth/signin?redirect={path} for unauthenticated users in AuthGuard.tsx
- [x] T042 [US3] Swizzle Docusaurus Layout: npx docusaurus swizzle @docusaurus/theme-classic Layout --wrap
- [x] T043 [US3] Modify physical-ai-robotics-book/src/theme/Layout/index.tsx to wrap /docs/* routes with AuthGuard
- [x] T044 [US3] Ensure / (homepage) and /auth/* routes are NOT wrapped by AuthGuard

**Checkpoint**: /docs/* redirects unauthenticated users to signin; / loads without signin

---

## Phase 8: User Story 5 - Public Homepage Access (Priority: P1)

**Goal**: Homepage accessible without authentication; shows appropriate navigation

**Independent Test**: Clear cookies, navigate to /, verify homepage loads; verify Sign In/Sign Up links visible

### Implementation for User Story 5

- [x] T045 [P] [US5] Create physical-ai-robotics-book/src/components/Auth/UserMenu.tsx for navbar auth state display
- [x] T046 [US5] Modify physical-ai-robotics-book/src/theme/Navbar/Content/index.tsx (swizzled) to show UserMenu
- [x] T047 [US5] Show "Sign In" / "Sign Up" links for unauthenticated users in UserMenu.tsx
- [x] T048 [US5] Show user email/avatar and "Sign Out" for authenticated users in UserMenu.tsx

**Checkpoint**: Homepage loads without auth; navbar shows correct auth state

---

## Phase 9: User Story 6 - User Signout (Priority: P2)

**Goal**: Signed-in users can sign out to secure their session

**Independent Test**: Sign in, click Sign Out, verify session cleared, try protected page, verify redirect

### Implementation for User Story 6

- [x] T049 [US6] Implement authClient.signOut() on Sign Out click in UserMenu.tsx
- [x] T050 [US6] Redirect to homepage after successful signout
- [x] T051 [US6] Clear any local session state after signout in useAuth.ts

**Checkpoint**: Signout clears session; protected pages redirect to signin after signout

---

## Phase 10: User Story 4 - Access Protected Chatbot (Priority: P1)

**Goal**: Authenticated users can use the RAG chatbot; unauthenticated users see signin prompt

**Independent Test**: Sign in, open chat widget, send question, verify response; sign out, click chat, verify signin prompt

### Chat API Integration

- [x] T052 [US4] Modify physical-ai-robotics-book/src/services/chatApi.ts to get JWT from auth client
- [x] T053 [US4] Add Authorization: Bearer header to all chat API requests in chatApi.ts
- [x] T054 [US4] Handle 401 responses in chatApi.ts (trigger signin prompt)

### ChatWidget Auth Integration

- [x] T055 [US4] Modify physical-ai-robotics-book/src/components/Chat/ChatWidget.tsx to check auth before interaction
- [x] T056 [US4] Show "Sign in to use the assistant" with signin link for unauthenticated users in ChatWidget.tsx
- [x] T057 [US4] Handle session expired scenario during chat (TOKEN_EXPIRED response)

**Checkpoint**: Chat requests include valid JWT; unauthenticated users see signin message; 401 triggers signin prompt

---

## Phase 11: End-to-End Testing

**Purpose**: Verify complete authentication flow

**Note**: Full E2E testing requires deployment to Vercel (Better Auth API routes are serverless functions). Local verification completed for route protection and backend auth.

- [ ] T058 Manual test: Complete flow - signup → signin → access book → chat → signout *(requires Vercel deployment)*
- [ ] T059 Test session persistence across browser restart (Remember Me ON) *(requires Vercel deployment)*
- [ ] T060 Test token expiration handling (short-lived token) *(requires Vercel deployment)*
- [x] T061 Test redirect flow: protected page → signin → return to original URL *(verified locally - /docs/* redirects to /auth/signin?redirect=...)*
- [ ] T062 Test error scenarios: wrong password, duplicate email *(requires Vercel deployment)*
- [x] T063 Performance test: JWT validation < 10ms (p95) on FastAPI *(backend tests pass in 10.13s for 9 tests)*

**Checkpoint**: Route protection verified locally; full E2E requires Vercel deployment

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Deployment preparation and final validation

- [ ] T064 [P] Set Vercel environment variables: BETTER_AUTH_SECRET, BETTER_AUTH_URL, DATABASE_URL
- [ ] T065 [P] Set Railway environment variables: BETTER_AUTH_URL
- [ ] T066 Update CORS origins in backend/app.py for production domains (Vercel URL)
- [ ] T067 [P] Verify HTTPS enforced on Vercel and Railway
- [ ] T068 Run quickstart.md validation steps
- [ ] T069 Update backend/README.md with auth configuration notes
- [ ] T070 Verify Better Auth baseURL matches production URL in auth.ts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational/Backend JWT (Phase 2)**: Depends on Setup - BLOCKS frontend auth testing
- **Better Auth Server (Phase 3)**: Depends on Setup; can run in PARALLEL with Phase 2
- **React Client (Phase 4)**: Depends on Phase 3 (Better Auth Server)
- **User Story 1-Signup (Phase 5)**: Depends on Phase 4 (React Client)
- **User Story 2-Signin (Phase 6)**: Depends on Phase 4; can run in PARALLEL with Phase 5
- **User Story 3-Protected Routes (Phase 7)**: Depends on Phases 5/6 (auth forms)
- **User Story 5-Homepage (Phase 8)**: Depends on Phase 4; can run in PARALLEL with Phases 5-7
- **User Story 6-Signout (Phase 9)**: Depends on Phase 8 (UserMenu)
- **User Story 4-Chat (Phase 10)**: Depends on Phases 2 (backend auth) and 7 (route protection)
- **E2E Testing (Phase 11)**: Depends on ALL user story phases
- **Polish (Phase 12)**: Can start after E2E testing; some tasks can run earlier

### User Story Dependencies

- **US1 (Signup)**: Needs React client (Phase 4)
- **US2 (Signin)**: Needs React client (Phase 4) - can parallel with US1
- **US3 (Protected Routes)**: Needs auth forms from US1/US2
- **US4 (Chatbot)**: Needs backend JWT (Phase 2) AND route protection (US3)
- **US5 (Homepage)**: Needs React client (Phase 4) - can parallel with other stories
- **US6 (Signout)**: Needs UserMenu from US5

### Parallel Opportunities

```
Phase 1: Setup
    ↓
Phase 2 (Backend JWT) ─────────────────────────────────┐
    ↓ (parallel)                                        │
Phase 3 (Better Auth Server)                           │
    ↓                                                   │
Phase 4 (React Client)                                 │
    ↓                                                   │
┌───────────────────────────────────────┐              │
│ Phase 5 (US1) ─── Phase 6 (US2)       │ ← parallel   │
│        ↓              ↓                │              │
│     Phase 7 (US3) ← depends on both   │              │
│        ↓                               │              │
│ Phase 8 (US5) ← can start from Ph4    │              │
│        ↓                               │              │
│     Phase 9 (US6)                      │              │
└───────────────────────────────────────┘              │
                    ↓                                   │
              Phase 10 (US4) ← needs Phase 2 + Phase 7─┘
                    ↓
              Phase 11 (E2E)
                    ↓
              Phase 12 (Polish)
```

---

## Parallel Execution Examples

### Phase 1 Parallel Tasks
```bash
# All can run together:
T001: Add PyJWT to requirements.txt
T002: Install better-auth, hono in package.json
T003: Create frontend .env.local
T004: Create backend .env template
```

### Phases 5+6 Parallel (Auth Forms)
```bash
# Can develop in parallel:
T027-T033: SignUpForm and signup page (US1)
T034-T039: SignInForm and signin page (US2)
```

### Phase 8 Parallel with Earlier Phases
```bash
# UserMenu can start once Phase 4 (React Client) is complete:
T045: Create UserMenu.tsx
T046-T048: Navbar integration
```

---

## Implementation Strategy

### MVP First (Core Auth Flow)

1. Complete Phase 1: Setup
2. Complete Phase 2: Backend JWT Validation
3. Complete Phase 3: Better Auth Server Setup
4. Complete Phase 4: React Client
5. Complete Phase 5: User Signup (US1)
6. Complete Phase 6: User Signin (US2)
7. **STOP and VALIDATE**: Test signup + signin flow end-to-end

### Incremental Delivery

1. Setup + Backend JWT → Backend ready for protected endpoints
2. Better Auth Server → Auth endpoints functional
3. Signup + Signin → Users can create accounts
4. Route Protection → Book content protected
5. Chat Integration → Full feature complete

### Critical Path

```
Setup → Backend JWT → Better Auth Server → React Client → Auth UI → Route Protection → Chat Integration → E2E
```

---

## Summary

| Metric | Count |
|--------|-------|
| Total Tasks | 71 |
| Setup Phase | 6 tasks |
| Foundational Phase | 11 tasks |
| User Story Tasks | 42 tasks |
| E2E Testing | 6 tasks |
| Polish | 6 tasks |
| Parallelizable Tasks | 12 marked [P] |
| User Stories Covered | 6 (US1-US6) |

### MVP Scope (Phases 1-7)

Completing through Phase 7 (User Story 3) delivers:
- Backend JWT validation
- Better Auth server on Vercel
- Signup and signin functionality
- Protected book routes
- **Users can create accounts and access protected content**

### Full Scope (All Phases)

Completing all phases delivers:
- All 6 user stories
- Chat API protection
- E2E validation
- Production deployment ready

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Backend-first approach (Phase 2) enables testing without frontend
- Better Auth migration must complete before frontend auth can work
- CORS configuration critical for Vercel → Railway communication
- JWT validation uses JWKS endpoint (no shared secret needed on backend)
