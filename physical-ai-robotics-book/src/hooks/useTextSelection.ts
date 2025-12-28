/**
 * Text selection hook for ChatKit Frontend.
 *
 * Captures text selections from book pages using the browser Selection API.
 * Used for "Ask about selection" feature.
 *
 * @spec 006-chatkit-frontend
 */

import { useState, useEffect, useCallback } from 'react';
import type { SelectionContext } from '../types/chat';

// =============================================================================
// Selection State Interface
// =============================================================================

export interface TextSelectionState {
  /** Current selection context or null if no selection */
  selection: SelectionContext | null;
  /** Selection bounding rectangle for popup positioning */
  selectionRect: DOMRect | null;
  /** Clear the current selection */
  clearSelection: () => void;
}

// =============================================================================
// useTextSelection Hook (TASK-6.9)
// =============================================================================

/**
 * Hook for capturing text selections on the page.
 *
 * Listens for mouseup events and uses window.getSelection()
 * to capture selected text. Returns SelectionContext with
 * text, sourceUrl (current page), and capturedAt timestamp.
 *
 * Features:
 * - Ignores selections < 1 character
 * - Provides selection bounding rect for popup positioning
 * - Cleans up event listeners on unmount
 *
 * @returns TextSelectionState with selection, selectionRect, clearSelection
 *
 * @example
 * ```typescript
 * function SelectionPopup() {
 *   const { selection, selectionRect, clearSelection } = useTextSelection();
 *
 *   if (!selection || !selectionRect) {
 *     return null;
 *   }
 *
 *   return (
 *     <div style={{ top: selectionRect.bottom, left: selectionRect.left }}>
 *       <button onClick={() => onAskAboutSelection(selection.text)}>
 *         Ask about selection
 *       </button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useTextSelection(): TextSelectionState {
  const [selection, setSelection] = useState<SelectionContext | null>(null);
  const [selectionRect, setSelectionRect] = useState<DOMRect | null>(null);

  // Handle selection changes
  const handleSelectionChange = useCallback(() => {
    const windowSelection = window.getSelection();

    if (!windowSelection || windowSelection.isCollapsed) {
      // No selection or empty selection
      setSelection(null);
      setSelectionRect(null);
      return;
    }

    const selectedText = windowSelection.toString().trim();

    // Ignore very short selections (likely accidental)
    if (selectedText.length < 1) {
      setSelection(null);
      setSelectionRect(null);
      return;
    }

    // Get bounding rectangle for positioning
    const range = windowSelection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    // Only set if we have a valid rect
    if (rect.width > 0 && rect.height > 0) {
      setSelection({
        text: selectedText,
        sourceUrl: window.location.href,
        capturedAt: new Date(),
      });
      setSelectionRect(rect);
    }
  }, []);

  // Clear selection function
  const clearSelection = useCallback(() => {
    // Clear browser selection
    const windowSelection = window.getSelection();
    if (windowSelection) {
      windowSelection.removeAllRanges();
    }

    setSelection(null);
    setSelectionRect(null);
  }, []);

  // Set up event listeners
  useEffect(() => {
    // Use mouseup to detect selection completion
    const handleMouseUp = () => {
      // Small delay to ensure selection is finalized
      setTimeout(handleSelectionChange, 10);
    };

    // Handle keyboard selection (Shift+Arrow keys)
    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.shiftKey) {
        setTimeout(handleSelectionChange, 10);
      }
    };

    // Clear selection when clicking elsewhere
    const handleMouseDown = (event: MouseEvent) => {
      // Don't clear if clicking on a chat element
      const target = event.target as HTMLElement;
      if (target.closest('[data-chat-widget]')) {
        return;
      }

      // Check if click is outside current selection
      const windowSelection = window.getSelection();
      if (windowSelection && !windowSelection.isCollapsed) {
        const range = windowSelection.getRangeAt(0);
        const rect = range.getBoundingClientRect();

        const clickX = event.clientX;
        const clickY = event.clientY;

        const isInsideSelection =
          clickX >= rect.left &&
          clickX <= rect.right &&
          clickY >= rect.top &&
          clickY <= rect.bottom;

        if (!isInsideSelection) {
          // Click outside selection - will be cleared by browser
          setSelection(null);
          setSelectionRect(null);
        }
      }
    };

    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('keyup', handleKeyUp);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('keyup', handleKeyUp);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, [handleSelectionChange]);

  return {
    selection,
    selectionRect,
    clearSelection,
  };
}

// =============================================================================
// Additional Exports
// =============================================================================

export type { SelectionContext };
