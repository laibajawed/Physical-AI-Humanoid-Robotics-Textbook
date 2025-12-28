# Research: Authentication Integration

**Feature**: 007-authentication-integration
**Date**: 2025-12-23
**Status**: Complete

---

## Research Questions & Findings

### 1. Better Auth + FastAPI Integration Pattern

**Question**: How to integrate Better Auth (TypeScript-only) with a FastAPI (Python) backend?

**Decision**: Use JWKS-based JWT validation in FastAPI

**Rationale**:
- Better Auth exposes a JWKS endpoint at `/api/auth/jwks`
- FastAPI validates JWTs using PyJWT with JWKS client
- This is the recommended pattern from the official Better Auth + Python FastAPI guide
- Stateless validation: no cross-service API calls needed per request

**Alternatives Considered**:
1. ~~Shared secret HMAC signing~~ - Less secure, requires secret synchronization
2. ~~Separate Node.js auth service~~ - Added complexity and cost
3. ~~Session tokens with database lookup~~ - Added latency, not stateless

**Implementation Pattern** (from Context7):
```python
from jwt import PyJWKClient
import jwt

def verify_jwt_token(token: str) -> Dict[str, str]:
    jwk_client = PyJWKClient(f"{BETTER_AUTH_URL}/api/auth/jwks")
    signing_key = jwk_client.get_signing_key_from_jwt(token)

    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["EdDSA", "RS256"],
        options={"verify_aud": False}
    )

    return {"user_id": payload.get("sub"), "email": payload.get("email")}
```

---

### 2. Better Auth on Vercel Serverless Functions

**Question**: How to run Better Auth without a dedicated Node.js server?

**Decision**: Use Hono framework with Vercel Serverless Functions

**Rationale**:
- Better Auth integrates seamlessly with Hono
- Vercel's `/api/` directory automatically deploys as serverless functions
- Same domain as Docusaurus frontend = no CORS complexity for auth endpoints
- Free tier is generous for auth workloads

**Implementation Pattern** (from Context7):
```typescript
// api/auth/[...all].ts
import { Hono } from "hono";
import { auth } from "../../src/lib/auth";

const app = new Hono();

app.on(["POST", "GET"], "/api/auth/*", (c) => {
    return auth.handler(c.req.raw);
});

export default app;
```

**Key Configuration**:
- Better Auth `baseURL` must match Vercel deployment URL
- Database adapter: PostgreSQL (Neon)
- Session strategy: JWT cookies with `cookieCache.enabled: true`

---

### 3. Better Auth Database Schema

**Question**: What tables does Better Auth require, and how do they coexist with existing chat tables?

**Decision**: Use Better Auth's default schema in the same Neon database

**Rationale**:
- Better Auth creates 3 core tables: `user`, `session`, `account`
- Existing chat tables use different names: `sessions`, `conversations`
- No naming conflicts; tables can coexist

**Schema Details** (from Context7):

**User Table**:
| Column | Type | Description |
|--------|------|-------------|
| id | string (UUID) | Primary key |
| name | string | User's display name |
| email | string (unique) | User's email |
| emailVerified | boolean | Verification status |
| image | string? | Profile image URL |
| createdAt | timestamp | Account creation time |
| updatedAt | timestamp | Last update time |

**Session Table**:
| Column | Type | Description |
|--------|------|-------------|
| id | string (UUID) | Primary key |
| userId | string (FK) | References user.id |
| token | string (unique) | Session token (JWT) |
| expiresAt | timestamp | Session expiration |
| ipAddress | string? | Client IP |
| userAgent | string? | Browser user agent |
| createdAt | timestamp | Session start |
| updatedAt | timestamp | Last activity |

**Account Table**:
| Column | Type | Description |
|--------|------|-------------|
| id | string (UUID) | Primary key |
| userId | string (FK) | References user.id |
| accountId | string | Provider account ID |
| providerId | string | Provider name (e.g., "credential") |
| accessToken | string? | OAuth access token |
| refreshToken | string? | OAuth refresh token |
| password | string? | Hashed password (credential auth) |
| createdAt | timestamp | Account link time |
| updatedAt | timestamp | Last update |

**Migration Command**:
```bash
npx @better-auth/cli migrate
```

---

### 4. PyJWT Token Validation

**Question**: How to validate JWTs in FastAPI using PyJWT?

**Decision**: Use PyJWKClient for JWKS-based validation with caching

**Rationale**:
- PyJWT 2.8+ supports JWKS clients natively
- Automatic key rotation handling
- Built-in caching (15-minute default) reduces JWKS endpoint calls

**Implementation Pattern** (from Context7):
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
import jwt

security = HTTPBearer()

# Cache JWKS client (module-level singleton)
_jwk_client = None

def get_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(
            f"{os.getenv('BETTER_AUTH_URL')}/api/auth/jwks",
            cache_keys=True,
            lifespan=300  # 5 minutes
        )
    return _jwk_client

