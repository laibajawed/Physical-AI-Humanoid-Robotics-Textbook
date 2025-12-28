/**
 * Session management hook for ChatKit Frontend.
 *
 * Manages session ID in localStorage with fallback for private browsing.
 * Session IDs are client-generated UUID v4 per spec IC-004.
 *
 * @spec 006-chatkit-frontend
 */

import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { CONFIG } from '../services/config';
import type { SessionState } from '../types/chat';

// =============================================================================
// UUID Validation
// =============================================================================

/**
 * UUID v4 validation regex.
 * Per spec: TASK-6.8 acceptance criteria.
 */
const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/**
 * Validate that a string is a valid UUID v4.
 *
 * @param id - String to validate
 * @returns True if valid UUID v4
 */
function isValidUUID(id: string): boolean {
  return UUID_V4_REGEX.test(id);
}

// =============================================================================
// useSession Hook (TASK-6.8)
// =============================================================================

/**
 * Hook for managing chat session ID.
 *
 * On mount:
 * 1. Checks localStorage for existing session ID
 * 2. If valid UUID v4 found, uses it (isNewSession: false)
 * 3. If not found or invalid, generates new UUID v4 (isNewSession: true)
 * 4. Falls back to in-memory UUID if localStorage unavailable
 *
 * @returns SessionState with sessionId, isNewSession, storageAvailable
 *
 * @example
 * ```typescript
 * function ChatWidget() {
 *   const { sessionId, isNewSession, storageAvailable } = useSession();
 *
 *   useEffect(() => {
 *     if (!isNewSession) {
 *       // Load history for existing session
 *       loadHistory(sessionId);
 *     }
 *   }, [sessionId, isNewSession]);
 * }
 * ```
 */
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
      // Attempt to read from localStorage
      const stored = localStorage.getItem(CONFIG.SESSION_STORAGE_KEY);

      if (stored && isValidUUID(stored)) {
        // Valid session found - use it
        sessionId = stored;
        isNewSession = false;
      } else {
        // No valid session - generate new one
        sessionId = uuidv4();
        isNewSession = true;

        // Try to save to localStorage
        try {
          localStorage.setItem(CONFIG.SESSION_STORAGE_KEY, sessionId);
        } catch {
          // localStorage write failed (quota exceeded, etc.)
          storageAvailable = false;
        }

        // If there was an invalid value, clear it
        if (stored) {
          try {
            localStorage.removeItem(CONFIG.SESSION_STORAGE_KEY);
            localStorage.setItem(CONFIG.SESSION_STORAGE_KEY, sessionId);
          } catch {
            // Ignore cleanup errors
          }
        }
      }
    } catch {
      // localStorage unavailable (private browsing, etc.)
      storageAvailable = false;
      sessionId = uuidv4();
      isNewSession = true;
    }

    setState({
      sessionId,
      isNewSession,
      storageAvailable,
    });
  }, []);

  return state;
}

// =============================================================================
// Additional Exports
// =============================================================================

/**
 * Clear session ID from localStorage.
 *
 * Useful for "Start New Conversation" functionality.
 */
export function clearSession(): void {
  try {
    localStorage.removeItem(CONFIG.SESSION_STORAGE_KEY);
  } catch {
    // Ignore errors if localStorage unavailable
  }
}

/**
 * Get session ID synchronously (for non-React contexts).
 *
 * Note: Prefer useSession() hook in React components.
 *
 * @returns Session ID or newly generated UUID
 */
export function getSessionIdSync(): string {
  try {
    const stored = localStorage.getItem(CONFIG.SESSION_STORAGE_KEY);
    if (stored && isValidUUID(stored)) {
      return stored;
    }
  } catch {
    // Ignore errors
  }
  return uuidv4();
}
