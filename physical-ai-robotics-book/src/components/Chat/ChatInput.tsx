/**
 * ChatInput component for ChatKit Frontend.
 * @spec 006-chatkit-frontend
 */

import React, { useState, useRef, useEffect } from 'react';
import { CONFIG } from '../../services/config';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
  autoFocus?: boolean;
}

export function ChatInput({ onSend, isLoading, placeholder = 'Type a message...', autoFocus = false }: ChatInputProps): React.ReactElement {
  const [value, setValue] = useState('');
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (autoFocus && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [autoFocus]);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    
    if (trimmed.length > CONFIG.MAX_QUERY_LENGTH) {
      setError('Question is too long (max ' + CONFIG.MAX_QUERY_LENGTH.toLocaleString() + ' characters)');
      return;
    }
    
    setError(null);
    onSend(trimmed);
    setValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const showCharCount = value.length > CONFIG.MAX_QUERY_LENGTH * 0.8;

  return (
    <div>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => { setValue(e.target.value); setError(null); }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isLoading}
          rows={1}
          style={{
            flex: 1,
            padding: '10px 12px',
            border: '1px solid #d1d5db',
            borderRadius: '8px',
            resize: 'none',
            fontSize: '14px',
            fontFamily: 'inherit',
            outline: 'none',
            minHeight: '40px',
            maxHeight: '120px',
          }}
        />
        <button
          onClick={handleSubmit}
          disabled={!value.trim() || isLoading}
          style={{
            padding: '10px 16px',
            backgroundColor: !value.trim() || isLoading ? '#9ca3af' : '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: !value.trim() || isLoading ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: 500,
          }}
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>
      {showCharCount && (
        <div style={{ marginTop: '4px', fontSize: '12px', color: value.length > CONFIG.MAX_QUERY_LENGTH ? '#b91c1c' : '#6b7280', textAlign: 'right' }}>
          {value.length.toLocaleString()} / {CONFIG.MAX_QUERY_LENGTH.toLocaleString()}
        </div>
      )}
      {error && <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#b91c1c' }}>{error}</p>}
    </div>
  );
}

export default ChatInput;
