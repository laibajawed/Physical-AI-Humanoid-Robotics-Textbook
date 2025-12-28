/**
 * ChatWidget component for ChatKit Frontend.
 *
 * Main entry point with floating trigger button and ChatPanel.
 *
 * @spec 006-chatkit-frontend
 */

import React from 'react';
import { useChat } from '../../hooks/useChat';
import { ChatPanel } from './ChatPanel';

export function ChatWidget(): React.ReactElement {
  const {
    messages,
    isLoading,
    error,
    isOpen,
    mode,
    selectedText,
    sendMessage,
    open,
    close,
    clearSelection,
  } = useChat();

  return (
    <>
      {/* Floating trigger button - using inline styles for reliability */}
      {!isOpen && (
        <button
          onClick={open}
          data-chat-widget
          style={{
            position: 'fixed',
            bottom: '1rem',
            right: '1rem',
            zIndex: 9999,
            width: '56px',
            height: '56px',
            backgroundColor: '#2563eb',
            color: 'white',
            borderRadius: '50%',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: 'none',
            cursor: 'pointer',
          }}
          aria-label="Open chat assistant"
        >
          <svg
            style={{ width: '24px', height: '24px' }}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        </button>
      )}

      {/* Chat panel */}
      {isOpen && (
        <ChatPanel
          messages={messages}
          isLoading={isLoading}
          error={error}
          mode={mode}
          selectedText={selectedText?.text ?? null}
          onSendMessage={sendMessage}
          onClose={close}
          onClearSelection={clearSelection}
        />
      )}
    </>
  );
}

export default ChatWidget;
