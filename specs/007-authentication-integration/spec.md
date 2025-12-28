# Feature Specification: Authentication Integration for Protected Book and Chatbot Access

**Feature Branch**: `007-authentication-integration`
**Created**: 2025-12-23
**Updated**: 2025-12-23
**Status**: Ready for Planning

**Input**: User description: "Implement Signup and Signin using Better Auth, backed by Neon Postgres. Enforce authentication only for protected resources: book content and embedded RAG chatbot. Public homepage remains accessible without login."

---

## Architecture Decision: Better Auth on Vercel Serverless + FastAPI JWT Validation

### Problem Statement

Better Auth is a **TypeScript-only** authentication framework. The project uses:
- **Frontend**: Docusaurus (TypeScript/React) - deployed on Vercel
- **Backend**: FastAPI (Python) - deployed on Railway (free $5/month plan)

Docusaurus is a static site generator without native API routes. Better Auth requires a server runtime.

### Chosen Architecture

**Solution**: Better Auth runs as a Vercel Serverless Function (Hono) at `/api/auth/*`, on the same domain as the Docusaurus frontend. FastAPI validates JWTs using Better Auth's JWKS endpoint (asymmetric key validation).

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Authentication Architecture                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                        VERCEL (Free Tier)                           │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  ┌──────────────────┐    ┌─────────────────────────────┐    │   │
│   │  │   Docusaurus     │    │   /api/auth/* (Serverless)  │    │   │
│   │  │   Static Site    │───▶│   Better Auth + Hono        │    │   │
│   │  │   React Frontend │    │   Same domain = no CORS     │    │   │
│   │  └──────────────────┘    └──────────────┬──────────────┘    │   │
│   └─────────────────────────────────────────│───────────────────┘   │
│                                             │                        │
│                                             │ Authorization: Bearer  │
│                                             ▼                        │
│   ┌─────────────────────┐           ┌──────────────┐                │
│   │   Neon Postgres     │◀─────────▶│   Railway    │                │
│   │   (Free Tier)       │           │   FastAPI    │                │
│   │   - user table      │           │   (Free $5)  │                │
│   │   - session table   │           │   Validates  │                │
│   │   - account table   │           │   JWT only   │                │
│   │   - sessions (chat) │           └──────────────┘                │
│   │   - conversations   │                                           │
│   └─────────────────────┘                                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

| Factor | Vercel Serverless | Alternative: Railway Service |
|--------|-------------------|------------------------------|
| Cost | $0 (Vercel free tier) | Uses Railway $5 credit |
| CORS | None (same domain) | Required (cross-domain) |
| Cold starts | Yes (~200ms) | None |
| Railway usage | FastAPI only | Would need 2 services |
| Cookie handling | Native (same origin) | Complex (cross-domain) |
| Free tier fit | Excellent | Tight on $5/month |

### Configuration Requirements

1. **JWKS Validation**: FastAPI validates JWTs using Better Auth's public JWKS endpoint (`/api/auth/jwks`) - no shared secret needed on backend
2. **Session Strategy**: Better Auth uses JWT-based sessions with cookie storage
3. **Database**: Better Auth uses Neon Postgres (same database as existing chat sessions)
4. **Token Passing**: Frontend reads JWT from Better Auth cookie and sends as `Authorization: Bearer <token>` to FastAPI

---

## User Scenarios & Testing _(mandatory)_

### User Story 1 - User Signup (Priority: P1)

As a new visitor, I want to create an account with my email and password so that I can access the protected book content and chatbot.

**Why this priority**: Account creation is the gateway to all protected features. Without signup, no user can access the book.

**Independent Test**: Navigate to signup page, enter valid email/password, submit, verify account created and session established.

**Acceptance Scenarios**:

1. **Given** I am on the homepage (unauthenticated), **When** I click "Sign Up", **Then** I am navigated to a signup form.
2. **Given** I am on the signup form, **When** I enter a valid email and password (8+ chars), **Then** my account is created, I am automatically signed in, and redirected to `/docs/introduction`.
3. **Given** I submit signup with an email that already exists, **When** the server responds, **Then** I see an error: "An account with this email already exists."
4. **Given** I submit signup with a password < 8 characters, **When** validation runs, **Then** I see an error: "Password must be at least 8 characters."

---

### User Story 2 - User Signin (Priority: P1)

As a returning user, I want to sign in with my email and password so that I can access my book content and chatbot.

**Why this priority**: Signin enables returning users to access protected content.

**Independent Test**: Navigate to signin page, enter valid credentials, submit, verify redirected to book content with session active.

**Acceptance Scenarios**:

1. **Given** I am on the signin page, **When** I enter valid credentials and submit, **Then** I am signed in and redirected to the book.
2. **Given** I enter an incorrect password, **When** I submit, **Then** I see an error: "Invalid email or password."
3. **Given** I enter an email that doesn't exist, **When** I submit, **Then** I see the same generic error: "Invalid email or password." (no email enumeration)
4. **Given** I successfully sign in with "Remember me" checked, **When** I close and reopen the browser, **Then** I remain signed in.

---

### User Story 3 - Access Protected Book Content (Priority: P1)

As an authenticated user, I want to access the book content pages so that I can read the Physical AI & Humanoid Robotics textbook.

**Why this priority**: The book content is the primary value proposition. Protection ensures only registered users access it.

**Independent Test**: Sign in, navigate to any `/docs/*` page, verify content renders. Sign out, try same URL, verify redirect to signin.

**Acceptance Scenarios**:

1. **Given** I am signed in, **When** I navigate to `/docs/introduction`, **Then** I see the book content.
2. **Given** I am NOT signed in, **When** I navigate to `/docs/introduction`, **Then** I am redirected to `/auth/signin?redirect=/docs/introduction`.
3. **Given** I am redirected to signin with a `redirect` param, **When** I successfully sign in, **Then** I am returned to the originally requested page.
4. **Given** I am signed in, **When** I click internal links between book pages, **Then** navigation works without re-authentication.

---

### User Story 4 - Access Protected Chatbot (Priority: P1)

As an authenticated user, I want to use the RAG chatbot so that I can ask questions about the book content.

**Why this priority**: The chatbot is a key feature that differentiates this product. Protection ties chatbot usage to registered users.

**Independent Test**: Sign in, open chat widget, send a question, verify response received. Sign out, try to send a message, verify error or redirect.

**Acceptance Scenarios**:

1. **Given** I am signed in, **When** I open the chat widget and submit a question, **Then** my request is authenticated and I receive a response.
2. **Given** I am NOT signed in, **When** I click the chat widget, **Then** I see a prompt: "Sign in to use the assistant" with a signin link.
3. **Given** my session expires while the chat is open, **When** I submit a question, **Then** I see: "Session expired. Please sign in again." with a signin link.
4. **Given** I am signed in, **When** the FastAPI backend receives my chat request, **Then** the request includes a valid JWT and is processed.

---

### User Story 5 - Public Homepage Access (Priority: P1)

As any visitor (authenticated or not), I want to access the public homepage without signing in so that I can learn about the book before creating an account.

**Why this priority**: The homepage serves as a marketing/landing page. Requiring login would hurt discoverability.

**Independent Test**: Clear all cookies, navigate to `/`, verify homepage loads without redirect.

**Acceptance Scenarios**:

1. **Given** I am NOT signed in, **When** I navigate to `/` (homepage), **Then** the page loads normally without any redirect.
2. **Given** I am NOT signed in, **When** I am on the homepage, **Then** I see "Sign In" and "Sign Up" navigation links.
3. **Given** I AM signed in, **When** I navigate to the homepage, **Then** I see my email/avatar and a "Sign Out" option in the navigation.
4. **Given** I am on the homepage, **When** I click any book link (e.g., "Read the Book"), **Then** I am taken to the signin page with redirect preserved.

---

### User Story 6 - User Signout (Priority: P2)

As a signed-in user, I want to sign out so that I can secure my session on shared devices.

**Why this priority**: Essential for security but not blocking core functionality.

**Independent Test**: Sign in, click Sign Out, verify session cleared, try to access protected page, verify redirect to signin.

**Acceptance Scenarios**:

1. **Given** I am signed in, **When** I click "Sign Out" in the navigation, **Then** my session is terminated.
2. **Given** I sign out, **When** I try to access `/docs/introduction`, **Then** I am redirected to signin.
3. **Given** I sign out, **When** my browser sends any request to FastAPI, **Then** the request is rejected with 401 Unauthorized.

---

### Edge Cases

| Edge Case | Behavior |
|-----------|----------|
| User navigates directly to protected URL while unauthenticated | Redirect to `/auth/signin?redirect={original_url}` |
| Session token expires | Frontend shows session expired message; redirect to signin |
| FastAPI receives request with expired JWT | Return 401 with `error_code: TOKEN_EXPIRED` |
| FastAPI receives request with invalid JWT signature | Return 401 with `error_code: INVALID_TOKEN` |
| User opens multiple browser tabs | All tabs share the same session (cookie-based) |
| User clears cookies while on protected page | Next navigation or API call triggers re-auth flow |
| Better Auth database is unavailable | Signin/signup fail with 503; existing valid JWTs still work on FastAPI |
| User tries signup with disposable email | Allow (no email domain restrictions in v1) |
| CORS error on auth endpoints | Display: "Authentication service unavailable. Please try again." |
| JWKS endpoint unavailable | FastAPI uses cached keys; if cache expires, requests fail with 401 until endpoint recovers |

---

## API Contracts _(mandatory)_

### Better Auth Endpoints (Vercel Functions)

Better Auth auto-generates these endpoints at `/api/auth/*`:

```typescript
// Signup endpoint (auto-generated by Better Auth)
POST /api/auth/sign-up/email
Request: {
  email: string;        // Valid email format
  password: string;     // 8-128 characters
  name?: string;        // Optional display name
}
Response (Success): {
  user: {
    id: string;         // UUID
    email: string;
    name: string | null;
    createdAt: string;  // ISO 8601
  };
  session: {
    id: string;
    expiresAt: string;
  };
}
Response (Error 400): {
  error: {
    code: string;       // e.g., "USER_ALREADY_EXISTS"
    message: string;
  };
}

// Signin endpoint (auto-generated by Better Auth)
POST /api/auth/sign-in/email
Request: {
  email: string;
  password: string;
  rememberMe?: boolean; // Default: false
}
Response (Success): { user, session } // Same as signup
Response (Error 401): {
  error: {
    code: "INVALID_CREDENTIALS";
    message: "Invalid email or password";
  };
}

// Signout endpoint (auto-generated by Better Auth)
POST /api/auth/sign-out
Response (Success): { success: true }

// Get session endpoint (auto-generated by Better Auth)
GET /api/auth/session
Response (Authenticated): {
  user: { id, email, name, createdAt };
  session: { id, expiresAt };
}
Response (Unauthenticated): null
```

### FastAPI Protected Endpoints

Existing endpoints with authentication added:

```python
# Request headers for authenticated requests
Authorization: Bearer <jwt_token>
# OR via cookie (preferred for browser requests):
Cookie: better-auth.session_token=<jwt_token>

# Modified chat endpoint
POST /chat
Request: ChatRequest (unchanged)
Response (Authenticated): ChatResponse (unchanged)
Response (401): {
  "error_code": "UNAUTHORIZED",
  "message": "Authentication required",
  "request_id": "uuid"
}

# Modified streaming endpoint
POST /chat/stream
Response (401): SSE event: { "type": "error", "error_code": "UNAUTHORIZED" }

# Modified history endpoint
GET /history/{session_id}
Response (401): Same as /chat

# Health endpoint remains public
GET /health
Response: HealthResponse (unchanged, no auth required)
```

### JWT Token Structure

```typescript
// JWT payload (encoded by Better Auth, decoded by FastAPI)
interface JWTPayload {
  sub: string;          // User ID (UUID)
  email: string;        // User email
  iat: number;          // Issued at (Unix timestamp)
  exp: number;          // Expires at (Unix timestamp)
  // Better Auth adds additional fields based on configuration
}
```

### Frontend Types

```typescript
// Auth state in React
interface AuthState {
  user: User | null;
  session: Session | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface User {
  id: string;
  email: string;
  name: string | null;
  createdAt: Date;
}

interface Session {
  id: string;
  expiresAt: Date;
}

// Auth context hook return type
interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name?: string) => Promise<void>;
  signOut: () => Promise<void>;
  error: string | null;
}
```

---

## Error-to-UI Mapping _(mandatory)_

| Error Code | HTTP Status | User Message | Action |
|------------|-------------|--------------|--------|
| `USER_ALREADY_EXISTS` | 400 | "An account with this email already exists." | Show signin link |
| `INVALID_CREDENTIALS` | 401 | "Invalid email or password." | Clear password field |
| `WEAK_PASSWORD` | 400 | "Password must be at least 8 characters." | Focus password field |
| `INVALID_EMAIL` | 400 | "Please enter a valid email address." | Focus email field |
| `UNAUTHORIZED` | 401 | "Please sign in to continue." | Redirect to signin |
| `TOKEN_EXPIRED` | 401 | "Your session has expired. Please sign in again." | Redirect to signin |
| `INVALID_TOKEN` | 401 | "Authentication error. Please sign in again." | Clear session, redirect |
| `RATE_LIMITED` | 429 | "Too many attempts. Please wait a moment." | Disable form for 30s |
| `SERVICE_UNAVAILABLE` | 503 | "Authentication service unavailable. Please try again." | Show retry button |

---

## Requirements _(mandatory)_

### Functional Requirements

**Better Auth Setup (Frontend)**

- **FR-001**: System MUST install and configure Better Auth on the Docusaurus frontend.
- **FR-002**: System MUST create Better Auth API route handler at `/api/auth/[...all].ts`.
- **FR-003**: System MUST configure Better Auth to use Neon Postgres as the database.
- **FR-004**: System MUST configure Better Auth to use JWT-based sessions with cookie storage.
- **FR-005**: System MUST create user, session, and account tables in Neon Postgres via Better Auth migrations.

**Authentication UI**

- **FR-006**: System MUST implement a signup page at `/auth/signup` with email, password, and optional name fields.
- **FR-007**: System MUST implement a signin page at `/auth/signin` with email and password fields.
- **FR-008**: System MUST display auth status (signed in/out) in the Docusaurus navbar.
- **FR-009**: System MUST provide a "Sign Out" button for authenticated users.
- **FR-010**: System MUST redirect users to the originally requested URL after successful signin (via `redirect` query param).

**Route Protection (Frontend)**

- **FR-011**: System MUST protect all `/docs/*` routes, redirecting unauthenticated users to signin.
- **FR-012**: System MUST allow unauthenticated access to `/` (homepage).
- **FR-013**: System MUST allow unauthenticated access to `/auth/*` routes (signin, signup).
- **FR-014**: System MUST check authentication state before rendering protected pages.

**Chatbot Protection (Frontend)**

- **FR-015**: System MUST check authentication before allowing chat widget interaction.
- **FR-016**: System MUST display "Sign in to use the assistant" for unauthenticated users clicking the chat widget.
- **FR-017**: System MUST read the JWT from Better Auth cookie and include it as `Authorization: Bearer <token>` header in all chat API requests (required for cross-domain Vercel→Railway communication).

**FastAPI JWT Validation (Backend)**

- **FR-018**: System MUST implement JWT validation middleware using Better Auth's JWKS endpoint.
- **FR-019**: System MUST validate JWT signature, expiration, and required claims.
- **FR-020**: System MUST protect `/chat`, `/chat/stream`, and `/history/{session_id}` endpoints.
- **FR-021**: System MUST NOT protect the `/health` endpoint.
- **FR-022**: System MUST return 401 Unauthorized with structured error response for invalid tokens.
- **FR-023**: System MUST extract user_id from JWT and make it available to request handlers.

**Database Schema**

- **FR-024**: System MUST create `user` table with columns: id, name, email, emailVerified, image, createdAt, updatedAt.
- **FR-025**: System MUST create `session` table with columns: id, userId, token, expiresAt, ipAddress, userAgent.
- **FR-026**: System MUST create `account` table for credential storage.
- **FR-027**: System MUST NOT interfere with existing `sessions` and `conversations` tables (chat history).

---

### Non-Functional Requirements

**Security**

- **NFR-001**: Passwords MUST be hashed using scrypt (Better Auth default).
- **NFR-002**: JWT tokens MUST expire based on "Remember Me" setting: 1 hour (OFF) or 30 days (ON).
- **NFR-003**: HTTPS MUST be enforced for all auth endpoints in production.
- **NFR-004**: CORS MUST be configured to allow only known frontend origins.
- **NFR-005**: Error messages MUST NOT leak information about whether an email exists (no enumeration).

**Performance**

- **NFR-006**: JWT validation on FastAPI MUST complete in < 10ms p95 (no database call).
- **NFR-007**: Signin/signup requests MUST complete in < 2 seconds.
- **NFR-008**: Auth state check on page load MUST complete in < 500ms.

**Reliability**

- **NFR-009**: If Better Auth database is unavailable, existing valid JWTs MUST still work on FastAPI.
- **NFR-010**: Session expiration MUST be handled gracefully with clear user messaging.

---

## Success Criteria _(mandatory)_

### Measurable Outcomes

| ID | Criterion | Measurement Method |
|----|-----------|-------------------|
| **SC-001** | User can create account and sign in within 30 seconds | Manual test: time full signup + signin flow |
| **SC-002** | 100% of `/docs/*` pages redirect unauthenticated users to signin | Automated test: request each docs page without cookie |
| **SC-003** | Homepage (`/`) loads without authentication | Automated test: request `/` without cookie, verify 200 |
| **SC-004** | Chat requests with valid JWT return responses | Automated test: send chat request with valid token |
| **SC-005** | Chat requests without JWT return 401 | Automated test: send chat request without token |
| **SC-006** | JWT validation adds < 10ms to request latency | Performance test: measure p95 latency with/without auth |
| **SC-007** | Invalid/expired tokens are rejected | Automated test: send requests with expired/tampered tokens |
| **SC-008** | Users remain signed in across browser sessions | Manual test: sign in, close browser, reopen, verify session |

---

## Test Scenarios _(mandatory)_

| # | Scenario | Steps | Expected Result |
|---|----------|-------|-----------------|
| 1 | New User Signup | Navigate to `/auth/signup` → Enter email/password → Submit | Account created, redirected to `/docs/introduction` |
| 2 | Existing User Signin | Navigate to `/auth/signin` → Enter valid credentials → Submit | Signed in, redirected to book |
| 3 | Invalid Signin | Navigate to `/auth/signin` → Enter wrong password → Submit | Error: "Invalid email or password" |
| 4 | Protected Page Access | Sign out → Navigate to `/docs/introduction` | Redirected to signin with redirect param |
| 5 | Post-Signin Redirect | Signin from redirect → Successfully authenticate | Returned to original `/docs/introduction` URL |
| 6 | Chat Without Auth | Open chat widget while signed out | "Sign in to use the assistant" message |
| 7 | Chat With Auth | Sign in → Open chat → Send question | Response received successfully |
| 8 | FastAPI Token Validation | Send chat request without Authorization header | 401 Unauthorized response |
| 9 | Expired Token | Use token with past expiration | 401 with "session expired" message |
| 10 | Signout | Click Sign Out → Try protected page | Session cleared, redirected to signin |
| 11 | Homepage Public Access | Clear cookies → Navigate to `/` | Homepage loads, no redirect |

---

## Constraints

### Frontend Constraints

- **FC-001**: Frontend framework: Docusaurus 3.9.2 with React 19.0.0
- **FC-002**: Authentication library: Better Auth (latest version)
- **FC-003**: Better Auth API routes via Docusaurus plugin or custom pages
- **FC-004**: Auth state management via Better Auth React client
- **FC-005**: No additional auth UI libraries required

### Backend Constraints

- **BC-001**: Backend framework: FastAPI with Python 3.11+
- **BC-002**: JWT validation: PyJWT or python-jose library
- **BC-003**: No Better Auth Python SDK available (JWT validation only)
- **BC-004**: Existing endpoints remain backward compatible
- **BC-005**: Add new `auth.py` module for JWT validation logic

### Database Constraints

- **DC-001**: Database: Neon Serverless Postgres (existing)
- **DC-002**: Better Auth tables created via CLI migration
- **DC-003**: Existing chat tables (`sessions`, `conversations`) remain unchanged
- **DC-004**: Schema prefix or separate schema not required (tables coexist)

### Environment Constraints

- **EC-001**: `BETTER_AUTH_SECRET`: Secret for JWT signing (32+ chars, frontend only)
- **EC-002**: `BETTER_AUTH_URL`: Frontend URL used by backend for JWKS endpoint discovery (e.g., `https://your-site.vercel.app`)
- **EC-003**: `DATABASE_URL`: Neon Postgres connection string (already exists)
- **EC-004**: Frontend env vars set in Vercel dashboard
- **EC-005**: Backend env vars set in Railway dashboard

### Integration Constraints

- **IC-001**: JWT tokens passed via `better-auth.session_token` cookie (browser requests)
- **IC-002**: JWT tokens can also be passed via `Authorization: Bearer <token>` header (API clients)
- **IC-003**: FastAPI validates JWT using Better Auth's JWKS endpoint (asymmetric validation)
- **IC-004**: No cross-service API calls for authentication validation

---

## File Structure

### Frontend Additions (Vercel Project)

```
physical-ai-robotics-book/
├── api/                            # Vercel Serverless Functions directory
│   └── auth/
│       └── [...all].ts             # Better Auth + Hono handler (catches /api/auth/*)
├── src/
│   ├── lib/
│   │   ├── auth.ts                 # Better Auth server configuration
│   │   └── auth-client.ts          # Better Auth React client
│   ├── components/
│   │   ├── Auth/
│   │   │   ├── SignInForm.tsx      # Signin form component
│   │   │   ├── SignUpForm.tsx      # Signup form component
│   │   │   ├── AuthGuard.tsx       # Route protection wrapper
│   │   │   └── UserMenu.tsx        # Navbar user dropdown
│   │   └── Chat/
│   │       └── ChatWidget.tsx      # Modified to check auth & pass JWT
│   ├── hooks/
│   │   └── useAuth.ts              # Auth state hook (wraps Better Auth client)
│   └── theme/
│       └── Navbar/
│           └── index.tsx           # Modified to show auth state
├── vercel.json                     # Vercel config (rewrites for /api/auth/*)
└── .env.local                      # Local env vars (BETTER_AUTH_SECRET, DATABASE_URL)
```

### Backend Additions (Railway)

```
backend/
├── auth.py                         # JWT validation middleware (PyJWT)
├── app.py                          # Modified to use auth middleware on protected routes
├── models/
│   └── auth.py                     # Auth-related models (TokenPayload, AuthenticatedUser)
├── requirements.txt                # Add PyJWT>=2.8.0
└── .env                            # Add BETTER_AUTH_SECRET (same as Vercel)
```

### New Dependencies

**Frontend (package.json)**:
```json
{
  "better-auth": "^1.x.x",
  "hono": "^4.x.x"
}
```

**Backend (requirements.txt)**:
```
PyJWT>=2.8.0
```

---

## Assumptions

- **RISK**: Better Auth React 19 compatibility unverified. Mitigation: Test in Phase 3 (T002a); fallback to React 18 if issues arise.
- Neon Postgres can handle additional auth tables without performance impact.
- Vercel serverless functions can run Better Auth API routes.
- JWT validation in Python is straightforward with standard libraries (PyJWT).
- The shared secret approach is secure for this use case (not multi-tenant).
- Browser cookie handling works correctly across Vercel (frontend) and Railway (backend) domains.
- CORS is already configured to allow credentials (existing setup in `backend/app.py`).

---

## Not Building (Out of Scope)

**Advanced Authentication Features**
- Social login providers (Google, GitHub, etc.)
- Multi-factor authentication (2FA)
- Passwordless/magic link authentication
- Passkey/WebAuthn support
- Email verification (not required - users access immediately after signup)
- Password reset flow (deferred to v2)

**Authorization & Permissions**
- Role-based access control (RBAC)
- Admin vs. user roles
- Per-page or per-chapter access control
- Subscription tiers or paywalls

**User Management**
- User profile pages
- Account settings
- Avatar upload
- Email change
- Password change UI

**Session Management**
- Multiple device session management
- Session revocation UI
- Login history

**Infrastructure**
- Auth service monitoring dashboard
- Rate limiting per user
- Audit logging
- GDPR compliance features (data export, deletion)

---

## Clarifications & Decisions

### Session 2025-12-23

- Q: How should JWT tokens be transmitted from browser to FastAPI backend (cross-domain)? → A: Frontend reads JWT cookie and adds `Authorization: Bearer <token>` header to FastAPI requests.
- Q: Where should users be redirected after successful signup? → A: Redirect to `/docs/introduction` (book start).
- Q: Is email verification required before accessing protected content? → A: No, users can access immediately after signup (reduces friction for MVP).
- Q: What should session duration be based on "Remember Me" setting? → A: Remember Me OFF: 1 hour (browser session), Remember Me ON: 30 days.
- Q: Where should Better Auth run given Docusaurus has no API routes and Railway free tier is limited? → A: Vercel Serverless Functions (same domain as frontend, no CORS, generous free tier).

### Why Better Auth + FastAPI Hybrid?

**Decision**: Use Better Auth on frontend with JWT validation on FastAPI backend.

**Rationale**:
- Better Auth is TypeScript-only; no native Python support exists
- Adding a separate Node.js auth service increases complexity and cost
- JWT validation is stateless and fast (no database call on each request)
- Shared secret approach works well for single-tenant applications

**Trade-offs**:
- Session revocation requires short token expiry (not instant)
- User data queries from FastAPI require direct database access

### Cookie vs. Header Token Passing

**Decision**: Support both cookie and Authorization header.

**Rationale**:
- Cookies work automatically for browser requests (chat widget)
- Authorization header useful for API testing and potential mobile apps
- Better Auth sets cookies by default; frontend doesn't need changes for browser flow

### Protected vs. Public Routes

**Decision**: Only `/docs/*` and chat API require authentication.

**Rationale**:
- Homepage serves as marketing/landing page
- Auth pages must be accessible to unauthenticated users
- Health endpoint must remain public for monitoring
- This matches the user's requirements exactly

### Database Schema Coexistence

**Decision**: Better Auth tables coexist with chat tables in the same database.

**Rationale**:
- Simplifies deployment (one database connection string)
- No schema conflicts (Better Auth uses `user`, `session`, `account`; chat uses `sessions`, `conversations`)
- Can query user data directly from FastAPI if needed

---

## Dependencies

### Frontend Dependencies (to add)

```json
{
  "better-auth": "^1.x.x",
  "hono": "^4.x.x",
  "@hono/node-server": "^1.x.x"
}
```

### Backend Dependencies (to add)

```
PyJWT>=2.8.0
```

### Infrastructure (all free tier)

| Service | Purpose | Cost |
|---------|---------|------|
| Vercel | Docusaurus static site + Better Auth serverless functions | $0 |
| Railway | FastAPI backend | $0 (within $5 credit) |
| Neon | PostgreSQL database (auth tables + chat tables) | $0 |

---

## References

- Better Auth documentation: https://www.better-auth.com/docs
- Better Auth GitHub: https://github.com/better-auth/better-auth
- Existing backend: `backend/app.py`
- Existing chat integration: `specs/006-chatkit-frontend/spec.md`
- Docusaurus config: `physical-ai-robotics-book/docusaurus.config.ts`
- Neon Postgres setup: `backend/db.py`
