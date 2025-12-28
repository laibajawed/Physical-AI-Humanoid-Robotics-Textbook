# Data Model: Spec-4 ChatKit Frontend Integration

**Feature**: 006-chatkit-frontend
**Phase**: 1 - Design
**Date**: 2025-12-18

---

## 1. Frontend TypeScript Interfaces

### 1.1 API Request Types

```typescript
/**
 * Chat request sent to backend
 * Maps to: backend/models/request.py:ChatRequest
 */
interface ChatRequest {
  query: string;                    // 1-32000 characters
  selected_text?: string | null;    // 0-64000 characters (optional)
  session_id?: string | null;       // UUID v4 (generated if missing)
  filters?: {
    source_url_prefix?: string | null;
    section?: string | null;
  } | null;
}

/**
 * History request parameters
 * Maps to: GET /history/{session_id}?limit=N
 */
interface HistoryRequest {
  session_id: string;               // UUID v4
  limit?: number;                   // Default 50, max 100
}
```

### 1.2 API Response Types

```typescript
/**
 * Source citation in response
 * Maps to: backend/models/response.py:SourceCitation
 */
interface SourceCitation {
  source_url: string;               // Full URL to book section
  title: string;                    // Document/chapter title
  section: string;                  // Section/heading name
  chunk_position: number;           // Position in source
  similarity_score: number;         // 0.0-1.0
  snippet: string;                  // First 200 characters
}

/**
 * Response metadata
 * Maps to: backend/models/response.py:ResponseMetadata
 */
interface ResponseMetadata {
  query_time_ms: number;            // Total processing time
  retrieval_count: number;          // Number of chunks retrieved
  mode: 'full' | 'selected_text' | 'retrieval_only' | 'no_results';
  low_confidence: boolean;          // True if scores 0.3-0.5
  request_id: string;               // UUID for tracing
}

/**
 * Main chat response
 * Maps to: backend/models/response.py:ChatResponse
 */
interface ChatResponse {
  answer: string | null;            // AI response (null if unavailable)
  fallback_message?: string | null; // Shown when answer is null
  sources: SourceCitation[];        // Array of citations
  metadata: ResponseMetadata;
  session_id: string;               // Client session identifier
}

/**
 * Error response
 * Maps to: backend/models/response.py:ErrorResponse
 */
interface ErrorResponse {
  error_code: string;               // Machine-readable code
  message: string;                  // Human-readable message
  request_id: string;               // UUID for tracing
  details?: Record<string, unknown>;// Additional context
}

/**
 * History entry (single conversation turn)
 * Maps to: backend/models/session.py:HistoryEntry
 *
 * NOTE: Backend stores each turn as query+response pair, NOT role+content.
 * Frontend must transform this for UI display.
 */
interface HistoryEntry {
  timestamp: string;                // ISO 8601 - when the exchange occurred
  query: string;                    // User's question
  response: string;                 // Agent's answer
  sources?: SourceCitation[];       // Citations for the answer
}

/**
 * History response
 * Maps to: backend/models/session.py:ConversationHistoryResponse
 */
interface HistoryResponse {
  session_id: string;
  entries: HistoryEntry[];          // Array of conversation turns (NOT "messages")
  total_entries: number;            // Total count (NOT "total_count")
}
```

### 1.3 History Transformation Helper

The backend returns `HistoryEntry` with `{query, response}` pairs, but the UI displays
individual messages with `{role, content}`. Use this transformation:

```typescript
/**
 * Transform backend HistoryEntry to UI ChatMessage array
 * Each HistoryEntry becomes TWO ChatMessages (user + assistant)
 */
function transformHistoryToMessages(entries: HistoryEntry[]): ChatMessage[] {
  const messages: ChatMessage[] = [];

  for (const entry of entries) {
    // User message
    messages.push({
      id: `${entry.timestamp}-user`,
      role: 'user',
      content: entry.query,
      timestamp: new Date(entry.timestamp),
    });

    // Assistant message
    messages.push({
      id: `${entry.timestamp}-assistant`,
      role: 'assistant',
      content: entry.response,
      timestamp: new Date(entry.timestamp),
      sources: entry.sources,
    });
  }

  return messages;
}
```

### 1.4 Frontend UI State Types

