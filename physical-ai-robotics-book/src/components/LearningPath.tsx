import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';

interface LearningPathItem {
  title: string;
  description: string;
  url: string;
  status: 'completed' | 'in-progress' | 'not-started';
}

interface LearningPathProps {
  title: string;
  items: LearningPathItem[];
  className?: string;
}

export default function LearningPath({
  title,
  items,
  className,
}: LearningPathProps): React.ReactElement {
  return (
    <div className={clsx('learning-path', className)}>
      <h2 className="learning-path-title">{title}</h2>
      <ol className="learning-path-list">
        {items.map((item, index) => (
          <li
            key={index}
            className={clsx(
              'learning-path-item',
              `learning-path-item--${item.status}`
            )}
          >
            <Link to={item.url} className="learning-path-link">
              <div className="learning-path-item-content">
                <div className="learning-path-item-header">
                  <span className="learning-path-item-number">{index + 1}.</span>
                  <h3 className="learning-path-item-title">{item.title}</h3>
                </div>
                <p className="learning-path-item-description">{item.description}</p>
              </div>
              <div className="learning-path-item-status">
                {item.status === 'completed' ? '✓' :
                 item.status === 'in-progress' ? '→' : '○'}
              </div>
            </Link>
          </li>
        ))}
      </ol>
    </div>
  );
}