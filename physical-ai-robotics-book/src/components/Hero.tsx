import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';

interface HeroProps {
  title: string;
  subtitle?: string;
  description: string;
  ctaText?: string;
  ctaLink?: string;
  className?: string;
}

export default function Hero({
  title,
  subtitle,
  description,
  ctaText = 'Get Started',
  ctaLink = '/docs/introduction',
  className,
}: HeroProps): React.ReactElement {
  return (
    <section className={clsx('hero', className)}>
      <div className="container">
        {subtitle && <span className="hero-subtitle">{subtitle}</span>}
        <h1 className="hero-title">{title}</h1>
        <p className="hero-description">{description}</p>
        {ctaLink && (
          <Link className="button button--primary button--lg hero-cta" to={ctaLink}>
            {ctaText}
          </Link>
        )}
      </div>
    </section>
  );
}