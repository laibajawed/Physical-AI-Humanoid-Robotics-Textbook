/**
 * Error handling utilities for ChatKit Frontend.
 *
 * Provides custom error classes and error-to-UI message mapping
 * per spec Error-to-UI Mapping table.
 *
 * @spec 006-chatkit-frontend
 */

// =============================================================================
// Error Codes
// =============================================================================

/**
 * Error codes matching backend ErrorCodes.
 * Maps to: backend/models/response.py:ErrorCodes
 */
export const ErrorCodes = {
  // Request validation errors
  EMPTY_QUERY: 'EMPTY_QUERY',
  QUERY_TOO_LONG: 'QUERY_TOO_LONG',
  SELECTION_TOO_LONG: 'SELECTION_TOO_LONG',
  VALIDATION_ERROR: 'VALIDATION_ERROR',

  // Session errors
  INVALID_SESSION_ID: 'INVALID_SESSION_ID',
  SESSION_NOT_FOUND: 'SESSION_NOT_FOUND',

  // Service errors
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
  RATE_LIMITED: 'RATE_LIMITED',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  QDRANT_UNAVAILABLE: 'QDRANT_UNAVAILABLE',
  GEMINI_UNAVAILABLE: 'GEMINI_UNAVAILABLE',

  // Frontend-only errors
  CORS_ERROR: 'CORS_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT: 'TIMEOUT',
  HISTORY_ERROR: 'HISTORY_ERROR',
} as const;

export type ErrorCode = (typeof ErrorCodes)[keyof typeof ErrorCodes];

// =============================================================================
// User-Friendly Error Messages
// =============================================================================

/**
 * Mapping from error codes to user-friendly messages.
 * Per spec: Error-to-UI Mapping table in data-model.md
 */
export const ERROR_MESSAGES: Record<string, string> = {
  // Request validation
  [ErrorCodes.EMPTY_QUERY]: 'Please enter a question.',
  [ErrorCodes.QUERY_TOO_LONG]: 'Your question is too long. Please shorten it.',
  [ErrorCodes.SELECTION_TOO_LONG]: 'The selected text is too long. Please select a smaller portion.',
  [ErrorCodes.VALIDATION_ERROR]: 'Please enter a valid question.',

  // Session errors
  [ErrorCodes.INVALID_SESSION_ID]: 'Session expired. Starting a new conversation.',
  [ErrorCodes.SESSION_NOT_FOUND]: 'Session not found. Starting a new conversation.',

  // Service errors
  [ErrorCodes.SERVICE_UNAVAILABLE]: 'The assistant is temporarily unavailable. Please try again.',
  [ErrorCodes.RATE_LIMITED]: 'Too many requests. Please wait a moment and try again.',
  [ErrorCodes.INTERNAL_ERROR]: 'Something went wrong. Please try again later.',
  [ErrorCodes.QDRANT_UNAVAILABLE]: 'Search service is temporarily unavailable. Please try again.',
  [ErrorCodes.GEMINI_UNAVAILABLE]: 'AI service is temporarily unavailable. Please try again.',

  // Frontend errors
  [ErrorCodes.CORS_ERROR]: 'Unable to connect to the assistant. Please check your connection.',
  [ErrorCodes.NETWORK_ERROR]: 'Network error. Please check your internet connection.',
  [ErrorCodes.TIMEOUT]: 'Request timed out. Please try again.',
  [ErrorCodes.HISTORY_ERROR]: 'Failed to load conversation history.',
};

// =============================================================================
// ChatApiError Class
// =============================================================================

/**
 * Custom error class for API errors.
 *
 * Contains structured error information from backend responses
 * and provides user-friendly message generation.
 */
export class ChatApiError extends Error {
  /** Machine-readable error code */
  public readonly errorCode: string;
  /** HTTP status code (0 for network errors) */
  public readonly status: number;
  /** Original error message from backend */
  public readonly originalMessage: string;
  /** Additional error details */
  public readonly details?: Record<string, unknown>;

