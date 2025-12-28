# Feature Specification: Docusaurus ChatKit Frontend + Integration

**Feature Branch**: `006-chatkit-frontend`
**Created**: 2025-12-18
**Updated**: 2025-12-18
**Status**: Ready for Planning

**Input**: User description: "Build the RAG chatbot frontend inside the Docusaurus book using ChatKit, then integrate it with the existing FastAPI + OpenAI Agents backend, including Neon Postgres chat history (database.py) and browser-safe CORS."

---

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Ask Questions About the Book (Priority: P1)

As a reader of the Physical AI & Humanoid Robotics textbook, I want to ask questions about the book content directly from the documentation site so that I can get instant answers without leaving the page.

**Why this priority**: This is the core functionality that enables the RAG chatbot to deliver value. Without a working chat interface connected to the backend, no other feature matters.

**Independent Test**: Can be fully tested by opening the chat widget, typing "What is inverse kinematics?", and verifying a response appears with source citations within 5 seconds.

**Acceptance Scenarios**:

1. **Given** I am on any page of the Docusaurus book, **When** I click the chat widget trigger, **Then** a chat interface opens where I can type questions.
2. **Given** the chat interface is open, **When** I submit a question about the book content, **Then** I receive an answer with source citations linking to relevant book sections.
3. **Given** I ask a question, **When** the backend responds, **Then** the response renders within the chat UI with proper markdown formatting.

---

### User Story 2 - View Source Citations (Priority: P1)

As a researcher or student, I want to see where each answer comes from so that I can verify the information and explore related content in the original source.

**Why this priority**: Source citations are essential for RAG trustworthiness. Users must be able to verify AI-generated answers against the original book content.

**Independent Test**: Can be tested by asking any book-related question and verifying that clickable source links appear that navigate to the correct book sections.

**Acceptance Scenarios**:

1. **Given** I receive an answer to my question, **When** the response includes source citations, **Then** each citation shows the chapter/section title and is clickable.
2. **Given** I click on a source citation link, **When** the navigation occurs, **Then** I am taken to the correct section of the book.
3. **Given** multiple sources contribute to an answer, **When** displayed, **Then** all sources are listed in a clear, scannable format.

---

### User Story 3 - Selected-Text Mode (Priority: P1)

As a student reading a specific section, I want to highlight text in the book and ask questions about only that selection so that I get focused answers grounded in the specific content I'm studying.

**Why this priority**: This differentiating feature enables contextual learning. Students can get clarification on specific paragraphs without irrelevant information from other chapters.

**Independent Test**: Can be tested by selecting text on a book page, clicking "Ask about selection", typing a question, and verifying the answer references only the selected content.

**Acceptance Scenarios**:

1. **Given** I highlight/select text on a book page, **When** I click an "Ask about selection" button, **Then** the selected text is captured and displayed in the chat context.
2. **Given** selected text is captured, **When** I submit a question, **Then** the answer is grounded only in that selected text (not the full book).
3. **Given** I'm in selected-text mode, **When** I receive a response, **Then** the citation indicates "based on your selection" rather than showing chapter references.

---

### User Story 4 - Conversation History Persistence (Priority: P2)

As a returning user, I want my previous conversations to be saved so that I can continue where I left off and reference past answers.

**Why this priority**: Enhances user experience by providing continuity. Users studying over multiple sessions benefit from persistent context.

**Independent Test**: Can be tested by starting a conversation, closing the browser, reopening the site, and verifying previous messages are displayed.

**Acceptance Scenarios**:

1. **Given** I have an active chat session, **When** I close and reopen the browser, **Then** my previous conversation history is displayed.
2. **Given** I return to the site with an existing session_id (stored in localStorage), **When** the chat loads, **Then** the frontend fetches and displays my conversation history from the backend.
3. **Given** I start a fresh session, **When** I send my first message, **Then** a new session_id is generated and stored in localStorage.

---

### User Story 5 - Graceful Error Handling (Priority: P2)

As a user, I want clear feedback when something goes wrong so that I know whether to retry or try a different approach.

**Why this priority**: Production systems must handle errors gracefully. Users should never see cryptic error messages or experience silent failures.

**Independent Test**: Can be tested by disconnecting the backend and submitting a question, verifying a user-friendly error message appears.

**Acceptance Scenarios**:

1. **Given** the backend is unavailable, **When** I submit a question, **Then** I see a friendly error message like "Service temporarily unavailable. Please try again."
2. **Given** my question has no relevant results in the book, **When** the agent responds, **Then** I see a message indicating "I couldn't find relevant information" rather than an empty response.
3. **Given** a network timeout occurs, **When** displayed, **Then** the error message includes a "Retry" button.

