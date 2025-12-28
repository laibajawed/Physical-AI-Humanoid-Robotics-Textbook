/**
 * API client for ChatKit Frontend.
 *
 * Provides functions for communicating with the FastAPI backend:
 * - sendChatMessage() - Non-streaming chat request
 * - streamChatMessage() - SSE streaming chat request
 * - getHistory() - Conversation history retrieval
 * - transformHistoryToMessages() - Backend to UI format conversion
 *
 * @spec 006-chatkit-frontend
 */

import { CONFIG } from './config';
import { ChatApiError, ErrorCodes, createNetworkError } from './errors';
import { getAuthToken } from '../lib/auth-client';
import type {
  ChatRequest,
  ChatResponse,
  ChatMessage,
  HistoryEntry,
  HistoryResponse,
  SourceCitation,
} from '../types/chat';

// =============================================================================
// Non-Streaming Chat API (TASK-6.5)
// =============================================================================

/**
 * Send a chat message and receive a complete response.
 *
 * Posts to /chat endpoint and returns the full response.
 * Use streamChatMessage() for streaming responses.
 *
 * @param backendUrl - Backend API base URL (from useBackendUrl hook)
 * @param request - Chat request with query, selected_text, session_id
 * @returns Promise resolving to ChatResponse
 * @throws ChatApiError on HTTP or network errors
 *
 * @example
 * ```typescript
 * const backendUrl = useBackendUrl();
 * const response = await sendChatMessage(backendUrl, {
 *   query: "What is inverse kinematics?",
 *   session_id: sessionId,
 * });
 * ```
 */
export async function sendChatMessage(
  backendUrl: string,
  request: ChatRequest,
): Promise<ChatResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT_MS);

  // Get auth token for authenticated requests
  const token = await getAuthToken();

  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    // Add authorization header if authenticated
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${backendUrl}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      // Try to parse error response
      try {
        const errorData = await response.json();
        throw new ChatApiError(
          errorData.error_code || ErrorCodes.INTERNAL_ERROR,
          errorData.message || 'Request failed',
          response.status,
          errorData.details,
        );
      } catch (parseError) {
        if (parseError instanceof ChatApiError) {
          throw parseError;
        }
        throw new ChatApiError(
          ErrorCodes.INTERNAL_ERROR,
          `Request failed with status ${response.status}`,
          response.status,
        );
      }
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof ChatApiError) {
      throw error;
    }

    throw createNetworkError(error);
  }
}

// =============================================================================
// Streaming Chat API (TASK-6.6)
// =============================================================================

/**
 * Stream a chat response via Server-Sent Events.
 *
 * Posts to /chat/stream and calls callbacks as SSE events arrive.
 * Returns an abort function to cancel the stream.
 *
 * Event types from backend:
 * - delta: Partial answer text
 * - sources: Citation data (sent at end)
 * - done: Stream complete
 * - error: Error occurred
 *
 * @param backendUrl - Backend API base URL
 * @param request - Chat request with query, selected_text, session_id
 * @param onDelta - Called for each partial answer text
 * @param onSources - Called when sources are received
 * @param onError - Called on error
 * @param onDone - Called when stream completes
 * @returns Abort function to cancel the stream
 *
 * @example
 * ```typescript
 * const abort = streamChatMessage(
 *   backendUrl,
 *   { query: "What is ROS2?", session_id },
 *   (delta) => setContent(prev => prev + delta),
 *   (sources) => setSources(sources),
 *   (error) => setError(error),
 *   () => setIsLoading(false),
 * );
 *
 * // To cancel:
 * abort();
 * ```
 */
export function streamChatMessage(
  backendUrl: string,
  request: ChatRequest,
  onDelta: (delta: string) => void,
  onSources: (sources: SourceCitation[]) => void,
  onError: (error: string) => void,
  onDone: () => void,
): () => void {
  const controller = new AbortController();

  // Start the fetch in the background
  (async () => {
    try {
      // Get auth token for authenticated requests
      const token = await getAuthToken();

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      // Add authorization header if authenticated
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${backendUrl}/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      if (!response.ok) {
        // Try to get error details
        try {
          const errorData = await response.json();
          onError(errorData.message || `Request failed with status ${response.status}`);
        } catch {
          onError(`Request failed with status ${response.status}`);
        }
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        onError('Response body is not readable');
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        // Append new data to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;

            try {
              const data = JSON.parse(jsonStr);

              // Handle different event types
              if (data.delta !== undefined) {
                onDelta(data.delta);
              } else if (data.sources !== undefined) {
                onSources(data.sources);
              } else if (data.error !== undefined) {
                onError(data.error);
              } else if (data.done === true) {
                onDone();
              }
            } catch (parseError) {
              // Skip malformed JSON lines
              console.warn('Failed to parse SSE data:', jsonStr);
            }
          }
        }
      }

      // Process any remaining data in buffer
      if (buffer.startsWith('data: ')) {
        const jsonStr = buffer.slice(6).trim();
        if (jsonStr) {
          try {
            const data = JSON.parse(jsonStr);
            if (data.done === true) {
              onDone();
            }
          } catch {
            // Ignore final parse errors
          }
        }
      }
    } catch (error) {
      // Don't report abort errors (user cancelled)
      if (error instanceof Error && error.name === 'AbortError') {
        return;
      }

      onError(error instanceof Error ? error.message : 'Stream failed');
    }
  })();

  // Return abort function
  return () => controller.abort();
}

