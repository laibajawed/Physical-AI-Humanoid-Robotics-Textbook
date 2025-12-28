/**
 * Chat state management hook for ChatKit Frontend.
 *
 * Implements chat state with useReducer pattern per constraint FC-005
 * (no external state libraries). Manages messages, loading, errors,
 * and integrates with streaming API.
 *
 * @spec 006-chatkit-frontend
 */

import { useReducer, useCallback, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import {
  streamChatMessage,
  getHistory,
  transformHistoryToMessages,
} from '../services/chatApi';
import { getErrorMessage } from '../services/errors';
import { useSession } from './useSession';
import { useBackendUrl } from '../services/config';
import type {
  ChatState,
  ChatAction,
  ChatMessage,
  SelectionContext,
  SourceCitation,
} from '../types/chat';

// =============================================================================
// Initial State
// =============================================================================

const initialState: ChatState = {
  messages: [],
  isLoading: false,
  error: null,
  isOpen: false,
  mode: 'full',
  selectedText: null,
};

// =============================================================================
// Chat Reducer (TASK-6.10)
// =============================================================================

/**
 * Reducer for chat state management.
 *
 * Actions:
 * - OPEN: Show chat panel
 * - CLOSE: Hide chat panel
 * - SET_LOADING: Set loading state
 * - ADD_MESSAGE: Add new message
 * - UPDATE_LAST_MESSAGE: Update the last message (for streaming)
 * - SET_ERROR: Set error message
 * - SET_SELECTED_TEXT: Set selected text context
 * - LOAD_HISTORY: Load messages from history
 * - CLEAR_SELECTION: Clear selected text and return to full mode
 */
function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'OPEN':
      return { ...state, isOpen: true };

    case 'CLOSE':
      return { ...state, isOpen: false };

    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };

    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
      };

    case 'UPDATE_LAST_MESSAGE': {
      if (state.messages.length === 0) {
        return state;
      }
      const messages = [...state.messages];
      const lastIndex = messages.length - 1;
      messages[lastIndex] = {
        ...messages[lastIndex],
        ...action.payload,
      };
      return { ...state, messages };
    }

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

    case 'CLEAR_SELECTION':
      return {
        ...state,
        selectedText: null,
        mode: 'full',
      };

    default:
      return state;
  }
}

// =============================================================================
// useChat Hook Return Type
// =============================================================================

export interface UseChatReturn extends ChatState {
  /** Send a message to the chat */
  sendMessage: (query: string) => Promise<(() => void) | undefined>;
  /** Open the chat panel */
  open: () => void;
  /** Close the chat panel */
  close: () => void;
  /** Set selected text context */
  setSelectedText: (context: SelectionContext | null) => void;
  /** Clear current error */
  clearError: () => void;
  /** Clear selected text and return to full mode */
  clearSelection: () => void;
  /** Session ID for the current session */
  sessionId: string;
}

// =============================================================================
// useChat Hook (TASK-6.10)
// =============================================================================

/**
 * Main chat state management hook.
 *
 * Provides complete chat functionality including:
 * - State management with useReducer
 * - Streaming message support
 * - History loading on mount
 * - Selected text mode support
 * - Error handling
 *
 * @returns UseChatReturn with state and actions
 *
 * @example
 * ```typescript
 * function ChatWidget() {
 *   const {
 *     messages,
 *     isLoading,
 *     error,
 *     isOpen,
 *     mode,
 *     selectedText,
 *     sendMessage,
 *     open,
 *     close,
 *     setSelectedText,
 *     clearError,
 *   } = useChat();
 *
 *   const handleSend = async (query: string) => {
 *     await sendMessage(query);
 *   };
 * }
 * ```
 */