---

### User Story 6 - Responsive Chat UI (Priority: P2)

As a mobile or tablet user, I want the chat interface to work well on different screen sizes so that I can use it on any device.

**Why this priority**: The Docusaurus book is accessible on multiple devices. The chat feature should maintain usability across screen sizes.

**Independent Test**: Can be tested by resizing the browser window or using device simulation to verify the chat UI adapts appropriately.

**Acceptance Scenarios**:

1. **Given** I'm on a mobile device (viewport < 768px), **When** I open the chat, **Then** it displays as a full-screen overlay or bottom sheet.
2. **Given** I'm on a desktop (viewport >= 1024px), **When** the chat is open, **Then** it displays as a floating panel that doesn't obstruct the main content.
3. **Given** any viewport size, **When** I interact with the chat, **Then** input fields, buttons, and text are readable and accessible.

---

### Edge Cases

| Edge Case | Behavior |
|-----------|----------|
| Backend returns empty sources array | Display the answer text with a note "No specific sources cited" |
| User's selected text < 20 characters | Show tooltip: "Please select more text for better results" but allow submission |
| localStorage unavailable (private browsing) | Generate ephemeral session_id in memory; warn user history won't persist |
| Backend returns CORS error | Display: "Unable to connect to the assistant. Please check your connection and try again." |
| Chat history API returns error | Fail gracefully; show empty chat with ability to start new conversation |
| Streaming response interrupted mid-stream | Display partial response with "Response interrupted. Tap to retry." |
| User rapidly submits multiple questions | Queue submissions and display "Processing previous request..." for subsequent ones |
| Backend returns 429 (rate limit) | Display: "Too many requests. Please wait a moment and try again." |
| Backend returns 500 (server error) | Display: "Something went wrong on our end. Please try again later." with retry button |
| Network timeout (> 30 seconds) | Display: "Request timed out. Please check your connection." with retry button |

---

## API Contracts _(mandatory)_

### Request Types (TypeScript)

```typescript
// Chat request sent to backend
interface ChatRequest {
  query: string;                    // 1-32000 characters
  selected_text?: string | null;    // 0-64000 characters (optional)
  session_id?: string | null;       // UUID v4 (generated if missing)
  filters?: {
    source_url_prefix?: string | null;
    section?: string | null;
  } | null;
}

// History request
interface HistoryRequest {
  session_id: string;               // UUID v4
  limit?: number;                   // Default 50, max 100
}
```

### Response Types (TypeScript)

```typescript
// Source citation in response
interface SourceCitation {
  source_url: string;               // Full URL to book section
  title: string;                    // Document/chapter title
  section: string;                  // Section/heading name
  chunk_position: number;           // Position in source
  similarity_score: number;         // 0.0-1.0
  snippet: string;                  // First 200 characters
}

// Response metadata
interface ResponseMetadata {
  query_time_ms: number;            // Total processing time
  retrieval_count: number;          // Number of chunks retrieved
  mode: 'full' | 'selected_text' | 'retrieval_only' | 'no_results';
  low_confidence: boolean;          // True if scores 0.3-0.5
  request_id: string;               // UUID for tracing
}

// Main chat response
interface ChatResponse {
  answer: string | null;            // AI response (null if unavailable)
  fallback_message?: string | null; // Shown when answer is null
  sources: SourceCitation[];        // Array of citations
  metadata: ResponseMetadata;
  session_id: string;               // Client session identifier
}

// Error response
interface ErrorResponse {
  error_code: string;               // Machine-readable code
  message: string;                  // Human-readable message
  request_id: string;               // UUID for tracing
  details?: Record<string, any>;    // Additional context
}

// History entry (backend format - each entry is one conversation turn)
interface HistoryEntry {
  timestamp: string;                // ISO 8601
  query: string;                    // User's question
  response: string;                 // Agent's answer
  sources?: SourceCitation[];       // Citations for the response
}

// History response
interface HistoryResponse {
  session_id: string;
  entries: HistoryEntry[];          // Array of conversation turns
  total_entries: number;
}

// NOTE: Frontend must transform each HistoryEntry into TWO ChatMessages:
// - User message: { role: 'user', content: entry.query, timestamp }
// - Assistant message: { role: 'assistant', content: entry.response, sources, timestamp }
```

### Frontend State Types

```typescript
// Chat UI state
interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  isOpen: boolean;
  mode: 'full' | 'selected_text';
  selectedText: string | null;
}

// Individual message in UI
interface ChatMessage {
  id: string;                       // Client-generated UUID
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: SourceCitation[];
  isStreaming?: boolean;
  error?: string;
}

// Session state
interface SessionState {
  sessionId: string | null;
  isNewSession: boolean;
  storageAvailable: boolean;
}
```