// =============================================================================
// History API (TASK-6.7)
// =============================================================================

/**
 * Get conversation history for a session.
 *
 * Fetches history from /history/{session_id} endpoint.
 * Returns empty array for new sessions (404 response).
 *
 * @param backendUrl - Backend API base URL
 * @param sessionId - Session UUID
 * @returns Promise resolving to array of HistoryEntry
 * @throws ChatApiError on non-404 errors
 *
 * @example
 * ```typescript
 * const entries = await getHistory(backendUrl, sessionId);
 * const messages = transformHistoryToMessages(entries);
 * ```
 */
export async function getHistory(
  backendUrl: string,
  sessionId: string,
): Promise<HistoryEntry[]> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT_MS);

  // Get auth token for authenticated requests
  const token = await getAuthToken();

  const headers: Record<string, string> = {};
  
  // Add authorization header if authenticated
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(
      `${backendUrl}/history/${sessionId}?limit=${CONFIG.HISTORY_LIMIT}`,
      {
        method: 'GET',
        headers,
        signal: controller.signal,
      },
    );

    clearTimeout(timeoutId);

    // 404 means new session with no history - return empty array
    if (response.status === 404) {
      return [];
    }

    if (!response.ok) {
      throw new ChatApiError(
        ErrorCodes.HISTORY_ERROR,
        `Failed to load history: ${response.status}`,
        response.status,
      );
    }

    const data: HistoryResponse = await response.json();
    return data.entries;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof ChatApiError) {
      throw error;
    }

    // Don't fail hard on history errors - just return empty
    console.warn('Failed to load history:', error);
    return [];
  }
}

// =============================================================================
// History Transformation (TASK-6.7)
// =============================================================================

/**
 * Transform backend HistoryEntry to UI ChatMessage array.
 *
 * Backend stores each conversation turn as {query, response} pairs,
 * but the UI displays individual messages with {role, content}.
 * This function transforms each HistoryEntry into TWO ChatMessages:
 * - User message with the query
 * - Assistant message with the response and sources
 *
 * @param entries - Array of HistoryEntry from backend
 * @returns Array of ChatMessage for UI display
 *
 * @example
 * ```typescript
 * // Backend format (one entry per turn)
 * const entries = [{ timestamp, query: "Question?", response: "Answer", sources: [...] }];
 *
 * // UI format (two messages per turn)
 * const messages = transformHistoryToMessages(entries);
 * // [
 * //   { role: 'user', content: "Question?", ... },
 * //   { role: 'assistant', content: "Answer", sources: [...], ... }
 * // ]
 * ```
 */
export function transformHistoryToMessages(entries: HistoryEntry[]): ChatMessage[] {
  const messages: ChatMessage[] = [];

  for (const entry of entries) {
    const timestamp = new Date(entry.timestamp);

    // User message
    messages.push({
      id: `${entry.timestamp}-user`,
      role: 'user',
      content: entry.query,
      timestamp,
    });

    // Assistant message
    messages.push({
      id: `${entry.timestamp}-assistant`,
      role: 'assistant',
      content: entry.response,
      timestamp,
      sources: entry.sources,
    });
  }

  return messages;
}

// =============================================================================
// Validation Helpers
// =============================================================================

/**
 * Validate query before sending to backend.
 *
 * @param query - Query string to validate
 * @returns Error message or null if valid
 */
export function validateQuery(query: string): string | null {
  if (!query || query.trim().length === 0) {
    return 'Please enter a question';
  }

  if (query.length > CONFIG.MAX_QUERY_LENGTH) {
    return `Question is too long (max ${CONFIG.MAX_QUERY_LENGTH.toLocaleString()} characters)`;
  }

  return null;
}

/**
 * Validate selection before using in selected-text mode.
 *
 * @param text - Selected text to validate
 * @returns Error message or null if valid
 */
export function validateSelection(text: string): string | null {
  if (text.length < CONFIG.MIN_SELECTION_LENGTH) {
    return 'Please select more text for better results';
  }

  if (text.length > CONFIG.MAX_SELECTION_LENGTH) {
    return `Selection is too long (max ${CONFIG.MAX_SELECTION_LENGTH.toLocaleString()} characters)`;
  }

  return null;
}
