# Quickstart: Spec-4 ChatKit Frontend Integration

**Feature**: 006-chatkit-frontend
**Phase**: 1 - Design
**Date**: 2025-12-18

---

## Prerequisites

Before starting, ensure:

1. **Backend is running** at `http://localhost:8000`
   ```bash
   cd backend
   python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Backend health check passes**:
   ```bash
   curl http://localhost:8000/health
   # Expected: {"status":"healthy",...}
   ```

3. **Dependencies installed** in Docusaurus:
   ```bash
   cd physical-ai-robotics-book
   npm install
   ```

---

## Environment Setup

### Frontend Configuration

**IMPORTANT**: Docusaurus does NOT use `NEXT_PUBLIC_*` variables (that's Next.js).
Use `docusaurus.config.ts` customFields instead.

#### Step 1: Update docusaurus.config.ts

Add `customFields` to your config:

```typescript
// physical-ai-robotics-book/docusaurus.config.ts
const config: Config = {
  // ... existing config
  customFields: {
    backendUrl: process.env.BACKEND_URL || 'http://localhost:8000',
  },
  // ... rest of config
};
```

#### Step 2: Create .env file (optional for local dev)

Create `physical-ai-robotics-book/.env`:

```env
# Backend API URL (optional - defaults to localhost:8000)
BACKEND_URL=http://localhost:8000
```

#### Step 3: For production (Vercel)

Set `BACKEND_URL` in Vercel project settings → Environment Variables.

### Backend CORS Update

Update backend `CORS_ORIGINS` environment variable:

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://hackathon-i-physical-ai-humanoid-ro-dun.vercel.app
```

---

## File Structure

Create these files in `physical-ai-robotics-book/src/`:

```
src/
├── components/
│   ├── Chat/
│   │   ├── ChatWidget.tsx       # Main container + floating trigger
│   │   ├── ChatPanel.tsx        # Chat interface panel
│   │   ├── ChatMessage.tsx      # Individual message component
│   │   ├── ChatInput.tsx        # Input field with send button
│   │   ├── SourceCitations.tsx  # Citation list component
│   │   └── index.ts             # Barrel exports
│   └── TextSelection/
│       ├── SelectionPopup.tsx   # "Ask about selection" button
│       └── index.ts
├── hooks/
│   ├── useChat.ts               # Chat state + API logic
│   ├── useTextSelection.ts      # Text selection capture
│   └── useSession.ts            # Session/localStorage management
├── services/
│   ├── chatApi.ts               # Backend API client
│   └── config.ts                # Environment configuration
├── context/
│   └── ChatContext.tsx          # React Context provider
└── theme/
    └── Layout/
        └── index.tsx            # Wrap layout with ChatProvider
```

---

## Implementation Order

### Step 1: Configuration (src/services/config.ts)

```typescript
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';

// Static config values
export const CONFIG = {
  REQUEST_TIMEOUT_MS: 30000,
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 1000,
  SESSION_STORAGE_KEY: 'chatkit_session_id',
  MAX_QUERY_LENGTH: 32000,
  MAX_SELECTION_LENGTH: 64000,
  MIN_SELECTION_LENGTH: 20,
  HISTORY_LIMIT: 50,
} as const;

// Hook to get backend URL from Docusaurus config
export function useBackendUrl(): string {
  const { siteConfig } = useDocusaurusContext();
  return (siteConfig.customFields?.backendUrl as string) || 'http://localhost:8000';
}

// For non-React contexts (rare), use default
export const DEFAULT_BACKEND_URL = 'http://localhost:8000';
```

### Step 2: API Client (src/services/chatApi.ts)

```typescript
import { CONFIG } from './config';

// Types matching backend models/session.py
interface HistoryEntry {
  timestamp: string;
  query: string;      // User's question
  response: string;   // Agent's answer
  sources?: SourceCitation[];
}

interface ChatRequest {
  query: string;
  selected_text?: string | null;
  session_id?: string | null;
}

interface ChatResponse {
  answer: string | null;
  fallback_message?: string | null;
  sources: SourceCitation[];
  metadata: ResponseMetadata;
  session_id: string;
}

// API client functions take backendUrl as parameter (from hook)
export async function sendChatMessage(
  backendUrl: string,
  request: ChatRequest
): Promise<ChatResponse> {
  const response = await fetch(`${backendUrl}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new ChatApiError(error.error_code, error.message, response.status);
  }

  return response.json();
}

