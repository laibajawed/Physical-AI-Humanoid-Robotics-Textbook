# Quickstart: Authentication Integration

**Feature**: 007-authentication-integration
**Date**: 2025-12-23

This guide covers local development setup for the authentication integration.

---

## Prerequisites

- Node.js 18+ (for frontend/Better Auth)
- Python 3.11+ (for backend)
- pnpm or npm
- Access to Neon Postgres database

---

## 1. Environment Setup

### Frontend (.env.local)

Create `physical-ai-robotics-book/.env.local`:

```bash
# Better Auth Configuration
BETTER_AUTH_SECRET=your-32-character-secret-key-here
BETTER_AUTH_URL=http://localhost:3000

# Database (same as backend)
DATABASE_URL=postgresql://user:pass@your-neon-host.neon.tech/dbname?sslmode=require
```

### Backend (.env)

Add to `backend/.env`:

```bash
# Existing variables...
DATABASE_URL=postgresql://user:pass@your-neon-host.neon.tech/dbname?sslmode=require

# New: Better Auth URL for JWKS validation
BETTER_AUTH_URL=http://localhost:3000
```

---

## 2. Install Dependencies

### Frontend

```bash
cd physical-ai-robotics-book

# Install Better Auth and Hono
pnpm add better-auth hono @hono/node-server
# OR
npm install better-auth hono @hono/node-server
```

### Backend

```bash
cd backend

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR
.\.venv\Scripts\activate   # Windows

# Install PyJWT
pip install PyJWT>=2.8.0

# Update requirements.txt
echo "PyJWT>=2.8.0" >> requirements.txt
```

---

## 3. Database Migration

Run Better Auth CLI to create auth tables:

```bash
cd physical-ai-robotics-book

# Generate migration (review first)
npx @better-auth/cli generate

# Apply migration
npx @better-auth/cli migrate
```

Verify tables created:
```sql
-- Connect to Neon and run:
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('user', 'session', 'account');
```

---

## 4. Create Auth Configuration

### Frontend: `src/lib/auth.ts`

```typescript
import { betterAuth } from "better-auth";
import { Pool } from "pg";

export const auth = betterAuth({
    database: new Pool({
        connectionString: process.env.DATABASE_URL,
    }),
    emailAndPassword: {
        enabled: true,
        minPasswordLength: 8,
    },
    session: {
        cookieCache: {
            enabled: true,
            maxAge: 60 * 5, // 5 minutes
        },
    },
});
```

### Frontend: `src/lib/auth-client.ts`

```typescript
import { createAuthClient } from "better-auth/react";

export const authClient = createAuthClient({
    baseURL: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
});

export type Session = typeof authClient.$Infer.Session;
```

### API Route: `api/auth/[...all].ts`

```typescript
import { Hono } from "hono";
import { auth } from "../../src/lib/auth";

const app = new Hono();

app.on(["POST", "GET"], "/api/auth/*", (c) => {
    return auth.handler(c.req.raw);
});

export default app;
```

---

## 5. Create Backend Auth Module

### `backend/auth.py`

```python
"""JWT validation middleware for Better Auth tokens."""

import os
from functools import lru_cache
from typing import Dict

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import PyJWKClient

load_dotenv()

security = HTTPBearer(auto_error=False)

@lru_cache(maxsize=1)
def get_jwk_client() -> PyJWKClient:
    """Get cached JWKS client."""
    better_auth_url = os.getenv("BETTER_AUTH_URL", "http://localhost:3000")
    return PyJWKClient(
        f"{better_auth_url}/api/auth/jwks",
        cache_keys=True,
        lifespan=300,  # 5 minutes
    )

def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, str]:
    """
    Verify JWT token and extract user info.

    Returns:
        dict with user_id and email

    Raises:
        HTTPException 401 on invalid/expired token
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "UNAUTHORIZED",
                "message": "Authentication required",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        jwk_client = get_jwk_client()
        signing_key = jwk_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["EdDSA", "RS256"],
            options={"verify_aud": False},
        )

        user_id = payload.get("sub")
        email = payload.get("email", "")

        if not user_id:
            raise ValueError("Missing sub claim")

        return {"user_id": user_id, "email": email}

    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "TOKEN_EXPIRED",
                "message": "Token has expired. Please sign in again.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.exceptions.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_TOKEN",
                "message": "Invalid token",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
```

---

## 6. Protect Backend Endpoints

Modify `backend/app.py`:

```python
from auth import verify_jwt_token

# Add to protected endpoints:
@app.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    request: Request,
    chat_request: ChatRequest,
    current_user: dict = Depends(verify_jwt_token),  # Add this
) -> ChatResponse:
    # ... existing code ...
    # current_user["user_id"] and current_user["email"] available
```

---

## 7. Start Development Servers

### Terminal 1: Frontend

```bash
cd physical-ai-robotics-book
pnpm start
# Runs at http://localhost:3000
```

### Terminal 2: Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app:app --reload --port 8000
# Runs at http://localhost:8000
```

---

## 8. Test Authentication Flow

### Sign Up (via curl)

```bash
curl -X POST http://localhost:3000/api/auth/sign-up/email \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"password123"}' \
  -c cookies.txt
```

### Sign In

```bash
curl -X POST http://localhost:3000/api/auth/sign-in/email \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' \
  -c cookies.txt
```

### Get Session

```bash
curl http://localhost:3000/api/auth/session \
  -b cookies.txt
```

### Test Protected Backend Endpoint

```bash
# Extract JWT from cookie file and use as Bearer token
TOKEN=$(cat cookies.txt | grep better-auth | awk '{print $7}')

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"What is inverse kinematics?"}'
```

---

## 9. Common Issues

### Issue: JWKS endpoint returns 404

**Cause**: Better Auth not configured correctly
**Solution**: Verify `api/auth/[...all].ts` is properly exported and Vercel config has correct rewrites

### Issue: Token validation fails with "Invalid algorithm"

**Cause**: Algorithm mismatch between Better Auth and PyJWT
**Solution**: Ensure `algorithms=["EdDSA", "RS256"]` in PyJWT decode

### Issue: CORS errors on auth endpoints

**Cause**: Cross-origin requests blocked
**Solution**: Auth endpoints should be same-origin (Vercel); for development, ensure CORS middleware allows localhost:3000

### Issue: Database connection refused

**Cause**: Neon database SSL configuration
**Solution**: Ensure `?sslmode=require` in DATABASE_URL

---

## Next Steps

1. Create signin/signup UI components
2. Implement AuthGuard for protected routes
3. Modify ChatWidget to include JWT in requests
4. Add user menu to navbar
5. Test full end-to-end flow
