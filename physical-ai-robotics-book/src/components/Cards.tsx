import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';

interface CardProps {
  title: string;
  description: string;
  icon?: string;
  link?: string;
  className?: string;
}

export default function Card({
  title,
  description,
  icon = '📚',
  link,
  className,
}: CardProps): React.ReactElement {
  const cardContent = (
    <div className={clsx('card', className)}>
      <div className="card-content">
        <div className="card-icon">{icon}</div>
        <h3 className="card-title">{title}</h3>
        <p className="card-description">{description}</p>
      </div>
    </div>
  );

  if (link) {
    return (
      <Link to={link} className="card-link">
        {cardContent}
      </Link>
    );
  }

  return cardContent;
}