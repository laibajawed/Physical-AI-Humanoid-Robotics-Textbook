/**
 * TypeScript interfaces for ChatKit Frontend Integration.
 *
 * Maps to backend models in backend/models/
 * - ChatRequest -> backend/models/request.py:ChatRequest
 * - ChatResponse -> backend/models/response.py:ChatResponse
 * - HistoryEntry -> backend/models/session.py:HistoryEntry
 *
 * @spec 006-chatkit-frontend
 */

// =============================================================================
// API Request Types
// =============================================================================

/**
 * Metadata filter for scoping search results.
 * Maps to: backend/models/request.py:MetadataFilter
 */
export interface MetadataFilter {
  source_url_prefix?: string | null;
  section?: string | null;
}

/**
 * Chat request sent to backend.
 * Maps to: backend/models/request.py:ChatRequest
 */
export interface ChatRequest {
  /** User's question (1-32000 characters) */
  query: string;
  /** Selected text for grounding (0-64000 characters, optional) */
  selected_text?: string | null;
  /** Session UUID v4 (generated if missing) */
  session_id?: string | null;
  /** Optional metadata filters */
  filters?: MetadataFilter | null;
}

// =============================================================================
// API Response Types
// =============================================================================

/**
 * Source citation from Qdrant retrieval.
 * Maps to: backend/models/response.py:SourceCitation
 */
export interface SourceCitation {
  /** Full URL to book section */
  source_url: string;
  /** Document/chapter title */
  title: string;
  /** Section/heading name */
  section: string;
  /** Position in source document (0-indexed) */
  chunk_position: number;
  /** Cosine similarity score (0.0-1.0) */
  similarity_score: number;
  /** First 200 characters preview */
  snippet: string;
}

/**
 * Citation for selected-text mode responses.
 * Maps to: backend/models/response.py:SelectedTextCitation
 */
export interface SelectedTextCitation {
  /** Always 'selected_text' for this type */
  source_type: 'selected_text';
  /** Character count of provided selection */
  selection_length: number;
  /** First 200 chars of selection for preview */
  snippet: string;
  /** How the selection relates to the answer */
  relevance_note: string;
}

/**
 * Response metadata from backend.
 * Maps to: backend/models/response.py:ResponseMetadata
 */
export interface ResponseMetadata {
  /** Total processing time in milliseconds */
  query_time_ms: number;
  /** Number of chunks retrieved from Qdrant */
  retrieval_count: number;
  /** Response mode */
  mode: 'full' | 'selected_text' | 'retrieval_only' | 'no_results';
  /** True if best results had scores 0.3-0.5 */
  low_confidence: boolean;
  /** UUID for request tracing */
  request_id: string;
}

/**
 * Main chat response from backend.
 * Maps to: backend/models/response.py:ChatResponse
 */
export interface ChatResponse {
  /** AI-generated answer (null if unavailable) */
  answer: string | null;
  /** Message when answer is null (graceful degradation) */
  fallback_message?: string | null;
  /** Array of citations */
  sources: (SourceCitation | SelectedTextCitation)[];
  /** Response metadata */
  metadata: ResponseMetadata;
  /** Session ID (provided or newly generated) */
  session_id: string;
}

/**
 * Error response from backend.
 * Maps to: backend/models/response.py:ErrorResponse
 */
export interface ErrorResponse {
  /** Machine-readable error code */
  error_code: string;
  /** Human-readable error description */
  message: string;
  /** UUID for request tracing */
  request_id: string;
  /** Additional error context */
  details?: Record<string, unknown>;
}

// =============================================================================
// History Types
// =============================================================================

/**
 * Single conversation turn from history.
 * Maps to: backend/models/session.py:HistoryEntry
 *
 * NOTE: Backend stores each turn as query+response pair, NOT role+content.
 * Frontend must transform this for UI display using transformHistoryToMessages().
 */
export interface HistoryEntry {
  /** ISO 8601 timestamp - when the exchange occurred */
  timestamp: string;
  /** User's question */
  query: string;
  /** Agent's answer */
  response: string;
  /** Citations for the answer */
  sources?: SourceCitation[];
}

/**
 * History response from backend.
 * Maps to: backend/models/session.py:ConversationHistoryResponse
 */
export interface HistoryResponse {
  /** Session UUID */
  session_id: string;
  /** Array of conversation turns (NOT "messages") */
  entries: HistoryEntry[];
  /** Total number of entries (NOT "total_count") */
  total_entries: number;
}

// =============================================================================
// Frontend UI State Types
// =============================================================================

/**
 * Individual message in UI.
 * Used in: src/components/Chat/ChatMessage.tsx
 */
export interface ChatMessage {
  /** Client-generated unique ID */
  id: string;
  /** Message role */
  role: 'user' | 'assistant';
  /** Message content */
  content: string;
  /** When message was created */
  timestamp: Date;
  /** Source citations (assistant messages only) */
  sources?: SourceCitation[];
  /** True if message is still streaming */
  isStreaming?: boolean;
  /** Error message if failed */
  error?: string;
}

/**
 * Chat UI state.
 * Used in: src/hooks/useChat.ts
 */
export interface ChatState {
  /** Array of chat messages */
  messages: ChatMessage[];
  /** True while waiting for response */
  isLoading: boolean;
  /** Current error message or null */
  error: string | null;
  /** True if chat panel is visible */
  isOpen: boolean;
  /** Current query mode */
  mode: 'full' | 'selected_text';
  /** Selected text context or null */
  selectedText: SelectionContext | null;
}

/**
 * Session state from localStorage.
 * Used in: src/hooks/useSession.ts
 */
export interface SessionState {
  /** Session UUID (never null after init) */
  sessionId: string;
  /** True if this is a new session (no history) */
  isNewSession: boolean;
  /** True if localStorage is available */
  storageAvailable: boolean;
}

/**
 * Selection context for selected-text mode.
 * Used in: src/hooks/useTextSelection.ts
 */
export interface SelectionContext {
  /** Selected text content */
  text: string;
  /** Current page URL where selection was made */
  sourceUrl: string;
  /** When selection was captured */
  capturedAt: Date;
}

// =============================================================================
// Streaming Event Types (SSE from /chat/stream)
// =============================================================================

/** SSE event type discriminator */
export type StreamEventType = 'delta' | 'sources' | 'done' | 'error';

/** Partial answer text event */
export interface StreamDeltaEvent {
  delta: string;
}

/** Sources and metadata event */
export interface StreamSourcesEvent {
  sources: SourceCitation[];
  metadata: {
    query_time_ms: number;
    mode: string;
    session_id: string;
  };
}

/** Stream completion event */
export interface StreamDoneEvent {
  done: true;
}

/** Error event */
export interface StreamErrorEvent {
  error: string;
}

/** Union type for all stream events */
export type StreamEvent =
  | StreamDeltaEvent
  | StreamSourcesEvent
  | StreamDoneEvent
  | StreamErrorEvent;

// =============================================================================
// Chat Action Types (for useReducer)
// =============================================================================

/** Action types for chat state reducer */
export type ChatAction =
  | { type: 'OPEN' }
  | { type: 'CLOSE' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'UPDATE_LAST_MESSAGE'; payload: Partial<ChatMessage> }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_SELECTED_TEXT'; payload: SelectionContext | null }
  | { type: 'LOAD_HISTORY'; payload: ChatMessage[] }
  | { type: 'CLEAR_SELECTION' };
