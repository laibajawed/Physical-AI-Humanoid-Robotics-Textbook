import React from 'react';
import Link from '@docusaurus/Link';
import clsx from 'clsx';

interface DownloadCardProps {
  title: string;
  description: string;
  href: string;
  icon?: string;
  className?: string;
}

export default function DownloadCard({
  title,
  description,
  href,
  icon = '📥',
  className,
}: DownloadCardProps): React.ReactElement {
  return (
    <div className={clsx('download-card', className)}>
      <div className="download-card-content">
        <div className="download-card-icon">{icon}</div>
        <div className="download-card-text">
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
      </div>
      <Link className="download-card-link" to={href}>
        Download
      </Link>
    </div>
  );
}