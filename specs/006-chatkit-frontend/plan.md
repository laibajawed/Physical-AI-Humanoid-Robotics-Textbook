# Implementation Plan: Spec-4 ChatUI Frontend Integration

**Feature Branch**: `006-chatkit-frontend`
**Created**: 2025-12-18
**Status**: Ready for Tasks

---

## Executive Summary

This plan defines the technical architecture for integrating an Alibaba ChatUI-based RAG chatbot UI into the Docusaurus Physical AI & Robotics textbook. The frontend connects to the existing FastAPI backend (`backend/app.py`) for Q&A with source citations, supports selected-text-only mode, and persists conversation history via Neon Postgres.

---

## 1. Technical Context

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DOCUSAURUS BOOK (Vercel)                                 │
│                                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────────┐              │
│  │ Book Pages  │───>│  ChatWidget  │<───│ SelectionPopup    │              │
│  │ (MDX)       │    │  (Global)    │    │ (Text Selection)  │              │
│  └─────────────┘    └──────┬───────┘    └───────────────────┘              │
│                            │                                                │
│                    ┌───────┴────────┐                                       │
│                    │  chatApi.ts    │                                       │
│                    └───────┬────────┘                                       │
└────────────────────────────┼────────────────────────────────────────────────┘
                             │ HTTPS (CORS)
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (Railway)                                │
│                                                                             │
│  /chat (354) ─────> OpenAI Agents SDK ───> Qdrant (vectors)                │
│  /chat/stream (543) ────────────────────> Neon Postgres (history)          │
│  /history/{id} (625)                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Integration Points

| Layer | Component | Location | Notes |
|-------|-----------|----------|-------|
| Frontend | Chat Widget | `src/theme/Layout/index.tsx` | Global via Layout wrapper |
| Frontend | API Client | `src/services/chatApi.ts` | REST + SSE |
| Backend | CORS Config | `backend/app.py:176-183` | Update `CORS_ORIGINS` |
| Backend | Chat Endpoint | `backend/app.py:354` | No changes needed |
| Backend | Stream Endpoint | `backend/app.py:543` | No changes needed |
| Backend | History Endpoint | `backend/app.py:625` | No changes needed |

### 1.3 Environment Configuration