export function useChat(): UseChatReturn {
  const backendUrl = useBackendUrl();
  const { sessionId, isNewSession } = useSession();
  const [state, dispatch] = useReducer(chatReducer, initialState);

  // Track streaming content accumulation
  const streamContentRef = useRef('');

  // Track if history has been loaded
  const historyLoadedRef = useRef(false);

  // Load history on mount for existing sessions
  useEffect(() => {
    if (!sessionId || historyLoadedRef.current) {
      return;
    }

    // Don't load history for new sessions
    if (isNewSession) {
      historyLoadedRef.current = true;
      return;
    }

    // Load history
    const loadHistory = async () => {
      try {
        const entries = await getHistory(backendUrl, sessionId);
        if (entries.length > 0) {
          // Transform backend format to UI format
          const messages = transformHistoryToMessages(entries);
          dispatch({ type: 'LOAD_HISTORY', payload: messages });
        }
      } catch (error) {
        // Silently fail - user can still use chat without history
        console.warn('Failed to load chat history:', error);
      } finally {
        historyLoadedRef.current = true;
      }
    };

    loadHistory();
  }, [backendUrl, sessionId, isNewSession]);

  // Send message action
  const sendMessage = useCallback(
    async (query: string): Promise<(() => void) | undefined> => {
      if (!sessionId) {
        return undefined;
      }

      // Clear previous error
      dispatch({ type: 'SET_ERROR', payload: null });

      // Set loading state
      dispatch({ type: 'SET_LOADING', payload: true });

      // Reset stream content accumulator
      streamContentRef.current = '';

      // Add user message immediately
      const userMessage: ChatMessage = {
        id: uuidv4(),
        role: 'user',
        content: query,
        timestamp: new Date(),
      };
      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });

      // Add placeholder assistant message for streaming
      const assistantMessage: ChatMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      };
      dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });

      try {
        // Start streaming
        const cancelStream = streamChatMessage(
          backendUrl,
          {
            query,
            selected_text: state.selectedText?.text ?? null,
            session_id: sessionId,
          },
          // onDelta
          (delta: string) => {
            streamContentRef.current += delta;
            dispatch({
              type: 'UPDATE_LAST_MESSAGE',
              payload: { content: streamContentRef.current },
            });
          },
          // onSources
          (sources: SourceCitation[]) => {
            dispatch({
              type: 'UPDATE_LAST_MESSAGE',
              payload: { sources },
            });
          },
          // onError
          (errorMessage: string) => {
            dispatch({
              type: 'UPDATE_LAST_MESSAGE',
              payload: {
                isStreaming: false,
                error: errorMessage,
              },
            });
            dispatch({ type: 'SET_LOADING', payload: false });
            dispatch({ type: 'SET_ERROR', payload: errorMessage });
          },
          // onDone
          () => {
            dispatch({
              type: 'UPDATE_LAST_MESSAGE',
              payload: { isStreaming: false },
            });
            dispatch({ type: 'SET_LOADING', payload: false });
          },
        );

        return cancelStream;
      } catch (error) {
        const errorMessage = getErrorMessage(error);
        dispatch({
          type: 'UPDATE_LAST_MESSAGE',
          payload: {
            isStreaming: false,
            error: errorMessage,
            content: errorMessage,
          },
        });
        dispatch({ type: 'SET_ERROR', payload: errorMessage });
        dispatch({ type: 'SET_LOADING', payload: false });
        return undefined;
      }
    },
    [backendUrl, sessionId, state.selectedText],
  );

  // Action creators
  const open = useCallback(() => {
    dispatch({ type: 'OPEN' });
  }, []);

  const close = useCallback(() => {
    dispatch({ type: 'CLOSE' });
  }, []);

  const setSelectedText = useCallback((context: SelectionContext | null) => {
    dispatch({ type: 'SET_SELECTED_TEXT', payload: context });
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: 'SET_ERROR', payload: null });
  }, []);

  const clearSelection = useCallback(() => {
    dispatch({ type: 'CLEAR_SELECTION' });
  }, []);

  return {
    ...state,
    sendMessage,
    open,
    close,
    setSelectedText,
    clearError,
    clearSelection,
    sessionId,
  };
}