```typescript
/**
 * Chat UI state
 * Used in: src/hooks/useChat.ts
 */
interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  isOpen: boolean;
  mode: 'full' | 'selected_text';
  selectedText: SelectionContext | null;
}

/**
 * Individual message in UI
 * Used in: src/components/Chat/ChatMessage.tsx
 */
interface ChatMessage {
  id: string;                       // Client-generated UUID
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: SourceCitation[];
  isStreaming?: boolean;
  error?: string;
}

/**
 * Session state
 * Used in: src/hooks/useSession.ts
 */
interface SessionState {
  sessionId: string | null;
  isNewSession: boolean;
  storageAvailable: boolean;
}

/**
 * Selection context for selected-text mode
 * Used in: src/hooks/useTextSelection.ts
 */
interface SelectionContext {
  text: string;                     // Selected text content
  sourceUrl: string;                // Current page URL
  capturedAt: Date;                 // When selection was captured
}
```

### 1.4 Streaming Event Types

```typescript
/**
 * SSE event types from /chat/stream
 */
type StreamEventType = 'delta' | 'sources' | 'done' | 'error';

interface StreamDeltaEvent {
  delta: string;                    // Partial answer text
}

interface StreamSourcesEvent {
  sources: SourceCitation[];
  metadata: {
    query_time_ms: number;
    mode: string;
    session_id: string;
  };
}

interface StreamDoneEvent {
  done: true;
}

interface StreamErrorEvent {
  error: string;
}

type StreamEvent =
  | StreamDeltaEvent
  | StreamSourcesEvent
  | StreamDoneEvent
  | StreamErrorEvent;
```

---

## 2. Database Schema Reference

### 2.1 Neon Postgres Tables (backend/db.py)

The frontend does not directly interact with the database, but understanding the schema helps with API design.

```sql
-- Sessions table
CREATE TABLE sessions (
  id UUID PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversations table
CREATE TABLE conversations (
  id SERIAL PRIMARY KEY,
  session_id UUID REFERENCES sessions(id),
  query TEXT NOT NULL,
  response TEXT,
  sources JSONB,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for session lookup
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
```

---

## 3. Validation Rules

### 3.1 Request Validation

| Field | Type | Min | Max | Required | Default |
|-------|------|-----|-----|----------|---------|
| `query` | string | 1 | 32000 | Yes | - |
| `selected_text` | string | 0 | 64000 | No | null |
| `session_id` | UUID v4 | - | - | No | Generated |
| `filters.source_url_prefix` | string | 0 | 500 | No | null |
| `filters.section` | string | 0 | 200 | No | null |

### 3.2 Frontend Validation

```typescript
// Query validation
const validateQuery = (query: string): string | null => {
  if (!query || query.trim().length === 0) {
    return 'Please enter a question';
  }
  if (query.length > 32000) {
    return 'Question is too long (max 32,000 characters)';
  }
  return null;
};

// Selection validation
const validateSelection = (text: string): string | null => {
  if (text.length < 20) {
    return 'Please select more text for better results';
  }
  if (text.length > 64000) {
    return 'Selection is too long (max 64,000 characters)';
  }
  return null;
};

// Session ID validation
const isValidSessionId = (id: string): boolean => {
  const uuidV4Regex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidV4Regex.test(id);
};
```

---

## 4. State Transitions

### 4.1 Chat State Machine

```
                    ┌──────────────────┐
                    │      IDLE        │
                    │  isOpen: false   │
                    │  isLoading: false│
                    └────────┬─────────┘
                             │ open()
                             ▼
                    ┌──────────────────┐
      ┌─────────────│      OPEN        │──────────────┐
      │             │  isOpen: true    │              │
      │             │  isLoading: false│              │
      │             └────────┬─────────┘              │
      │ close()              │ submit()               │ selectText()
      │                      ▼                        ▼
      │             ┌──────────────────┐    ┌──────────────────┐
      │             │    LOADING       │    │  SELECTED_TEXT   │
      │             │  isOpen: true    │    │  mode: selected  │
      │             │  isLoading: true │    │  selectedText: X │
      │             └────────┬─────────┘    └────────┬─────────┘
      │                      │                       │
      │      ┌───────────────┼───────────────┐      │ submit()
      │      │ success       │ error         │      │
      │      ▼               ▼               ▼      ▼
      │ ┌──────────┐   ┌──────────────┐   ┌──────────────────┐
      │ │ RESPONSE │   │    ERROR     │   │  LOADING         │
      │ │ messages+│   │  error: msg  │   │  (selected mode) │
      │ └────┬─────┘   └──────┬───────┘   └────────┬─────────┘
      │      │                │                    │
      │      └────────────────┼────────────────────┘
      │                       │
      │                       ▼
      │             ┌──────────────────┐
      └─────────────│      OPEN        │
                    │  Ready for next  │
                    └──────────────────┘
```