def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, str]:
    token = credentials.credentials

    try:
        jwk_client = get_jwk_client()
        signing_key = jwk_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["EdDSA", "RS256"],
            options={"verify_aud": False}
        )

        user_id = payload.get("sub")
        email = payload.get("email", "")

        if not user_id:
            raise ValueError("Missing sub claim")

        return {"user_id": user_id, "email": email}

    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "TOKEN_EXPIRED", "message": "Token has expired"}
        )
    except jwt.exceptions.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "INVALID_TOKEN", "message": "Invalid token"}
        )
```

---

### 5. Better Auth React Client

**Question**: How to use Better Auth in React/Docusaurus frontend?

**Decision**: Use `createAuthClient` from `better-auth/react`

**Rationale**:
- Provides React hooks: `useSession`, `signIn.email`, `signUp.email`, `signOut`
- Automatic session management and cookie handling
- TypeScript types inferred from auth configuration

**Implementation Pattern** (from Context7):
```typescript
// src/lib/auth-client.ts
import { createAuthClient } from "better-auth/react";

export const authClient = createAuthClient({
    baseURL: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"
});

export type Session = typeof authClient.$Infer.Session;
```

**Usage in Components**:
```typescript
import { authClient } from "@/lib/auth-client";

// Sign up
const { data, error } = await authClient.signUp.email({
    name: "John Doe",
    email: "john@example.com",
    password: "password123"
});

// Sign in
const { data, error } = await authClient.signIn.email({
    email: "john@example.com",
    password: "password123",
    rememberMe: true
});

// Get session
const { useSession } = authClient;
const { data: session, isPending } = useSession();

// Sign out
await authClient.signOut();
```

---

### 6. Cross-Domain Token Passing (Vercel → Railway)

**Question**: How to pass JWT from browser to FastAPI on different domain?

**Decision**: Authorization Bearer header with JWT extracted from cookie

**Rationale**:
- Better Auth sets session cookie on Vercel domain
- Cross-domain cookie sharing requires SameSite=None + complex configuration
- Simpler: Frontend reads JWT and sends as Authorization header to FastAPI

**Implementation Pattern**:
```typescript
// Frontend: Extract JWT and send to FastAPI
async function callBackendAPI(endpoint: string, body: object) {
    const session = await authClient.getSession();
    const token = session?.session?.token; // JWT from Better Auth

    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify(body)
    });

    return response.json();
}
```

---

### 7. Docusaurus Route Protection

**Question**: How to protect `/docs/*` routes in Docusaurus?

**Decision**: Custom React wrapper component with auth check

**Rationale**:
- Docusaurus uses React for rendering
- Auth state available via Better Auth hooks
- Wrap protected pages with `AuthGuard` component

**Implementation Pattern**:
```typescript
// src/components/Auth/AuthGuard.tsx
import { useEffect } from 'react';
import { useRouter } from '@docusaurus/router';
import { authClient } from '@/lib/auth-client';

export function AuthGuard({ children }) {
    const { useSession } = authClient;
    const { data: session, isPending } = useSession();
    const router = useRouter();

    useEffect(() => {
        if (!isPending && !session) {
            router.push(`/auth/signin?redirect=${encodeURIComponent(window.location.pathname)}`);
        }
    }, [session, isPending, router]);

    if (isPending) {
        return <div>Loading...</div>;
    }

    if (!session) {
        return null;
    }

    return children;
}
```

**Docusaurus Integration**: Swizzle the Layout component to wrap protected routes.

---

## Technology Stack Summary

### Frontend (Vercel)
| Technology | Version | Purpose |
|------------|---------|---------|
| Docusaurus | 3.9.2 | Static site framework |
| React | 19.0.0 | UI library |
| Better Auth | ^1.x | Auth framework |
| Hono | ^4.x | Serverless function framework |

### Backend (Railway)
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | existing | API framework |
| PyJWT | ^2.8.0 | JWT validation |

### Database (Neon)
| Technology | Purpose |
|------------|---------|
| PostgreSQL | User data, sessions, chat history |

---

## Environment Variables

### Vercel (Frontend + Better Auth)
```
BETTER_AUTH_SECRET=<32+ character secret>
BETTER_AUTH_URL=https://your-site.vercel.app
DATABASE_URL=postgresql://...@neon.tech/...
```

### Railway (FastAPI Backend)
```
BETTER_AUTH_URL=https://your-site.vercel.app
```

Note: FastAPI uses JWKS endpoint for validation, not the shared secret directly.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| JWKS endpoint unavailable | PyJWKClient caches keys; existing sessions continue working |
| Token expiration during long chat | Frontend checks session before API calls; refresh if needed |
| React 19 compatibility with Better Auth | Better Auth supports React 19; test during implementation |
| Vercel cold starts on auth endpoints | Acceptable 200-300ms; cache session in client |

---

## References

- Better Auth Docs: https://www.better-auth.com/docs
- Better Auth + FastAPI Guide: Context7 `/hamza123545/how-to-use-better-auth-with-python-fast-api`
- Better Auth Hono Integration: Context7 `/www.better-auth.com/llmstxt`
- PyJWT Documentation: Context7 `/jpadilla/pyjwt`