  constructor(
    errorCode: string,
    message: string,
    status: number = 0,
    details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'ChatApiError';
    this.errorCode = errorCode;
    this.status = status;
    this.originalMessage = message;
    this.details = details;

    // Maintains proper stack trace for where error was thrown
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ChatApiError);
    }
  }

  /**
   * Get user-friendly error message.
   */
  getUserMessage(): string {
    return ERROR_MESSAGES[this.errorCode] || ERROR_MESSAGES[ErrorCodes.INTERNAL_ERROR];
  }
}

// =============================================================================
// Error Utility Functions
// =============================================================================

/**
 * Get user-friendly error message from any error type.
 *
 * @param error - Error object (ChatApiError, Error, or unknown)
 * @returns User-friendly message string
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof ChatApiError) {
    return error.getUserMessage();
  }

  if (error instanceof TypeError && error.message.includes('fetch')) {
    return ERROR_MESSAGES[ErrorCodes.NETWORK_ERROR];
  }

  if (error instanceof Error) {
    // Check for CORS errors
    if (error.message.includes('CORS') || error.message.includes('cross-origin')) {
      return ERROR_MESSAGES[ErrorCodes.CORS_ERROR];
    }

    // Check for network errors
    if (
      error.message.includes('network') ||
      error.message.includes('Network') ||
      error.message.includes('fetch')
    ) {
      return ERROR_MESSAGES[ErrorCodes.NETWORK_ERROR];
    }

    // Check for timeout
    if (error.name === 'AbortError' || error.message.includes('timeout')) {
      return ERROR_MESSAGES[ErrorCodes.TIMEOUT];
    }
  }

  // Generic fallback
  return ERROR_MESSAGES[ErrorCodes.INTERNAL_ERROR];
}

/**
 * Check if an error is retryable.
 *
 * Returns true for transient errors that may succeed on retry:
 * - 503 Service Unavailable
 * - Network errors
 * - Timeouts
 *
 * Returns false for client errors that won't improve:
 * - 400 Bad Request
 * - 429 Rate Limited (should wait, not immediate retry)
 *
 * @param error - Error object to check
 * @returns True if the error is retryable
 */
export function isRetryableError(error: unknown): boolean {
  if (error instanceof ChatApiError) {
    // Server errors are retryable
    if (error.status >= 500) {
      return true;
    }

    // Specific retryable error codes
    const retryableCodes = [
      ErrorCodes.SERVICE_UNAVAILABLE,
      ErrorCodes.QDRANT_UNAVAILABLE,
      ErrorCodes.GEMINI_UNAVAILABLE,
      ErrorCodes.NETWORK_ERROR,
      ErrorCodes.TIMEOUT,
    ];

    return retryableCodes.includes(error.errorCode as typeof retryableCodes[number]);
  }

  // Network errors are retryable
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return true;
  }

  // Abort errors (timeout) are retryable
  if (error instanceof Error && error.name === 'AbortError') {
    return true;
  }

  return false;
}

/**
 * Determine the error code from an HTTP status code.
 *
 * @param status - HTTP status code
 * @returns Corresponding error code
 */
export function statusToErrorCode(status: number): string {
  switch (status) {
    case 400:
      return ErrorCodes.VALIDATION_ERROR;
    case 404:
      return ErrorCodes.SESSION_NOT_FOUND;
    case 429:
      return ErrorCodes.RATE_LIMITED;
    case 503:
      return ErrorCodes.SERVICE_UNAVAILABLE;
    default:
      if (status >= 500) {
        return ErrorCodes.INTERNAL_ERROR;
      }
      return ErrorCodes.INTERNAL_ERROR;
  }
}

/**
 * Create a ChatApiError from a network/fetch error.
 *
 * @param error - Original error
 * @returns ChatApiError with appropriate code
 */
export function createNetworkError(error: unknown): ChatApiError {
  if (error instanceof Error) {
    if (error.name === 'AbortError') {
      return new ChatApiError(ErrorCodes.TIMEOUT, 'Request timed out', 0);
    }

    if (error.message.includes('CORS') || error.message.includes('cross-origin')) {
      return new ChatApiError(ErrorCodes.CORS_ERROR, 'CORS error', 0);
    }
  }

  return new ChatApiError(
    ErrorCodes.NETWORK_ERROR,
    error instanceof Error ? error.message : 'Network error',
    0,
  );
}
