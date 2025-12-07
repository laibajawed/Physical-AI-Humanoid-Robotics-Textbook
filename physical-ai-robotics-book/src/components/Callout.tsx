import React from 'react';
import clsx from 'clsx';

interface CalloutProps {
  children: React.ReactNode;
  type?: 'info' | 'warning' | 'tip' | 'example' | 'danger';
  title?: string;
}

export default function Callout({
  children,
  type = 'info',
  title,
}: CalloutProps): React.ReactElement {
  const iconMap = {
    info: 'ℹ️',
    warning: '⚠️',
    tip: '💡',
    example: '📝',
    danger: '🚨',
  };

  const titleMap = {
    info: 'Info',
    warning: 'Warning',
    tip: 'Tip',
    example: 'Example',
    danger: 'Danger',
  };

  const displayTitle = title || titleMap[type];

  return (
    <div className={clsx('callout', `callout-${type}`)}>
      <div className="callout-header">
        <span className="callout-icon">{iconMap[type]}</span>
        <strong>{displayTitle}</strong>
      </div>
      <div className="callout-content">{children}</div>
    </div>
  );
}