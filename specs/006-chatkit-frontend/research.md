# Research: Spec-4 ChatKit Frontend Integration

**Feature**: 006-chatkit-frontend
**Phase**: 0 - Research
**Date**: 2025-12-18

---

## 1. Architecture Analysis

### 1.1 End-to-End System Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOCUSAURUS BOOK (Vercel)                          │
│  ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────────┐   │
│  │  Book Content   │    │   ChatKit UI     │    │  Selection Popup     │   │
│  │  (MDX Pages)    │───>│  (React Widget)  │<───│  (Text Selection)    │   │
│  └─────────────────┘    └────────┬─────────┘    └──────────────────────┘   │
│                                  │                                          │
│                    ┌─────────────┴─────────────┐                           │
│                    │      chatApi.ts           │                           │
│                    │  (API Client Service)     │                           │
│                    └─────────────┬─────────────┘                           │
└──────────────────────────────────┼──────────────────────────────────────────┘
                                   │ HTTPS (CORS)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND (Railway)                           │
│  ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────────┐   │
│  │  /chat          │    │  /chat/stream    │    │  /history/{session}  │   │
│  │  (Non-streaming)│    │  (SSE Streaming) │    │  (Get History)       │   │
│  └────────┬────────┘    └────────┬─────────┘    └──────────┬───────────┘   │
│           │                      │                         │               │
│           └──────────────────────┼─────────────────────────┘               │
│                                  ▼                                          │
│                    ┌─────────────────────────┐                              │
│                    │     OpenAI Agents SDK   │                              │
│                    │     (RAG Agent)         │                              │
│                    └─────────────┬───────────┘                              │
│                                  │                                          │
│           ┌──────────────────────┼──────────────────────┐                  │
│           ▼                      ▼                      ▼                  │
│  ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────────┐   │
│  │  Qdrant Cloud   │    │  Cohere Embed    │    │  Neon Postgres       │   │
│  │  (Vector Store) │    │  (Embeddings)    │    │  (Session History)   │   │
│  └─────────────────┘    └──────────────────┘    └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Selected-Text-Only Request Flow

```
1. User Action:
   ┌──────────────────────────────────────────────┐
   │  User selects text on book page              │
   │  mouseup event → window.getSelection()       │
   └──────────────────────────────────────────────┘
                         │
                         ▼
2. Capture Selection:
   ┌──────────────────────────────────────────────┐
   │  SelectionPopup appears near selection       │
   │  Shows: "Ask about selection" button         │
   │  Captures: { text, sourceUrl, capturedAt }   │
   └──────────────────────────────────────────────┘
                         │
                         ▼
3. Submit Question:
   ┌──────────────────────────────────────────────┐
   │  ChatRequest {                               │
   │    query: "What does this mean?",            │
   │    selected_text: "<captured text>",         │
   │    session_id: "uuid-v4"                     │
   │  }                                           │
   └──────────────────────────────────────────────┘
                         │
                         ▼
4. Backend Processing:
   ┌──────────────────────────────────────────────┐
   │  Backend detects selected_text is present    │
   │  SKIPS Qdrant retrieval (no vector search)   │
   │  Answers ONLY from provided selection        │
   │  Returns mode="selected_text" in metadata    │
   └──────────────────────────────────────────────┘
                         │
                         ▼
5. Display Response:
   ┌──────────────────────────────────────────────┐
   │  UI shows answer with special citation:      │
   │  "Based on your selection" (not chapter ref) │
   │  Indicator shows "Selected-Text Mode" active │
   └──────────────────────────────────────────────┘
```

---

## 2. Existing Backend Review

### 2.1 Endpoints Available (backend/app.py)

| Endpoint | Method | Line | Purpose | Request | Response |
|----------|--------|------|---------|---------|----------|
| `/chat` | POST | 354 | Non-streaming Q&A | `ChatRequest` | `ChatResponse` |
| `/chat/stream` | POST | 543 | SSE streaming | `ChatRequest` | SSE events |
| `/history/{session_id}` | GET | 625 | Get conversation history | `session_id: UUID` | `ConversationHistoryResponse` |
| `/health` | GET | 291 | Service health check | - | `HealthResponse` |

### 2.2 CORS Configuration (app.py:61, 176-183)

```python
# Current configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Required Update**: Add production domain to `CORS_ORIGINS`:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://hackathon-i-physical-ai-humanoid-ro-dun.vercel.app
```

### 2.3 Request/Response Models (backend/models/)

**ChatRequest** - Already supports all required fields:
- `query: str` (1-32000 chars)
- `selected_text: Optional[str]` (0-64000 chars)
- `session_id: Optional[UUID]`
- `filters: Optional[QueryFilters]`

**ChatResponse** - Returns all needed data:
- `answer: Optional[str]`
- `fallback_message: Optional[str]`
- `sources: List[SourceCitation]`
- `metadata: ResponseMetadata`
- `session_id: UUID`

---

## 3. Integration Decisions

### 3.1 Widget Placement

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Global Floating Widget** | Single integration point, visible on all pages, persistent state | May obstruct content on some pages | **CHOSEN** |
| Per-Page Component | Fine-grained control, page-specific context | Requires integration in each MDX file | Not chosen |
| Sidebar Panel | Always visible, more screen real estate | Reduces content width, complex layout | Not chosen |

**Implementation**: Use Docusaurus theme wrapper at `src/theme/Layout/index.tsx` to inject ChatWidget globally.

