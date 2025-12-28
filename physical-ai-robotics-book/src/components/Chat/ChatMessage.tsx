/**
 * ChatMessage component for ChatKit Frontend.
 * @spec 006-chatkit-frontend
 */

import React from 'react';
import type { ChatMessage as ChatMessageType } from '../../types/chat';
import { SourceCitations } from './SourceCitations';

interface ChatMessageProps {
  message: ChatMessageType;
  mode: 'full' | 'selected_text';
}

export function ChatMessage({ message, mode }: ChatMessageProps): React.ReactElement {
  const isUser = message.role === 'user';
  
  const containerStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: isUser ? 'flex-end' : 'flex-start',
    marginBottom: '12px',
  };

  const bubbleStyle: React.CSSProperties = {
    maxWidth: '85%',
    padding: '12px 16px',
    borderRadius: '12px',
    backgroundColor: isUser ? '#2563eb' : '#f3f4f6',
    color: isUser ? 'white' : '#111827',
  };

  const timestampStyle: React.CSSProperties = {
    fontSize: '11px',
    color: '#9ca3af',
    marginTop: '4px',
  };

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div style={containerStyle}>
      <div style={bubbleStyle}>
        {message.isStreaming && !message.content ? (
          <span>Thinking...</span>
        ) : (
          <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{message.content}</div>
        )}
        {message.error && (
          <p style={{ margin: '8px 0 0 0', fontSize: '12px', color: isUser ? '#fecaca' : '#b91c1c' }}>{message.error}</p>
        )}
      </div>
      {!isUser && message.sources && message.sources.length > 0 && (
        <div style={{ maxWidth: '85%', marginTop: '8px' }}>
          <SourceCitations sources={message.sources} mode={mode} />
        </div>
      )}
      <span style={timestampStyle}>{formatTime(message.timestamp)}</span>
    </div>
  );
}

export default ChatMessage;
