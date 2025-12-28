# Data Model: Authentication Integration

**Feature**: 007-authentication-integration
**Date**: 2025-12-23
**Status**: Complete

---

## Overview

This document defines the database schema for authentication. Better Auth manages the core auth tables (`user`, `session`, `account`), which coexist with existing chat tables (`sessions`, `conversations`) in the same Neon Postgres database.

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        BETTER AUTH TABLES                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐           │
│  │    user     │◄──────│   session   │       │   account   │           │
│  ├─────────────┤  1:N  ├─────────────┤       ├─────────────┤           │
│  │ id (PK)     │       │ id (PK)     │       │ id (PK)     │           │
│  │ name        │       │ userId (FK) │──────►│ userId (FK) │◄──────────┤
│  │ email (UQ)  │       │ token (UQ)  │       │ accountId   │  1:N      │
│  │ emailVerif. │       │ expiresAt   │       │ providerId  │           │
│  │ image       │       │ ipAddress   │       │ password    │           │
│  │ createdAt   │       │ userAgent   │       │ accessToken │           │
│  │ updatedAt   │       │ createdAt   │       │ refreshToken│           │
│  └─────────────┘       │ updatedAt   │       │ createdAt   │           │
│                        └─────────────┘       │ updatedAt   │           │
│                                              └─────────────┘           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     EXISTING CHAT TABLES (unchanged)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐       ┌────────────────┐                              │
│  │   sessions   │◄──────│ conversations  │                              │
│  ├──────────────┤  1:N  ├────────────────┤                              │
│  │ session_id   │       │ id (PK)        │                              │
│  │ (PK, UUID)   │       │ session_id(FK) │                              │
│  │ created_at   │       │ timestamp      │                              │
│  │ last_active  │       │ query          │                              │
│  └──────────────┘       │ response       │                              │
│                         │ sources (JSON) │                              │
│                         │ metadata(JSON) │                              │
│                         └────────────────┘                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Better Auth Tables

### user

Primary table for authenticated users. Created and managed by Better Auth.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string, auto-generated |
| `name` | VARCHAR(255) | NOT NULL | User's display name |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User's email address |
| `emailVerified` | BOOLEAN | DEFAULT false | Email verification status |
| `image` | TEXT | NULLABLE | Profile image URL |
| `createdAt` | TIMESTAMPTZ | DEFAULT NOW() | Account creation timestamp |
| `updatedAt` | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |

**Indexes**:
- `PRIMARY KEY (id)`
- `UNIQUE INDEX ON email`

**Validation Rules**:
- Email must be valid format (enforced by Better Auth)
- Name required on signup

---

### session

Active user sessions. Created on signin, deleted on signout or expiration.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `userId` | VARCHAR(36) | FK → user.id, NOT NULL | Owner of this session |
| `token` | TEXT | UNIQUE, NOT NULL | JWT session token |
| `expiresAt` | TIMESTAMPTZ | NOT NULL | Session expiration time |
| `ipAddress` | VARCHAR(45) | NULLABLE | Client IP (IPv4/IPv6) |
| `userAgent` | TEXT | NULLABLE | Browser user agent string |
| `createdAt` | TIMESTAMPTZ | DEFAULT NOW() | Session start time |
| `updatedAt` | TIMESTAMPTZ | DEFAULT NOW() | Last activity time |

**Indexes**:
- `PRIMARY KEY (id)`
- `UNIQUE INDEX ON token`
- `INDEX ON userId`
- `INDEX ON expiresAt` (for cleanup queries)

**Foreign Keys**:
- `userId` REFERENCES `user(id)` ON DELETE CASCADE

**Session Duration Rules**:
- `rememberMe: false` → 1 hour expiration
- `rememberMe: true` → 30 days expiration

---

### account

Credential storage for authentication methods. For email/password, stores hashed password.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `userId` | VARCHAR(36) | FK → user.id, NOT NULL | Associated user |
| `accountId` | VARCHAR(255) | NOT NULL | Provider account ID (= userId for credentials) |
| `providerId` | VARCHAR(255) | NOT NULL | "credential" for email/password |
| `accessToken` | TEXT | NULLABLE | OAuth access token (not used for credentials) |
| `refreshToken` | TEXT | NULLABLE | OAuth refresh token (not used for credentials) |
| `password` | TEXT | NULLABLE | scrypt-hashed password |
| `createdAt` | TIMESTAMPTZ | DEFAULT NOW() | Account link time |
| `updatedAt` | TIMESTAMPTZ | DEFAULT NOW() | Last update |

**Indexes**:
- `PRIMARY KEY (id)`
- `INDEX ON userId`
- `UNIQUE INDEX ON (accountId, providerId)` - Prevents duplicate provider accounts

**Foreign Keys**:
- `userId` REFERENCES `user(id)` ON DELETE CASCADE

**Password Hashing**:
- Algorithm: scrypt (Better Auth default)
- Password never stored in plaintext

