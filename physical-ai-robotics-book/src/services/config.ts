/**
 * Configuration service for ChatKit Frontend.
 *
 * Provides static configuration constants and the useBackendUrl() hook
 * for accessing backend URL from Docusaurus context.
 *
 * @spec 006-chatkit-frontend
 */

import useDocusaurusContext from '@docusaurus/useDocusaurusContext';

// =============================================================================
// Static Configuration Constants
// =============================================================================

/**
 * Static configuration values for the chat frontend.
 * Use siteConfig.customFields.backendUrl in components for API URL.
 */
export const CONFIG = {
  // Timeouts
  /** Request timeout in milliseconds */
  REQUEST_TIMEOUT_MS: 30000,
  /** Stream timeout in milliseconds */
  STREAM_TIMEOUT_MS: 60000,

  // Retry Configuration
  /** Maximum number of retry attempts */
  MAX_RETRIES: 3,
  /** Initial delay between retries in milliseconds */
  RETRY_DELAY_MS: 1000,
  /** Multiplier for exponential backoff */
  RETRY_BACKOFF_MULTIPLIER: 2,

  // Validation Limits
  /** Maximum query length in characters */
  MAX_QUERY_LENGTH: 32000,
  /** Maximum selection length in characters */
  MAX_SELECTION_LENGTH: 64000,
  /** Minimum selection length for "Ask about selection" */
  MIN_SELECTION_LENGTH: 20,

  // Session Configuration
  /** localStorage key for session ID */
  SESSION_STORAGE_KEY: 'chatui_session_id',
  /** Maximum history entries to load */
  HISTORY_LIMIT: 50,

  // UI Configuration
  /** Maximum messages to display in chat */
  MAX_MESSAGES_DISPLAYED: 100,
  /** Scroll threshold for auto-scroll in pixels */
  AUTO_SCROLL_THRESHOLD: 100,
} as const;

// =============================================================================
// Default Backend URL (for non-React contexts)
// =============================================================================

/**
 * Default backend URL for non-React contexts (e.g., tests).
 * In React components, use useBackendUrl() hook instead.
 */
export const DEFAULT_BACKEND_URL = 'http://localhost:8000';

// =============================================================================
// useBackendUrl Hook
// =============================================================================

/**
 * Hook to get backend URL from Docusaurus configuration.
 *
 * Retrieves the backend URL from siteConfig.customFields.backendUrl,
 * configured in docusaurus.config.ts. Falls back to DEFAULT_BACKEND_URL
 * if not configured.
 *
 * @returns The backend API base URL
 *
 * @example
 * ```typescript
 * function ChatPanel() {
 *   const backendUrl = useBackendUrl();
 *   // backendUrl is now 'http://localhost:8000' or production URL
 * }
 * ```
 */
export function useBackendUrl(): string {
  const { siteConfig } = useDocusaurusContext();

  // customFields is typed as Record<string, unknown> in Docusaurus
  const backendUrl = siteConfig.customFields?.backendUrl;

  if (typeof backendUrl === 'string' && backendUrl.length > 0) {
    return backendUrl;
  }

  return DEFAULT_BACKEND_URL;
}

// =============================================================================
// Type Exports
// =============================================================================

/** Configuration object type */
export type ConfigType = typeof CONFIG;