---

## Error-to-UI Mapping _(mandatory)_

| Error Code | HTTP Status | User Message | Action |
|------------|-------------|--------------|--------|
| `VALIDATION_ERROR` | 400 | "Please enter a valid question." | Focus input field |
| `RATE_LIMITED` | 429 | "Too many requests. Please wait a moment and try again." | Disable input for 5s, show countdown |
| `SERVICE_UNAVAILABLE` | 503 | "The assistant is temporarily unavailable. Please try again." | Show retry button |
| `INTERNAL_ERROR` | 500 | "Something went wrong. Please try again later." | Show retry button |
| `CORS_ERROR` | N/A | "Unable to connect to the assistant. Please check your connection." | Show retry button |
| `NETWORK_ERROR` | N/A | "Network error. Please check your internet connection." | Show retry button |
| `TIMEOUT` | N/A | "Request timed out. Please try again." | Show retry button |
| `NO_RESULTS` | 200 | "I couldn't find relevant information in the book for your question." | Suggest rephrasing |
| `LOW_CONFIDENCE` | 200 | Show answer with disclaimer: "This answer may not be fully accurate." | Display normally |
| `SESSION_ERROR` | 400/404 | "Session error. Starting a new conversation." | Clear session, continue |

---

## Requirements _(mandatory)_

### Functional Requirements

**Chat UI Component**

- **FR-001**: System MUST implement an Alibaba ChatUI-based chat component embedded in the Docusaurus site.
- **FR-002**: System MUST display a floating chat trigger button on all book pages (bottom-right corner by default).
- **FR-003**: System MUST support expanding/collapsing the chat panel without losing conversation state.
- **FR-004**: Chat messages MUST render markdown content including code blocks, lists, and emphasis.
- **FR-005**: System MUST display a loading indicator while waiting for backend response.
- **FR-006**: System MUST auto-scroll to the latest message when new content arrives.

**Backend Integration**

- **FR-007**: System MUST send chat requests to the FastAPI `/chat` endpoint with `query`, `selected_text` (optional), and `session_id`.
- **FR-008**: System MUST handle streaming responses via the `/chat/stream` SSE endpoint.
- **FR-009**: System MUST parse and display source citations from the `sources` array in backend responses.
- **FR-010**: System MUST include `session_id` in all requests; generate UUID v4 if not stored.
- **FR-011**: System MUST call `/history/{session_id}` on initialization to load previous conversation.

**Selected-Text Mode**

- **FR-012**: System MUST capture text selection from book content pages using browser Selection API.
- **FR-013**: System MUST display a contextual "Ask about selection" button when text is selected.
- **FR-014**: System MUST send `selected_text` field to backend when user submits from selection mode.
- **FR-015**: System MUST clearly indicate in the UI when the chat is in "selected-text" mode vs. "full book" mode.
- **FR-016**: System MUST allow user to clear the selection and return to normal mode.

**Session & History**

- **FR-017**: System MUST store `session_id` in browser localStorage with key `chatui_session_id`.
- **FR-018**: System MUST retrieve session_id from localStorage on page load to maintain session continuity.
- **FR-019**: System MUST fetch conversation history from backend when session_id exists.
- **FR-020**: System MUST display historical messages before new messages in the chat timeline.

**Error Handling**

- **FR-021**: System MUST display user-friendly error messages mapped from error codes (see Error-to-UI Mapping).
- **FR-022**: System MUST provide retry functionality for transient errors (network, timeout, 5xx).
- **FR-023**: System MUST handle CORS errors specifically with actionable guidance.
- **FR-024**: System MUST gracefully degrade when optional features fail (history, streaming).

**CORS Configuration (Backend)**

- **FR-025**: Backend MUST configure CORS middleware with environment-variable-based origin allowlist.
- **FR-026**: Backend MUST allow `http://localhost:3000` and `http://localhost:5173` for local development.
- **FR-027**: Backend MUST allow production domain: `https://hackathon-i-physical-ai-humanoid-ro-dun.vercel.app`.
- **FR-027a**: Vercel preview deployments will experience CORS errors (acceptable for development workflow).
- **FR-028**: Backend MUST NOT use wildcard (`*`) origins in production configuration.

---

### Key Entities