**IMPORTANT**: Docusaurus does NOT use `NEXT_PUBLIC_*` variables (that's Next.js).
Use `docusaurus.config.ts` customFields instead.

**Frontend** (`physical-ai-robotics-book/docusaurus.config.ts`):
```typescript
const config: Config = {
  // ... existing config
  customFields: {
    backendUrl: process.env.BACKEND_URL || 'http://localhost:8000',
  },
};
```

**Frontend access in React**:
```typescript
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
const { siteConfig } = useDocusaurusContext();
const backendUrl = siteConfig.customFields.backendUrl as string;
```

**Frontend** (`physical-ai-robotics-book/.env` for local dev):
```env
BACKEND_URL=http://localhost:8000
```

**Backend** (update existing):
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://hackathon-i-physical-ai-humanoid-ro-dun.vercel.app
```

---

## 2. Constitution Check

| Principle | Status | Evidence |
|-----------|--------|----------|
| CODE QUALITY: TypeScript strict mode | ✅ PASS | All components use TypeScript with strict types |
| CODE QUALITY: Component-based React | ✅ PASS | Chat split into modular components |
| CODE QUALITY: Zero external deps where possible | ✅ PASS | Uses only installed deps (@chatui/core, uuid) |
| USER EXPERIENCE: Mobile-first responsive | ✅ PASS | Full-screen overlay on mobile, floating panel on desktop |
| USER EXPERIENCE: Fast page loads | ✅ PASS | Lazy-load chat on interaction, streaming reduces perceived latency |
| DESIGN STANDARDS: Tailwind CSS v4 | ✅ PASS | All styling via Tailwind classes |
| DESIGN STANDARDS: Consistent color palette | ✅ PASS | Uses existing Docusaurus theme colors |

---

## 3. Architectural Decisions

### 3.1 Widget Placement Strategy

**Decision**: Global floating widget via Layout wrapper

**Rationale**:
- Single integration point (`src/theme/Layout/index.tsx`)
- Chat available on all pages without per-page setup
- State persists during navigation
- Docusaurus-native pattern for global components

**Alternatives Considered**:
- Per-page component: Too much boilerplate, inconsistent UX
- Sidebar panel: Reduces content width, complex layout changes

### 3.2 Streaming Implementation

**Decision**: SSE via `/chat/stream` with non-streaming fallback

**Rationale**:
- Better UX with real-time feedback
- Backend already implements SSE (app.py:543)
- EventSource API is well-supported
- Graceful fallback to `/chat` if streaming fails

**Implementation**:
```typescript
// Primary: streaming
streamChatMessage(request, onDelta, onSources, onError, onDone);

// Fallback: non-streaming
if (streamingFailed) {
  const response = await sendChatMessage(request);
}
```

### 3.3 Session Storage

**Decision**: Client-generated UUID v4 in localStorage

**Key**: `chatui_session_id`

**Rationale**:
- Simple and persistent across sessions
- No cookies needed (GDPR-friendly)
- Backend accepts client-provided session IDs
- Graceful fallback to in-memory UUID if localStorage unavailable

**Constraint**: Per spec IC-004, "Session IDs are client-generated UUIDs, not server-assigned"

### 3.4 CORS Configuration

**Decision**: Strict allowlist (no wildcards in production)

**Allowed Origins**:
```
http://localhost:3000      # Docusaurus dev server
http://localhost:5173      # Vite dev server
https://hackathon-i-physical-ai-humanoid-ro-dun.vercel.app  # Production
```

**Rationale**:
- Maximum security
- Explicit control over allowed origins
- Per spec FR-028: "Backend MUST NOT use wildcard (*) origins in production"

**Trade-off**: Vercel preview deployments will get CORS errors (acceptable per FR-027a)

### 3.5 State Management

**Decision**: React Context + useReducer (per constraint FC-005)

**Rationale**:
- No additional state libraries needed
- useReducer handles complex state transitions
- Context provides chat state to all components
- Matches FC-005: "No additional state management libraries (Redux, Zustand) required"

---

## 4. Component Architecture

### 4.1 File Structure

```
physical-ai-robotics-book/src/
├── components/
│   ├── Chat/
│   │   ├── ChatWidget.tsx       # Main container + floating trigger
│   │   ├── ChatPanel.tsx        # Expanded chat interface
│   │   ├── ChatMessage.tsx      # Individual message rendering
│   │   ├── ChatInput.tsx        # Input field with send button
│   │   ├── SourceCitations.tsx  # Citation list component
│   │   ├── LoadingIndicator.tsx # Loading/streaming indicator
│   │   └── index.ts             # Barrel exports
│   └── TextSelection/
│       ├── SelectionPopup.tsx   # "Ask about selection" button
│       └── index.ts
├── hooks/
│   ├── useChat.ts               # Chat state + API logic
│   ├── useTextSelection.ts      # Text selection capture
│   └── useSession.ts            # Session/localStorage management
├── services/
│   ├── chatApi.ts               # Backend API client (REST + SSE)
│   ├── config.ts                # Environment configuration
│   └── errors.ts                # Custom error classes
├── context/
│   └── ChatContext.tsx          # React Context provider
├── types/
│   └── chat.ts                  # TypeScript interfaces
└── theme/
    └── Layout/
        └── index.tsx            # Layout wrapper with ChatWidget
```

### 4.2 Component Hierarchy

```
Layout (theme wrapper)
└── ChatWidget
    ├── TriggerButton (when closed)
    └── ChatPanel (when open)
        ├── Header
        │   ├── Title
        │   ├── ModeIndicator (full/selected-text)
        │   └── CloseButton
        ├── MessageList
        │   └── ChatMessage (repeated)
        │       ├── Content (markdown)
        │       ├── SourceCitations
        │       └── Timestamp
        ├── ErrorBanner (if error)
        └── ChatInput
            ├── TextArea
            └── SendButton

SelectionPopup (injected globally)
├── "Ask about selection" button
└── ClearButton
```

---

## 5. API Integration

### 5.1 Endpoints Used

| Endpoint | Method | Purpose | Frontend Usage |
|----------|--------|---------|----------------|
| `/chat` | POST | Non-streaming Q&A | Fallback mode |
| `/chat/stream` | POST | SSE streaming | Primary mode |
| `/history/{session_id}` | GET | Load history | On mount (if session exists) |
| `/health` | GET | Health check | Optional pre-flight |

### 5.2 History Data Transformation

**IMPORTANT**: Backend returns `HistoryEntry` with `{timestamp, query, response, sources}` format,
but the UI displays individual messages with `{role, content}` format.

The frontend must transform each history entry into TWO messages:
```typescript
// Backend format (one entry = one conversation turn)
{ timestamp, query: "User question", response: "Agent answer", sources: [...] }

// UI format (two messages per turn)
{ role: 'user', content: "User question", timestamp }
{ role: 'assistant', content: "Agent answer", timestamp, sources: [...] }
```

See `transformHistoryToMessages()` in `src/services/chatApi.ts`.

### 5.3 Request Flow

```
User types question
        │
        ▼
┌───────────────────────┐
│ Validate input        │ ← Check length, empty
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Build ChatRequest     │ ← query, selected_text, session_id
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ POST /chat/stream     │ ← Try streaming first
└───────────┬───────────┘
            │
    ┌───────┴───────┐
    │ Success?      │
    └───────┬───────┘
      Yes   │   No
    ┌───────┴───────┐
    │               │
    ▼               ▼
┌─────────┐   ┌─────────────┐
│ Stream  │   │ Fallback to │
│ SSE     │   │ POST /chat  │
└─────────┘   └─────────────┘
```

### 5.4 Error Handling

| Error | HTTP | Frontend Action |
|-------|------|-----------------|
| EMPTY_QUERY | 400 | Show inline error |
| QUERY_TOO_LONG | 400 | Show character count |
| RATE_LIMITED | 429 | Disable input, countdown |
| SERVICE_UNAVAILABLE | 503 | Retry button |
| CORS_ERROR | N/A | Check connection message |
| NETWORK_ERROR | N/A | Check internet message |

---

## 6. Selected-Text Mode Flow

```
1. User selects text on book page
   └── mouseup event triggers

2. SelectionPopup appears
   └── Position near selection using getBoundingClientRect()

3. User clicks "Ask about selection"
   └── Capture: { text, sourceUrl, capturedAt }

4. Chat opens in selected_text mode
   └── Show indicator: "Answering from selection"

5. User submits question
   └── Request includes selected_text field

6. Backend processes (no Qdrant search)
   └── Returns mode="selected_text" in metadata

7. Response displays
   └── Citation shows "Based on your selection"

8. User can clear selection
   └── Returns to full-book mode
```

---

## 7. Quality Validation

### 7.1 Selected-Text-Only Enforcement

**Backend**: Already implemented (app.py:462-469)
- When `selected_text` provided, skips Qdrant retrieval
- Returns `mode="selected_text"` in metadata
- Creates special citation for selected text

**Frontend**:
- Display "Selected-Text Mode" indicator
- Show "Based on your selection" instead of chapter refs
- Provide "Clear selection" button

### 7.2 Safe Fallbacks

| Condition | Fallback |
|-----------|----------|
| Empty retrieval | Show "No relevant information found" |
| LLM error | Show fallback_message from backend |
| Network timeout | Show retry button |
| localStorage unavailable | Use in-memory session |
| Streaming fails | Fall back to non-streaming |

### 7.3 Logging (No Secrets)

**Logged** (safe):
- request_id
- session_id
- query_length
- mode
- latency_ms

**Never Logged**:
- Query content
- Selected text
- API keys
- User PII

---

## 8. Testing Strategy

### 8.1 E2E Smoke Checklist

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 1 | UI Renders | Open any book page | Chat button visible |
| 2 | No CORS | Submit question | No CORS errors in console |
| 3 | Chat Works | Ask "What is inverse kinematics?" | Response within 5s |
| 4 | Citations | Check response | Clickable links |
| 5 | History | Close/reopen browser | Messages loaded |
| 6 | Selected-Text | Select text → Ask | Only references selection |
| 7 | Errors | Disconnect backend | User-friendly message |
| 8 | Mobile | 375px viewport | Full-screen overlay |

### 8.2 Unit Test Coverage

| Component | Test Focus |
|-----------|------------|
| useChat | State transitions, message handling |
| useSession | localStorage read/write, fallback |
| useTextSelection | Selection capture, coordinates |
| chatApi | Request formatting, error handling |
| ChatMessage | Markdown rendering, citations |

---

## 9. Implementation Dependencies

### 9.1 Execution Order

```
Phase 1: Foundation (no backend changes)
├── T1: src/services/config.ts
├── T2: src/types/chat.ts
├── T3: src/services/errors.ts
└── T4: src/services/chatApi.ts

Phase 2: Hooks
├── T5: src/hooks/useSession.ts
├── T6: src/hooks/useChat.ts
└── T7: src/hooks/useTextSelection.ts

Phase 3: Components
├── T8: src/components/Chat/ChatMessage.tsx
├── T9: src/components/Chat/SourceCitations.tsx
├── T10: src/components/Chat/ChatInput.tsx
├── T11: src/components/Chat/ChatPanel.tsx
├── T12: src/components/Chat/ChatWidget.tsx
└── T13: src/components/TextSelection/SelectionPopup.tsx

Phase 4: Integration
├── T14: src/theme/Layout/index.tsx (wrapper)
└── T15: Backend CORS update

Phase 5: Verification
├── T16: Manual smoke tests
└── T17: Mobile responsiveness check
```

### 9.2 Critical Path

```
config.ts → chatApi.ts → useSession.ts → useChat.ts → ChatWidget.tsx → Layout wrapper
```

---

## 10. Artifacts Generated

| Artifact | Path | Purpose |
|----------|------|---------|
| Research | `specs/006-chatkit-frontend/research.md` | Phase 0 decisions |
| Data Model | `specs/006-chatkit-frontend/data-model.md` | TypeScript interfaces |
| API Contract | `specs/006-chatkit-frontend/contracts/frontend-api.yaml` | OpenAPI spec |
| Quickstart | `specs/006-chatkit-frontend/quickstart.md` | Implementation guide |
| Plan | `specs/006-chatkit-frontend/plan.md` | This document |

---

## 11. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| CORS errors on preview deploys | Low | High | Accept for hackathon; test on production |
| localStorage unavailable | Medium | Low | In-memory fallback |
| Backend timeout | Medium | Medium | Loading indicator, retry button |
| ChatUI React 19 compatibility | Low | Low | Already installed and working |
| Streaming connection drops | Medium | Medium | Reconnection with backoff |

---

## 12. Next Steps

1. **Run `/sp.tasks`** to generate atomic implementation tasks
2. **Update backend CORS** in deployment environment
3. **Implement components** following quickstart.md order
4. **Run smoke tests** per checklist
5. **Deploy and verify** on production domain

---

## ADR Suggestions

The following architectural decisions may warrant formal documentation:

1. **Global Widget Placement**: Layout wrapper vs per-page component
2. **Client-Generated Sessions**: localStorage UUID vs server-assigned
3. **React Context State**: useReducer vs external state library

Run `/sp.adr <title>` to document if the team agrees these are significant.
