/**
 * ChatPanel component for ChatKit Frontend.
 * Using inline styles for Tailwind v4 compatibility.
 * @spec 006-chatkit-frontend
 */

import React, { useRef, useEffect, useState } from 'react';
import type { ChatMessage as ChatMessageType } from '../../types/chat';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';

export interface ChatPanelProps {
  messages: ChatMessageType[];
  isLoading: boolean;
  error: string | null;
  mode: 'full' | 'selected_text';
  selectedText: string | null;
  onSendMessage: (message: string) => void;
  onClose: () => void;
  onClearSelection: () => void;
}

export function ChatPanel({ messages, isLoading, error, mode, selectedText, onSendMessage, onClose, onClearSelection }: ChatPanelProps): React.ReactElement {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    const container = messagesContainerRef.current;
    const endElement = messagesEndRef.current;
    if (container && endElement) {
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
      if (isNearBottom || messages.length <= 1) endElement.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const panelStyle: React.CSSProperties = isMobile ? {
    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 9999,
    display: 'flex', flexDirection: 'column', backgroundColor: '#fff', overflow: 'hidden',
  } : {
    position: 'fixed', bottom: '1rem', right: '1rem', zIndex: 9999,
    width: '400px', height: '600px', maxHeight: 'calc(100vh - 2rem)',
    display: 'flex', flexDirection: 'column', backgroundColor: '#fff',
    borderRadius: '12px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)', overflow: 'hidden',
  };

  return (
    <div style={panelStyle} data-chat-panel>
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', backgroundColor: '#2563eb', color: 'white' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ChatIcon />
          <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>Ask the Textbook</h2>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {mode === 'selected_text' && <span style={{ fontSize: '12px', backgroundColor: '#1d4ed8', padding: '4px 8px', borderRadius: '4px' }}>Selection Mode</span>}
          <button onClick={onClose} style={{ padding: '4px', background: 'transparent', border: 'none', color: 'white', cursor: 'pointer' }} aria-label="Close chat"><CloseIcon /></button>
        </div>
      </header>

      {mode === 'selected_text' && selectedText && (
        <div style={{ padding: '8px 16px', backgroundColor: '#eff6ff', borderBottom: '1px solid #dbeafe' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{ margin: '0 0 4px 0', fontSize: '12px', fontWeight: 500, color: '#1d4ed8' }}>Answering about your selection:</p>
              <p style={{ margin: 0, fontSize: '14px', color: '#374151' }}>"{selectedText.slice(0, 100)}{selectedText.length > 100 ? '...' : ''}"</p>
            </div>
            <button onClick={onClearSelection} style={{ flexShrink: 0, fontSize: '12px', color: '#2563eb', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>Clear</button>
          </div>
        </div>
      )}

      {error && (
        <div style={{ padding: '12px 16px', backgroundColor: '#fef2f2', borderBottom: '1px solid #fecaca' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#b91c1c' }}>
            <ErrorIcon />
            <p style={{ margin: 0, fontSize: '14px' }}>{error}</p>
          </div>
        </div>
      )}

      <div ref={messagesContainerRef} style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
        {messages.length === 0 ? <EmptyState mode={mode} /> : (
          <>{messages.map((msg) => <ChatMessage key={msg.id} message={msg} mode={mode} />)}<div ref={messagesEndRef} /></>
        )}
      </div>

      <div style={{ padding: '16px', borderTop: '1px solid #e5e7eb' }}>
        <ChatInput onSend={onSendMessage} isLoading={isLoading} placeholder={mode === 'selected_text' ? 'Ask about your selection...' : 'Ask about the textbook...'} autoFocus />
      </div>
    </div>
  );
}

function EmptyState({ mode }: { mode: 'full' | 'selected_text' }): React.ReactElement {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', textAlign: 'center', padding: '0 32px' }}>
      <div style={{ width: '64px', height: '64px', marginBottom: '16px', borderRadius: '50%', backgroundColor: '#dbeafe', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <ChatIcon size={32} color="#2563eb" />
      </div>
      <h3 style={{ margin: '0 0 8px 0', fontSize: '18px', fontWeight: 500, color: '#111827' }}>
        {mode === 'selected_text' ? 'Ask about your selection' : 'Ask a question'}
      </h3>
      <p style={{ margin: 0, fontSize: '14px', color: '#6b7280' }}>
        {mode === 'selected_text' ? 'Your question will be answered based on the selected text.' : 'Ask anything about the Physical AI & Robotics textbook.'}
      </p>
    </div>
  );
}

function ChatIcon({ size = 20, color = 'currentColor' }: { size?: number; color?: string }): React.ReactElement {
  return <svg style={{ width: size, height: size }} fill="none" stroke={color} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>;
}

function CloseIcon(): React.ReactElement {
  return <svg style={{ width: 20, height: 20 }} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>;
}

function ErrorIcon(): React.ReactElement {
  return <svg style={{ width: 20, height: 20, flexShrink: 0 }} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>;
}

export default ChatPanel;