---

## Existing Chat Tables (Unchanged)

### sessions (chat sessions)

**Note**: This table is DIFFERENT from Better Auth's `session` table. Both coexist.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `session_id` | UUID | PRIMARY KEY | Chat session identifier |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Session creation |
| `last_active` | TIMESTAMPTZ | DEFAULT NOW() | Last activity |

---

### conversations

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Auto-increment ID |
| `session_id` | UUID | FK → sessions, NOT NULL | Parent chat session |
| `timestamp` | TIMESTAMPTZ | DEFAULT NOW() | Message timestamp |
| `query` | TEXT | NOT NULL | User's question |
| `response` | TEXT | NOT NULL | Agent's answer |
| `sources` | JSONB | DEFAULT '[]' | Citation data |
| `metadata` | JSONB | DEFAULT '{}' | Response metadata |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Record creation |

---

## Schema Migration

Better Auth provides a CLI for schema migrations:

```bash
# Generate migration files (review before applying)
npx @better-auth/cli generate

# Apply migrations to database
npx @better-auth/cli migrate
```

The migration creates the following SQL:

```sql
-- User table
CREATE TABLE IF NOT EXISTS "user" (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    "emailVerified" BOOLEAN DEFAULT false,
    image TEXT,
    "createdAt" TIMESTAMPTZ DEFAULT NOW(),
    "updatedAt" TIMESTAMPTZ DEFAULT NOW()
);

-- Session table
CREATE TABLE IF NOT EXISTS "session" (
    id VARCHAR(36) PRIMARY KEY,
    "userId" VARCHAR(36) NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    "expiresAt" TIMESTAMPTZ NOT NULL,
    "ipAddress" VARCHAR(45),
    "userAgent" TEXT,
    "createdAt" TIMESTAMPTZ DEFAULT NOW(),
    "updatedAt" TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_session_user ON "session"("userId");
CREATE INDEX idx_session_expires ON "session"("expiresAt");

-- Account table
CREATE TABLE IF NOT EXISTS "account" (
    id VARCHAR(36) PRIMARY KEY,
    "userId" VARCHAR(36) NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    "accountId" VARCHAR(255) NOT NULL,
    "providerId" VARCHAR(255) NOT NULL,
    "accessToken" TEXT,
    "refreshToken" TEXT,
    password TEXT,
    "createdAt" TIMESTAMPTZ DEFAULT NOW(),
    "updatedAt" TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE("accountId", "providerId")
);

CREATE INDEX idx_account_user ON "account"("userId");
```

---

## Data Flow

### Signup Flow
```
1. User submits email/password via frontend
2. Better Auth creates:
   - user record (id, name, email)
   - account record (userId, password hash)
   - session record (userId, JWT token)
3. JWT returned to frontend as cookie
```

### Signin Flow
```
1. User submits email/password
2. Better Auth:
   - Looks up user by email
   - Verifies password against account.password
   - Creates new session record
3. JWT returned to frontend as cookie
```

### Chat Request Flow (Authenticated)
```
1. Frontend reads JWT from Better Auth cookie
2. Frontend sends: Authorization: Bearer <JWT>
3. FastAPI extracts JWT from header
4. FastAPI validates JWT via JWKS endpoint
5. FastAPI extracts user_id from JWT claims
6. Request proceeds with authenticated context
```

---

## TypeScript Types

```typescript
// Frontend types (inferred from Better Auth)
interface User {
    id: string;
    name: string;
    email: string;
    emailVerified: boolean;
    image: string | null;
    createdAt: Date;
    updatedAt: Date;
}

interface Session {
    id: string;
    userId: string;
    token: string;
    expiresAt: Date;
    ipAddress: string | null;
    userAgent: string | null;
    createdAt: Date;
    updatedAt: Date;
}

interface AuthState {
    user: User | null;
    session: Session | null;
    isLoading: boolean;
    isAuthenticated: boolean;
}
```

---

## Python Models

```python
# Backend models for JWT validation
from dataclasses import dataclass
from typing import Optional

@dataclass
class TokenPayload:
    """Decoded JWT payload from Better Auth."""
    sub: str  # User ID
    email: str
    iat: int  # Issued at (Unix timestamp)
    exp: int  # Expires at (Unix timestamp)

@dataclass
class AuthenticatedUser:
    """User info extracted from validated JWT."""
    user_id: str
    email: str
```

---

## Table Naming Convention

| Better Auth Table | Chat Table | Purpose |
|-------------------|------------|---------|
| `user` | - | Authenticated users |
| `session` | - | Auth sessions (JWT-backed) |
| `account` | - | Credentials/OAuth accounts |
| - | `sessions` | Chat sessions (UUID-based) |
| - | `conversations` | Chat history |

**Note**: Different naming conventions prevent conflicts:
- Better Auth: camelCase (`userId`, `createdAt`)
- Chat: snake_case (`session_id`, `created_at`)
