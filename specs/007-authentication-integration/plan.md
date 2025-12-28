# Implementation Plan: Authentication Integration

**Branch**: `007-authentication-integration` | **Date**: 2025-12-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-authentication-integration/spec.md`

---

## Summary

Implement email/password authentication using Better Auth on Vercel Serverless Functions (Hono) with JWT validation in the FastAPI backend (Railway). Protect `/docs/*` routes and chat API endpoints while keeping the homepage and health endpoints public.

**Architecture**: Better Auth (TypeScript/Hono) runs on Vercel at `/api/auth/*`, sharing the Neon Postgres database. FastAPI validates JWTs using Better Auth's JWKS endpoint, enabling stateless authentication without cross-service API calls.

---

## Technical Context

**Language/Version**: TypeScript 5.0+ (frontend), Python 3.11+ (backend)
**Primary Dependencies**:
- Frontend: Better Auth ^1.x, Hono ^4.x, React 19.0.0, Docusaurus 3.9.2
- Backend: FastAPI (existing), PyJWT ^2.8.0

**Storage**: Neon Serverless Postgres (existing + 3 new auth tables)
**Testing**: Vitest (frontend), pytest (backend)
**Target Platform**: Vercel (frontend), Railway (backend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: JWT validation < 10ms, signin/signup < 2 seconds
**Constraints**: Free tier limits (Vercel, Railway $5 credit, Neon)
**Scale/Scope**: Single-tenant, ~100 concurrent users expected

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| CODE QUALITY | ✅ Pass | TypeScript strict mode, component-based React |
| USER EXPERIENCE | ✅ Pass | Mobile-first auth pages, clear error messages |
| CONTENT ORGANIZATION | ✅ Pass | Auth pages at `/auth/*`, protected content at `/docs/*` |
| DESIGN STANDARDS | ✅ Pass | Using Tailwind CSS v4, consistent with existing UI |

**Gate Status**: PASSED - No violations requiring justification.

---

## Project Structure

### Documentation (this feature)

```text
specs/007-authentication-integration/
├── spec.md                  # Feature specification (complete)
├── plan.md                  # This file
├── research.md              # Phase 0 output - research findings
├── data-model.md            # Phase 1 output - database schema
├── quickstart.md            # Phase 1 output - dev setup guide
├── contracts/
│   ├── auth-api.yaml        # Better Auth OpenAPI spec
│   └── protected-api.yaml   # FastAPI protected endpoints
└── tasks.md                 # Phase 2 output (via /sp.tasks)
```

### Source Code (repository root)

```text
# Frontend (Vercel deployment)
physical-ai-robotics-book/
├── api/                            # Vercel Serverless Functions
│   └── auth/
│       └── [...all].ts             # Better Auth + Hono handler
├── src/
│   ├── lib/
│   │   ├── auth.ts                 # Better Auth server config
│   │   └── auth-client.ts          # Better Auth React client
│   ├── components/
│   │   └── Auth/
│   │       ├── SignInForm.tsx      # Signin form
│   │       ├── SignUpForm.tsx      # Signup form
│   │       ├── AuthGuard.tsx       # Route protection wrapper
│   │       └── UserMenu.tsx        # Navbar user dropdown
│   ├── hooks/
│   │   └── useAuth.ts              # Auth state hook
│   ├── pages/
│   │   └── auth/
│   │       ├── signin.tsx          # Signin page
│   │       └── signup.tsx          # Signup page
│   ├── services/
│   │   └── chatApi.ts              # Modified to include JWT
│   └── theme/
│       └── Layout/
│           └── index.tsx           # Modified for auth guard
├── vercel.json                     # Vercel config (rewrites)
└── .env.local                      # Environment variables

# Backend (Railway deployment)
backend/
├── auth.py                         # JWT validation middleware (NEW)
├── models/
│   └── auth.py                     # Auth models (NEW)
├── app.py                          # Modified - add auth dependency
├── requirements.txt                # Add PyJWT
└── .env                            # Add BETTER_AUTH_URL
```

**Structure Decision**: Web application with frontend (Vercel) and backend (Railway) on separate domains. Better Auth runs as serverless functions on the same domain as the frontend to avoid CORS complexity for auth endpoints.

---

## Implementation Phases

### Phase 1: Backend JWT Validation (Backend-first approach)

**Goal**: FastAPI can validate Better Auth JWTs before frontend is ready.

**Tasks**:
1. **T1.1**: Add PyJWT to requirements.txt
2. **T1.2**: Create `backend/auth.py` with JWKS-based JWT validation
3. **T1.3**: Create `backend/models/auth.py` with TokenPayload, AuthenticatedUser
4. **T1.4**: Add `BETTER_AUTH_URL` environment variable support
5. **T1.5**: Create pytest tests for JWT validation (mocked JWKS)
6. **T1.6**: Protect `/chat`, `/chat/stream`, `/history/{session_id}` endpoints
7. **T1.7**: Ensure `/health` remains public
8. **T1.8**: Update error handling for 401 responses

**Acceptance**:
- [ ] `pytest tests/test_auth.py -v` passes
- [ ] Protected endpoints return 401 without token
- [ ] Health endpoint returns 200 without token

---

### Phase 2: Better Auth Server Setup (Vercel Functions)

**Goal**: Better Auth running on Vercel with database migrations.

**Tasks**:
1. **T2.1**: Install better-auth, hono, @hono/node-server
2. **T2.2**: Create `src/lib/auth.ts` with Better Auth configuration
3. **T2.3**: Create `api/auth/[...all].ts` Hono handler
4. **T2.4**: Configure vercel.json for `/api/auth/*` rewrites
5. **T2.5**: Run `npx @better-auth/cli migrate` to create auth tables
6. **T2.6**: Verify JWKS endpoint at `/api/auth/jwks`
7. **T2.7**: Test signup/signin via curl

**Acceptance**:
- [ ] `POST /api/auth/sign-up/email` creates user
- [ ] `POST /api/auth/sign-in/email` returns session
- [ ] `GET /api/auth/jwks` returns public keys
- [ ] Database has `user`, `session`, `account` tables

---

### Phase 3: Better Auth React Client

**Goal**: Frontend auth state management.

**Tasks**:
1. **T3.1**: Create `src/lib/auth-client.ts` with createAuthClient
2. **T3.2**: Create `src/hooks/useAuth.ts` wrapper hook
3. **T3.3**: Export auth types for use across components
4. **T3.4**: Test useSession hook in development

**Acceptance**:
- [ ] `useAuth()` returns user, isAuthenticated, isLoading
- [ ] Session persists across page refreshes

---

### Phase 4: Authentication UI Components

**Goal**: Signin and signup pages.

**Tasks**:
1. **T4.1**: Create `SignUpForm.tsx` with email/password/name fields
2. **T4.2**: Create `SignInForm.tsx` with email/password fields
3. **T4.3**: Create `src/pages/auth/signup.tsx` page
4. **T4.4**: Create `src/pages/auth/signin.tsx` page
5. **T4.5**: Implement form validation and error display
6. **T4.6**: Handle redirect parameter after successful auth
7. **T4.7**: Style forms with Tailwind CSS (mobile-first)

**Acceptance**:
- [ ] Signup form creates account and redirects
- [ ] Signin form authenticates and redirects
- [ ] Error messages display correctly
- [ ] Forms are mobile-responsive

---

### Phase 5: Route Protection

**Goal**: Protect `/docs/*` and integrate auth into layout.

**Tasks**:
1. **T5.1**: Create `AuthGuard.tsx` component
2. **T5.2**: Swizzle Docusaurus Layout component
3. **T5.3**: Add auth check to Layout for `/docs/*` routes
4. **T5.4**: Implement redirect to signin with return URL
5. **T5.5**: Create `UserMenu.tsx` for navbar
6. **T5.6**: Add signin/signup links for unauthenticated users
7. **T5.7**: Add user dropdown with signout for authenticated users

**Acceptance**:
- [ ] `/docs/*` redirects to signin when unauthenticated
- [ ] `/` (homepage) loads without signin
- [ ] Navbar shows auth state correctly
- [ ] Signout clears session and redirects

---

### Phase 6: Chat API Integration

**Goal**: Chat requests include JWT for authentication.

**Tasks**:
1. **T6.1**: Modify `chatApi.ts` to get JWT from auth client
2. **T6.2**: Add Authorization header to chat requests
3. **T6.3**: Handle 401 responses in chat (show signin prompt)
4. **T6.4**: Update ChatWidget to check auth before allowing interaction
5. **T6.5**: Show "Sign in to use assistant" for unauthenticated users

**Acceptance**:
- [ ] Chat requests include valid JWT
- [ ] 401 responses trigger signin prompt
- [ ] Unauthenticated users see signin message

---

### Phase 7: End-to-End Testing

**Goal**: Verify complete authentication flow.

**Tasks**:
1. **T7.1**: Manual test: signup → signin → access book → chat → signout
2. **T7.2**: Test session persistence across browser restart
3. **T7.3**: Test token expiration handling
4. **T7.4**: Test redirect flow (protected page → signin → return)
5. **T7.5**: Test error scenarios (wrong password, duplicate email)
6. **T7.6**: Performance test: JWT validation latency

**Acceptance**:
- [ ] All test scenarios pass
- [ ] JWT validation < 10ms (p95)
- [ ] No regressions in existing functionality

---

## Dependencies Between Phases

```
Phase 1 (Backend) ──┐
                    ├──► Phase 7 (E2E Testing)
Phase 2 (Auth Server) ──► Phase 3 (Client) ──► Phase 4 (UI) ──► Phase 5 (Protection) ──► Phase 6 (Chat) ──┘
```

- Phase 1 can start immediately (backend-first)
- Phase 2 must complete before Phase 3 (client needs server)
- Phase 3-6 are sequential (each builds on previous)
- Phase 7 requires all phases complete

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| React 19 + Better Auth incompatibility | Low | High | Test early in Phase 3; fallback to React 18 if needed |
| Vercel cold starts slow auth | Medium | Medium | Cookie caching enabled; acceptable for auth endpoints |
| JWKS endpoint unavailable | Low | High | PyJWKClient caches keys; monitor uptime |
| Neon free tier limits | Low | Medium | Auth tables are small; monitor usage |

---

## Environment Variables Summary

### Vercel (Frontend)
```
BETTER_AUTH_SECRET=<32+ chars>
BETTER_AUTH_URL=https://your-site.vercel.app
DATABASE_URL=postgresql://...
```

### Railway (Backend)
```
BETTER_AUTH_URL=https://your-site.vercel.app
DATABASE_URL=postgresql://... (existing)
```

---

## Deployment Checklist

- [ ] Vercel environment variables set
- [ ] Railway environment variables updated
- [ ] Database migration applied
- [ ] CORS origins updated for production domains
- [ ] HTTPS enforced (automatic on Vercel/Railway)
- [ ] Better Auth baseURL matches production URL

---

## References

- [spec.md](./spec.md) - Feature specification
- [research.md](./research.md) - Technology research findings
- [data-model.md](./data-model.md) - Database schema
- [quickstart.md](./quickstart.md) - Development setup guide
- [contracts/auth-api.yaml](./contracts/auth-api.yaml) - Better Auth OpenAPI
- [contracts/protected-api.yaml](./contracts/protected-api.yaml) - Protected API OpenAPI
