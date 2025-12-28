/**
 * SourceCitations component for ChatKit Frontend.
 * @spec 006-chatkit-frontend
 */

import React from 'react';
import type { SourceCitation } from '../../types/chat';

interface SourceCitationsProps {
  sources: SourceCitation[];
  mode: 'full' | 'selected_text';
}

export function SourceCitations({ sources, mode }: SourceCitationsProps): React.ReactElement {
  if (mode === 'selected_text') {
    return (
      <div style={{ fontSize: '12px', color: '#6b7280', fontStyle: 'italic' }}>
        Based on your selection
      </div>
    );
  }

  if (sources.length === 0) {
    return (
      <div style={{ fontSize: '12px', color: '#6b7280', fontStyle: 'italic' }}>
        No specific sources cited
      </div>
    );
  }

  return (
    <div style={{ fontSize: '12px' }}>
      <p style={{ margin: '0 0 4px 0', fontWeight: 500, color: '#374151' }}>Sources:</p>
      <ul style={{ margin: 0, padding: '0 0 0 16px', listStyleType: 'disc' }}>
        {sources.map((source, idx) => (
          <li key={idx} style={{ marginBottom: '2px' }}>
            <a
              href={source.source_url}
              style={{ color: '#2563eb', textDecoration: 'none' }}
              title={source.snippet}
            >
              {source.title}
              {source.section && <span style={{ color: '#6b7280' }}> - {source.section}</span>}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default SourceCitations;
