/**
 * SelectionPopup component for ChatKit Frontend.
 *
 * Appears when text is selected on book pages to allow
 * "Ask about selection" functionality.
 *
 * @spec 006-chatkit-frontend
 */

import React, { useEffect, useState } from 'react';
import { useTextSelection } from '../../hooks/useTextSelection';
import { CONFIG } from '../../services/config';
import type { SelectionContext } from '../../types/chat';

// =============================================================================
// Props Interface
// =============================================================================

export interface SelectionPopupProps {
  /** Called when user clicks "Ask about selection" */
  onAskAboutSelection: (context: SelectionContext) => void;
}

// =============================================================================
// SelectionPopup Component (TASK-6.18)
// =============================================================================

/**
 * Popup that appears when text is selected on book pages.
 *
 * Features:
 * - Uses useTextSelection() hook for selection tracking
 * - Shows "Ask about selection" button near selection
 * - Positioned using selection bounding rect
 * - Shows tooltip for selections < 20 chars
 * - Hidden when no text selected
 *
 * @param props - SelectionPopupProps
 *
 * @example
 * ```typescript
 * <SelectionPopup
 *   onAskAboutSelection={(context) => {
 *     setSelectedText(context);
 *     openChat();
 *   }}
 * />
 * ```
 */
export function SelectionPopup({ onAskAboutSelection }: SelectionPopupProps): React.ReactElement | null {
  const { selection, selectionRect, clearSelection } = useTextSelection();
  const [position, setPosition] = useState({ top: 0, left: 0 });

  // Calculate popup position
  useEffect(() => {
    if (!selectionRect) return;

    // Position above the selection, centered horizontally
    const top = selectionRect.top + window.scrollY - 50;
    const left = selectionRect.left + selectionRect.width / 2;

    setPosition({ top, left });
  }, [selectionRect]);

  // Don't render if no selection
  if (!selection || !selectionRect) {
    return null;
  }

  // Check if selection is too short
  const isTooShort = selection.text.length < CONFIG.MIN_SELECTION_LENGTH;

  // Handle click
  const handleClick = () => {
    if (isTooShort) return;

    onAskAboutSelection(selection);
    clearSelection();
  };

  return (
    <div
      data-chat-widget
      className="fixed z-50 transform -translate-x-1/2"
      style={{
        top: `${Math.max(10, position.top)}px`,
        left: `${position.left}px`,
      }}
    >
      <div className="relative">
        {/* Main button */}
        <button
          onClick={handleClick}
          disabled={isTooShort}
          className={`
            flex items-center gap-2
            px-3 py-2
            rounded-lg
            shadow-lg
            text-sm font-medium
            transition-all duration-200
            ${isTooShort
              ? 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white hover:shadow-xl'
            }
          `}
          aria-label={isTooShort ? 'Select more text to ask' : 'Ask about selected text'}
        >
          <AskIcon />
          <span>Ask about selection</span>
        </button>

        {/* Tooltip for short selections */}
        {isTooShort && (
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2">
            <div className="bg-gray-900 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
              Please select more text
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-b-gray-900" />
            </div>
          </div>
        )}

        {/* Arrow pointing down to selection */}
        <div className="absolute top-full left-1/2 transform -translate-x-1/2">
          <div
            className={`
              w-0 h-0
              border-l-[6px] border-l-transparent
              border-r-[6px] border-r-transparent
              border-t-[6px]
              ${isTooShort ? 'border-t-gray-100 dark:border-t-gray-800' : 'border-t-blue-600'}
            `}
          />
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Icon Component
// =============================================================================

function AskIcon(): React.ReactElement {
  return (
    <svg
      className="w-4 h-4"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

export default SelectionPopup;