- **ChatMessage**: A single message in the conversation; attributes include role (user|assistant), content (string), timestamp (ISO 8601), sources (optional array of citations).
- **ChatSession**: Client-side session state; attributes include session_id (UUID v4), messages (array of ChatMessage), mode (full|selected_text), selectedText (optional string).
- **SourceCitation**: Reference displayed to user; attributes include title (string), url (string), snippet (string, first 200 chars), similarity_score (number).
- **SelectionContext**: Captured text selection; attributes include text (string), pageUrl (string), capturedAt (timestamp).

---

## Success Criteria _(mandatory)_

### Measurable Outcomes

| ID | Criterion | Measurement Method |
|----|-----------|-------------------|
| **SC-001** | User can open chat widget and receive response to book question within 5 seconds | Manual test: time from submit to first response token |
| **SC-002** | 100% of responses with sources display clickable citation links | Automated test: verify all `sources[]` items render as `<a>` tags |
| **SC-003** | Selected-text mode captures and sends text in 100% of test cases | Automated test: mock Selection API, verify `selected_text` in request |
| **SC-004** | Chat history persists across browser sessions | Manual test: close browser, reopen, verify history loads |
| **SC-005** | Zero CORS errors from allowed origins | Automated test: requests from localhost:3000 and production domain succeed |
| **SC-006** | Error scenarios display user-friendly messages (no raw errors) | Manual test: disconnect backend, verify message matches Error-to-UI table |
| **SC-007** | Chat UI usable on mobile viewports (320px-767px) | Manual test: use device emulation, verify all buttons/inputs accessible |
| **SC-008** | Streaming responses show first token within 1 second | Manual test: time from submit to first streamed character |

---

## Test Scenarios _(mandatory)_

| # | Scenario | Steps | Expected Result |
|---|----------|-------|-----------------|
| 1 | Basic Q&A | Open chat → Type "What is inverse kinematics?" → Submit | Response with sources within 5s |
| 2 | Citation Navigation | Click any source link in response | Browser navigates to correct book section |
| 3 | Selected-Text Mode | Select text on page → Click "Ask about selection" → Ask question | Response references only selected text |
| 4 | Session Persistence | Send message → Close browser → Reopen site → Open chat | Previous conversation displayed |
| 5 | Error Recovery | Disconnect network → Submit question → Reconnect → Click Retry | Error message shown, retry succeeds |
| 6 | Mobile Responsiveness | Open chat on 375px viewport | Full-screen overlay, all controls accessible |
| 7 | Rapid Submission | Submit 3 questions quickly | First processes, others queued with message |
| 8 | Empty Sources | Ask question with no book matches | Answer shown with "No specific sources cited" note |

---

## Constraints

### Frontend Constraints

- **FC-001**: Frontend framework: Docusaurus 3.9.2 with React 19.0.0
- **FC-002**: Chat component: `@chatui/core` v2.4.2 (Alibaba ChatUI - free, open-source, MIT licensed)
- **FC-003**: Styling: Tailwind CSS v4.1.17 (already configured)
- **FC-004**: State management: React hooks (useState, useEffect, useCallback) + localStorage
- **FC-005**: No additional state management libraries (Redux, Zustand) required
- **FC-006**: TypeScript 5.6.2 for type safety

### Backend Constraints

- **BC-001**: Existing FastAPI endpoints in `backend/app.py` remain unchanged
- **BC-002**: CORS configuration uses existing middleware at `backend/app.py:176-183`
- **BC-003**: Use existing endpoints: `/chat` (line 354), `/chat/stream` (line 543), `/history/{session_id}` (line 625), `/health` (line 291)
- **BC-004**: Environment variable `CORS_ORIGINS` controls allowed origins

### Environment Constraints

- **EC-001**: Frontend configuration via `docusaurus.config.ts` customFields (NOT `NEXT_PUBLIC_*` which is Next.js only)
- **EC-002**: Local development: `BACKEND_URL=http://localhost:8000` in `.env`, accessed via `siteConfig.customFields.backendUrl`
- **EC-003**: Production: `BACKEND_URL` set in Vercel environment variables, built into customFields at build time
- **EC-004**: Backend `CORS_ORIGINS` must include all frontend origins (comma-separated)
- **EC-005**: No secrets stored in frontend code or localStorage

### Integration Constraints

- **IC-001**: Frontend deployed on Vercel (same as Docusaurus book)
- **IC-002**: Backend deployed separately (Railway/Render/etc.)
- **IC-003**: All communication via HTTPS in production
- **IC-004**: Session IDs are client-generated UUIDs, not server-assigned

### File Structure (Frontend)