export function streamChatMessage(
  backendUrl: string,
  request: ChatRequest,
  onDelta: (delta: string) => void,
  onSources: (sources: SourceCitation[]) => void,
  onError: (error: string) => void,
  onDone: () => void
): () => void {
  const controller = new AbortController();

  fetch(`${backendUrl}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal: controller.signal,
  }).then(async (response) => {
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    while (reader) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      const lines = text.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          if (data.delta) onDelta(data.delta);
          if (data.sources) onSources(data.sources);
          if (data.error) onError(data.error);
          if (data.done) onDone();
        }
      }
    }
  }).catch((error) => {
    if (error.name !== 'AbortError') {
      onError(error.message);
    }
  });

  return () => controller.abort();
}

export async function getHistory(
  backendUrl: string,
  sessionId: string
): Promise<HistoryEntry[]> {
  const response = await fetch(
    `${backendUrl}/history/${sessionId}?limit=${CONFIG.HISTORY_LIMIT}`
  );

  if (response.status === 404) {
    return []; // New session, no history
  }

  if (!response.ok) {
    throw new ChatApiError('HISTORY_ERROR', 'Failed to load history', response.status);
  }

  const data = await response.json();
  return data.entries;  // Returns HistoryEntry[] with {timestamp, query, response, sources}
}

// Transform backend HistoryEntry to UI ChatMessage array
export function transformHistoryToMessages(entries: HistoryEntry[]): ChatMessage[] {
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

### Step 3: Session Hook (src/hooks/useSession.ts)

```typescript
import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { CONFIG } from '../services/config';

interface SessionState {
  sessionId: string;
  isNewSession: boolean;
  storageAvailable: boolean;
}

export function useSession(): SessionState {
  const [state, setState] = useState<SessionState>({
    sessionId: '',
    isNewSession: true,
    storageAvailable: true,
  });

  useEffect(() => {
    let storageAvailable = true;
    let sessionId: string;
    let isNewSession = false;

    try {
      const stored = localStorage.getItem(CONFIG.SESSION_STORAGE_KEY);
      if (stored && isValidUUID(stored)) {
        sessionId = stored;
      } else {
        sessionId = uuidv4();
        localStorage.setItem(CONFIG.SESSION_STORAGE_KEY, sessionId);
        isNewSession = true;
      }
    } catch {
      // localStorage unavailable (private browsing)
      storageAvailable = false;
      sessionId = uuidv4();
      isNewSession = true;
    }

    setState({ sessionId, isNewSession, storageAvailable });
  }, []);

  return state;
}

function isValidUUID(id: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(id);
}
```

### Step 4: Chat Hook (src/hooks/useChat.ts)

```typescript
import { useReducer, useCallback, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import {
  streamChatMessage,
  getHistory,
  transformHistoryToMessages,
} from '../services/chatApi';
import { useSession } from './useSession';
import { useBackendUrl } from '../services/config';

type ChatState = {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  isOpen: boolean;
  mode: 'full' | 'selected_text';
  selectedText: string | null;
};

type ChatAction =
  | { type: 'OPEN' }
  | { type: 'CLOSE' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'UPDATE_LAST_MESSAGE'; payload: Partial<ChatMessage> }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_SELECTED_TEXT'; payload: string | null }
  | { type: 'LOAD_HISTORY'; payload: ChatMessage[] };

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'OPEN':
      return { ...state, isOpen: true };
    case 'CLOSE':
      return { ...state, isOpen: false };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'UPDATE_LAST_MESSAGE':
      const messages = [...state.messages];
      messages[messages.length - 1] = { ...messages[messages.length - 1], ...action.payload };
      return { ...state, messages };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'SET_SELECTED_TEXT':
      return {
        ...state,
        selectedText: action.payload,
        mode: action.payload ? 'selected_text' : 'full',
      };
    case 'LOAD_HISTORY':
      return { ...state, messages: action.payload };
    default:
      return state;
  }
}

export function useChat() {
  const backendUrl = useBackendUrl();
  const { sessionId, isNewSession } = useSession();
  const [state, dispatch] = useReducer(chatReducer, {
    messages: [],
    isLoading: false,
    error: null,
    isOpen: false,
    mode: 'full',
    selectedText: null,
  });

  // Track streaming content
  const streamContentRef = useRef('');

  // Load history on mount - transform backend format to UI format
  useEffect(() => {
    if (sessionId && !isNewSession) {
      getHistory(backendUrl, sessionId)
        .then((entries) => {
          // Transform {query, response} pairs to {role, content} messages
          const messages = transformHistoryToMessages(entries);
          dispatch({ type: 'LOAD_HISTORY', payload: messages });
        })
        .catch(() => {
          // Silently fail, user can start fresh
        });
    }
  }, [backendUrl, sessionId, isNewSession]);

  const sendMessage = useCallback(
    async (query: string) => {
      dispatch({ type: 'SET_ERROR', payload: null });
      dispatch({ type: 'SET_LOADING', payload: true });
      streamContentRef.current = '';

      // Add user message
      const userMessage: ChatMessage = {
        id: uuidv4(),
        role: 'user',
        content: query,
        timestamp: new Date(),
      };
      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });

      // Add placeholder assistant message
      const assistantMessage: ChatMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      };
      dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });

      try {
        // Use streaming with backendUrl from hook
        const cancel = streamChatMessage(
          backendUrl,
          {
            query,
            selected_text: state.selectedText,
            session_id: sessionId,
          },
          (delta) => {
            streamContentRef.current += delta;
            dispatch({
              type: 'UPDATE_LAST_MESSAGE',
              payload: { content: streamContentRef.current },
            });
          },
          (sources) => {
            dispatch({ type: 'UPDATE_LAST_MESSAGE', payload: { sources } });
          },
          (error) => {
            dispatch({ type: 'UPDATE_LAST_MESSAGE', payload: { error } });
          },
          () => {
            dispatch({ type: 'UPDATE_LAST_MESSAGE', payload: { isStreaming: false } });
            dispatch({ type: 'SET_LOADING', payload: false });
          }
        );

        return cancel;
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: (error as Error).message });
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    },
    [backendUrl, sessionId, state.selectedText]
  );

  return {
    ...state,
    sendMessage,
    open: () => dispatch({ type: 'OPEN' }),
    close: () => dispatch({ type: 'CLOSE' }),
    setSelectedText: (text: string | null) => dispatch({ type: 'SET_SELECTED_TEXT', payload: text }),
    clearError: () => dispatch({ type: 'SET_ERROR', payload: null }),
  };
}
```

### Step 5: Chat Widget (src/components/Chat/ChatWidget.tsx)

```typescript
import React from 'react';
import { useChat } from '../../hooks/useChat';
import { ChatPanel } from './ChatPanel';

