import React from 'react';
import clsx from 'clsx';

interface FigureProps {
  src: string;
  alt: string;
  caption?: string;
  className?: string;
}

export default function Figure({
  src,
  alt,
  caption,
  className,
}: FigureProps): React.ReactElement {
  return (
    <figure className={clsx('figure', className)}>
      <img src={src} alt={alt} />
      {caption && <figcaption className="figure-caption">{caption}</figcaption>}
    </figure>
  );
}