```
physical-ai-robotics-book/
├── src/
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatWidget.tsx       # Main chat container/trigger
│   │   │   ├── ChatPanel.tsx        # Expanded chat interface
│   │   │   ├── ChatMessage.tsx      # Individual message component
│   │   │   ├── ChatInput.tsx        # Input field with send button
│   │   │   ├── SourceCitations.tsx  # Citation list component
│   │   │   └── index.ts             # Exports
│   │   └── TextSelection/
│   │       ├── SelectionPopup.tsx   # "Ask about selection" button
│   │       └── index.ts
│   ├── hooks/
│   │   ├── useChat.ts               # Chat state and API logic
│   │   ├── useTextSelection.ts      # Text selection capture
│   │   └── useSession.ts            # Session/localStorage management
│   ├── services/
│   │   ├── chatApi.ts               # Backend API client
│   │   └── config.ts                # Environment configuration
│   └── theme/
│       └── Layout/
│           └── index.tsx            # Wrap layout with chat provider
├── static/
│   └── ...
└── docusaurus.config.ts
```

---

## Assumptions

- `@chatui/core` (Alibaba ChatUI) library is compatible with Docusaurus 3.x and React 19. **VERIFICATION REQUIRED**: ChatUI v2.4.2 was built for React 16-18; compatibility with React 19 should be tested in Phase 0 before implementation begins. If incompatible, fallback to custom chat component using Tailwind CSS.
- The existing FastAPI backend is deployed and accessible from the frontend at a known URL.
- Browser Selection API is supported by target browsers (Chrome, Firefox, Safari, Edge - last 2 versions).
- Vercel deployment supports environment variables for configuring the backend API URL.
- The Docusaurus book structure allows injecting custom React components via theme wrapping.
- Network latency between frontend (Vercel) and backend is under 200ms typically.
- Backend is deployed and passing `/health` checks before frontend integration begins.

---

## Not Building (Out of Scope)

**Authentication & Authorization**
- User authentication or login flows (sessions are anonymous)
- User accounts or profiles
- Role-based access control

**Internationalization & Accessibility**
- Multi-language support (English only)
- Screen reader optimization beyond basic ARIA (deferred)
- Voice input/output for chat

**Advanced Features**
- Chat history export or download feature
- File upload in chat (images, PDFs)
- Chat moderation or content filtering UI
- Custom chat themes or appearance settings
- Typing indicators showing "Assistant is typing..."
- Read receipts or message status indicators
- Chat reactions or feedback (thumbs up/down)

**Infrastructure & Operations**
- Admin dashboard for monitoring chat usage
- Push notifications for new messages
- Offline mode or service worker caching for chat
- Chat analytics or usage tracking dashboard
- A/B testing framework for chat UI
- Rate limiting UI (handled by backend 429 responses)

**Session Management**
- "Clear History" button (deferred to Phase 2)
- Multiple conversation threads
- Conversation search

---

## Clarifications & Decisions

### Chat UI Library Decision

**Decision**: Use `@chatui/core` v2.4.2 (Alibaba ChatUI)

**Rationale**:
- 100% free and open-source (MIT license)
- No vendor lock-in - works with any backend
- TypeScript support with predictable static types
- Responsive design adapts to any device
- Powerful theme customization
- Internationalization support
- Accessibility certified
- Active maintenance by Alibaba

**Trade-offs vs OpenAI ChatKit**:
- ChatUI requires manual backend integration (not a limitation for our custom FastAPI backend)
- No built-in OpenAI streaming support (we implement our own SSE handling)
- More flexible but requires slightly more setup code

### Production Domain

**Decision**: Production domain is `https://hackathon-i-physical-ai-humanoid-ro-dun.vercel.app`

**Action Required**: Add this domain to `CORS_ORIGINS` environment variable in backend deployment.

### Vercel Preview Strategy

**Decision**: Accept CORS errors on Vercel preview deployments

**Rationale**:
- Simplest approach for hackathon timeline
- Preview deployments use dynamic URLs that can't be pre-configured
- Test on production domain after merge

### Backend URL Discovery

**Decision**: Use Docusaurus `customFields` pattern in `docusaurus.config.ts`

**Rationale**:
- Docusaurus is NOT Next.js; `NEXT_PUBLIC_*` variables don't work
- `customFields` is the Docusaurus-native approach for runtime configuration
- Accessed via `useDocusaurusContext()` → `siteConfig.customFields.backendUrl`
- Environment variable `BACKEND_URL` is read at build time and baked into config

---

## References

- Backend API implementation: `backend/app.py`
- Backend models: `backend/models/request.py`, `backend/models/response.py`
- Spec-005 (RAG Agent API): `specs/005-rag-agent-api/spec.md`
- Docusaurus config: `physical-ai-robotics-book/docusaurus.config.ts`
- Frontend package: `physical-ai-robotics-book/package.json`