export function ChatWidget() {
  const chat = useChat();

  return (
    <>
      {/* Floating trigger button */}
      {!chat.isOpen && (
        <button
          onClick={chat.open}
          className="fixed bottom-4 right-4 z-50 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center transition-colors"
          aria-label="Open chat"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        </button>
      )}

      {/* Chat panel */}
      {chat.isOpen && (
        <ChatPanel
          messages={chat.messages}
          isLoading={chat.isLoading}
          error={chat.error}
          mode={chat.mode}
          selectedText={chat.selectedText}
          onSendMessage={chat.sendMessage}
          onClose={chat.close}
          onClearSelection={() => chat.setSelectedText(null)}
        />
      )}
    </>
  );
}
```

### Step 6: Layout Wrapper (src/theme/Layout/index.tsx)

```typescript
import React from 'react';
import Layout from '@theme-original/Layout';
import type { Props } from '@theme/Layout';
import { ChatWidget } from '../../components/Chat';

export default function LayoutWrapper(props: Props): JSX.Element {
  return (
    <>
      <Layout {...props} />
      <ChatWidget />
    </>
  );
}
```

---

## Running Locally

1. **Start backend**:
   ```bash
   cd backend
   python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start frontend**:
   ```bash
   cd physical-ai-robotics-book
   npm run start
   ```

3. **Test the integration**:
   - Open http://localhost:3000
   - Click the chat button (bottom-right)
   - Ask: "What is inverse kinematics?"
   - Verify response with citations

---

## E2E Smoke Test Checklist

| # | Test | Pass |
|---|------|------|
| 1 | Chat widget renders on all pages | ☐ |
| 2 | No CORS errors in browser console | ☐ |
| 3 | Chat completes with answer within 5s | ☐ |
| 4 | Citations render as clickable links | ☐ |
| 5 | History persists across browser sessions | ☐ |
| 6 | Selected-text mode works | ☐ |
| 7 | Error displays user-friendly message | ☐ |
| 8 | Mobile layout works (375px viewport) | ☐ |

---

## Troubleshooting

### CORS Errors
1. Check backend `CORS_ORIGINS` includes frontend URL
2. Restart backend after changing environment variables
3. Clear browser cache

### History Not Loading
1. Check localStorage in DevTools
2. Verify session_id format (UUID v4)
3. Check backend `/history` endpoint is accessible

### Streaming Not Working
1. Check network tab for `/chat/stream` request
2. Verify Content-Type is `text/event-stream`
3. Check for SSE parsing errors in console
