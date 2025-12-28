---
id: 1
title: Implement ChatKit Frontend Integration
stage: green
date: 2025-12-18
surface: agent
model: claude-sonnet-4-5-20250929
feature: 006-chatkit-frontend
branch: 006-chatkit-frontend
user: developer
command: /sp.implement
labels: ["chatkit", "frontend", "docusaurus", "react", "typescript"]
links:
  spec: specs/006-chatkit-frontend/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - physical-ai-robotics-book/src/types/chat.ts
  - physical-ai-robotics-book/src/services/config.ts
  - physical-ai-robotics-book/src/services/errors.ts
  - physical-ai-robotics-book/src/services/chatApi.ts
  - physical-ai-robotics-book/src/hooks/useSession.ts
  - physical-ai-robotics-book/src/hooks/useTextSelection.ts
  - physical-ai-robotics-book/src/hooks/useChat.ts
  - physical-ai-robotics-book/src/components/Chat/ChatMessage.tsx
  - physical-ai-robotics-book/src/components/Chat/SourceCitations.tsx
  - physical-ai-robotics-book/src/components/Chat/ChatInput.tsx
  - physical-ai-robotics-book/src/components/Chat/ChatPanel.tsx
  - physical-ai-robotics-book/src/components/Chat/ChatWidget.tsx
  - physical-ai-robotics-book/src/components/Chat/index.ts
  - physical-ai-robotics-book/src/components/TextSelection/SelectionPopup.tsx
  - physical-ai-robotics-book/src/components/TextSelection/index.ts
  - physical-ai-robotics-book/src/theme/Layout/index.tsx
  - backend/.env.example
  - physical-ai-robotics-book/.env.example
tests:
  - npm run typecheck - PASS
  - npm run build - PASS
---

## Prompt

Implement all tasks from TASK-6.1 through TASK-6.22 for the ChatKit frontend integration feature (006-chatkit-frontend). This includes:

### Phase 1: Foundation (Environment & Types)
- TASK-6.1: Add uuid dependency
- TASK-6.2: Add backendUrl to docusaurus.config.ts customFields
- TASK-6.3: Create TypeScript interfaces
- TASK-6.4: Create configuration service with useBackendUrl hook

### Phase 2: API Layer
- TASK-6.5: Create API client with sendChatMessage
- TASK-6.6: Add streaming support with streamChatMessage
- TASK-6.7: Add history retrieval

### Phase 3: State Management
- TASK-6.8: Create useSession hook
- TASK-6.9: Create useTextSelection hook
- TASK-6.10: Create useChat hook
- TASK-6.11: Add error handling utilities

### Phase 4: UI Components
- TASK-6.12: ChatMessage component
- TASK-6.13: SourceCitations component
- TASK-6.14: ChatInput component
- TASK-6.15: ChatPanel component
- TASK-6.16: ChatWidget component
- TASK-6.17: Barrel exports

### Phase 5: Text Selection
- TASK-6.18: SelectionPopup component
- TASK-6.19: Barrel export for TextSelection

### Phase 6: Integration
- TASK-6.20: Integrate into Layout
- TASK-6.21: Update backend CORS

### Phase 7: Verification
- TASK-6.22: E2E smoke tests

## Response snapshot

Successfully implemented complete ChatKit frontend integration with:

1. **TypeScript Types** (`src/types/chat.ts`): All interfaces from data-model.md including ChatRequest, ChatResponse, SourceCitation, HistoryEntry, ChatMessage, ChatState, SessionState, SelectionContext, and streaming event types.

2. **Configuration** (`src/services/config.ts`): Static CONFIG constants and useBackendUrl() hook using Docusaurus customFields pattern (not NEXT_PUBLIC_*).

3. **Error Handling** (`src/services/errors.ts`): ChatApiError class with error code mapping, user-friendly messages, and retry logic.

4. **API Client** (`src/services/chatApi.ts`):
   - sendChatMessage() for non-streaming requests
   - streamChatMessage() for SSE streaming
   - getHistory() for conversation history
   - transformHistoryToMessages() for backend to UI format conversion

5. **Hooks**:
   - useSession(): localStorage-based session management with UUID v4
   - useTextSelection(): Browser Selection API integration
   - useChat(): useReducer-based state management with streaming support

6. **UI Components**:
   - ChatMessage: Markdown rendering with code blocks, citations
   - SourceCitations: Clickable source links
   - ChatInput: Textarea with Enter to submit, validation
   - ChatPanel: Full chat interface with mobile responsiveness
   - ChatWidget: Floating trigger button entry point
   - SelectionPopup: "Ask about selection" button

7. **Integration**:
   - Layout wrapper with BrowserOnly for SSR safety
   - Backend .env.example with CORS_ORIGINS documentation

Build verification: `npm run typecheck` and `npm run build` both pass.

## Outcome

- Impact: Complete implementation of 21/22 tasks (E2E smoke test pending manual verification)
- Tests: TypeScript typecheck PASS, Docusaurus build PASS
- Files: 17 files created/modified
- Next prompts: Run E2E smoke tests manually, test with backend running
- Reflection: React 19 compatibility required using React.ReactElement instead of JSX.Element

## Evaluation notes (flywheel)

- Failure modes observed: JSX.Element type not found in React 19 environment
- Graders run and results (PASS/FAIL): typecheck PASS, build PASS
- Prompt variant (if applicable): spec4-backend-integrator agent
- Next experiment: Add unit tests for hooks and services