### 3.2 Streaming vs Non-Streaming

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **SSE Streaming** | Better UX (real-time feedback), lower perceived latency | More complex implementation | **CHOSEN** |
| Non-Streaming | Simpler implementation | User waits for full response | Fallback only |

**Implementation**: Primary mode uses `/chat/stream` with EventSource. Fall back to `/chat` if SSE fails.

### 3.3 Session Storage Strategy

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Client localStorage** | Simple, persists across sessions, no cookies needed | Limited to 5MB, cleared in private mode | **CHOSEN** |
| Cookies | Server-accessible, automatic inclusion | Size limit (4KB), GDPR concerns | Not chosen |
| Server-assigned | Single source of truth | Requires auth, can't work offline | Not chosen |

**Implementation**:
- Key: `chatkit_session_id`
- Value: UUID v4 (client-generated)
- Fallback: In-memory UUID if localStorage unavailable

### 3.4 CORS Policy

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Strict Allowlist** | Maximum security, explicit control | Requires manual updates | **CHOSEN** |
| Wildcard (*) | Easy, works everywhere | Security risk in production | Not allowed |
| Dynamic Pattern | Flexible for preview URLs | Complex, potential security holes | Not chosen |

**Allowed Origins**:
```
http://localhost:3000      # Docusaurus dev server
http://localhost:5173      # Vite dev server (if used)
https://hackathon-i-physical-ai-humanoid-ro-dun.vercel.app  # Production
```

---

## 4. Quality Validation Strategy

### 4.1 Selected-Text-Only Enforcement

The backend already handles this correctly (app.py:462-469):
```python
if selected_text:
    mode = "selected_text"
    low_confidence = False
    retrieval_count = 0
    sources = [create_selected_text_citation(selected_text, ...)]
```

**Frontend Enforcement**:
1. When `selected_text` is provided, backend SKIPS Qdrant retrieval
2. UI shows "Selected-Text Mode" indicator
3. Citations display "Based on your selection" not chapter references
4. User can clear selection to return to full-book mode

### 4.2 Safe Fallbacks for Empty Retrieval

When retrieval returns no results:
1. Backend sets `mode = "no_results"` (app.py:481)
2. Backend returns `fallback_message` (app.py:476-478)
3. Frontend displays: "I couldn't find relevant information in the book for your question."
4. Suggest rephrasing the question

### 4.3 Logging Strategy (No Secrets)

**Logged Fields** (safe):
- `request_id` (UUID)
- `session_id` (UUID, user-generated)
- `query_length` (int)
- `mode` (string)
- `latency_ms` (float)
- `status_code` (int)

**Never Logged**:
- Full query text (PII risk)
- Selected text content
- API keys
- User IP addresses

---

## 5. Testing Strategy

### 5.1 E2E Smoke Checklist

| # | Test | Steps | Expected | Status |
|---|------|-------|----------|--------|
| 1 | UI Renders | Open any book page | Chat trigger button visible in bottom-right | ☐ |
| 2 | No CORS Errors | Submit question | No CORS errors in console | ☐ |
| 3 | Chat Completes | Ask "What is inverse kinematics?" | Response with answer within 5s | ☐ |
| 4 | Citations Render | Check response | Clickable source links present | ☐ |
| 5 | History Persists | Close/reopen browser | Previous messages loaded | ☐ |
| 6 | Selected-Text Mode | Select text → Ask question | Answer references only selection | ☐ |
| 7 | Error Handling | Disconnect backend | User-friendly error message | ☐ |
| 8 | Mobile Layout | Open on 375px viewport | Full-screen overlay, all controls accessible | ☐ |

### 5.2 Unit Test Coverage

| Component | Test Focus |
|-----------|------------|
| `useChat.ts` | State transitions, message formatting |
| `useSession.ts` | localStorage read/write, fallback behavior |
| `useTextSelection.ts` | Selection capture, coordinate calculation |
| `chatApi.ts` | Request formatting, error handling |

---

## 6. Dependencies & Compatibility

### 6.1 Frontend Stack

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| `@docusaurus/core` | 3.9.2 | Documentation framework | Installed |
| `react` | 19.0.0 | UI library | Installed |
| `@openai/chatkit-react` | 1.3.0 | Chat UI components | Installed |
| `tailwindcss` | 4.1.17 | Styling | Installed |
| `typescript` | 5.6.2 | Type safety | Installed |

### 6.2 Backend Stack

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| `fastapi` | 0.115+ | API framework | Installed |
| `openai-agents` | 0.0.17+ | Agent SDK | Installed |
| `qdrant-client` | 1.14+ | Vector database | Installed |
| `asyncpg` | - | Postgres async driver | Installed |

---

## 7. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| CORS errors on preview deploys | Low | Accept for hackathon; test on production domain |
| localStorage unavailable | Medium | Graceful fallback to in-memory session |
| Backend timeout | Medium | Show loading indicator, implement retry |
| ChatKit compatibility with React 19 | Low | Already installed and tested |
| Streaming connection drops | Medium | Reconnection logic with exponential backoff |

---

## 8. Research Conclusions

All NEEDS CLARIFICATION items resolved:

1. **Widget Placement**: Global floating widget via Layout wrapper
2. **Streaming**: SSE via `/chat/stream` with non-streaming fallback
3. **Session Storage**: Client-generated UUID v4 in localStorage
4. **CORS Policy**: Strict allowlist (no wildcards in production)
5. **State Management**: React Context + useReducer (per FC-005 constraint)
6. **Selected-Text Enforcement**: Backend already implemented; UI needs indicators

**Ready for Phase 1: Design & Contracts**