### 4.2 Session State Transitions

```
┌─────────────────────────────────────────────────────────────────┐
│                        PAGE LOAD                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │  Check localStorage │
                  └──────────┬──────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                 │
            ▼                                 ▼
   ┌─────────────────┐              ┌─────────────────┐
   │ Session found   │              │ No session      │
   │ isNewSession:   │              │ isNewSession:   │
   │   false         │              │   true          │
   └────────┬────────┘              └────────┬────────┘
            │                                │
            ▼                                ▼
   ┌─────────────────┐              ┌─────────────────┐
   │ Load history    │              │ Generate UUID   │
   │ GET /history    │              │ Store in        │
   │                 │              │ localStorage    │
   └────────┬────────┘              └────────┬────────┘
            │                                │
            └────────────────┬───────────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │   READY TO CHAT     │
                  └─────────────────────┘
```

---

## 5. Entity Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
│                                                                 │
│  ┌─────────────┐     1:N      ┌─────────────────┐              │
│  │ ChatSession │──────────────│   ChatMessage   │              │
│  │             │              │                 │              │
│  │ sessionId   │              │ id              │              │
│  │ mode        │              │ role            │              │
│  │ selectedText│              │ content         │              │
│  └─────────────┘              │ timestamp       │              │
│                               │ sources[]       │              │
│                               └────────┬────────┘              │
│                                        │                       │
│                                        │ 0:N                   │
│                                        ▼                       │
│                               ┌─────────────────┐              │
│                               │ SourceCitation  │              │
│                               │                 │              │
│                               │ source_url      │              │
│                               │ title           │              │
│                               │ section         │              │
│                               │ snippet         │              │
│                               │ similarity_score│              │
│                               └─────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Error Code Mapping

| Error Code | HTTP Status | Frontend Action |
|------------|-------------|-----------------|
| `VALIDATION_ERROR` | 400 | Show inline error, focus input |
| `EMPTY_QUERY` | 400 | Show "Please enter a question" |
| `QUERY_TOO_LONG` | 400 | Show character count, trim |
| `SELECTION_TOO_LONG` | 400 | Show "Selection too long" |
| `RATE_LIMITED` | 429 | Disable input, countdown timer |
| `SESSION_NOT_FOUND` | 404 | Clear session, start fresh |
| `SERVICE_UNAVAILABLE` | 503 | Retry button with backoff |
| `INTERNAL_ERROR` | 500 | Generic error + retry |
| `CORS_ERROR` | N/A | Check connection message |
| `NETWORK_ERROR` | N/A | Check internet message |
| `TIMEOUT` | N/A | Retry button |

---

## 7. Configuration Constants

```typescript
// src/services/config.ts
// NOTE: In actual implementation, use useDocusaurusContext() to get siteConfig.customFields.backendUrl
// This file shows the constants; the actual URL comes from docusaurus.config.ts customFields

export const CONFIG = {
  // API Configuration - Use siteConfig.customFields.backendUrl in components
  // Fallback for non-Docusaurus contexts (e.g., tests)
  API_BASE_URL_FALLBACK: 'http://localhost:8000',

  // Timeouts
  REQUEST_TIMEOUT_MS: 30000,
  STREAM_TIMEOUT_MS: 60000,

  // Retry Configuration
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 1000,
  RETRY_BACKOFF_MULTIPLIER: 2,

  // Validation Limits
  MAX_QUERY_LENGTH: 32000,
  MAX_SELECTION_LENGTH: 64000,
  MIN_SELECTION_LENGTH: 20,

  // Session Configuration
  SESSION_STORAGE_KEY: 'chatui_session_id',
  HISTORY_LIMIT: 50,

  // UI Configuration
  MAX_MESSAGES_DISPLAYED: 100,
  AUTO_SCROLL_THRESHOLD: 100,
} as const;
```
