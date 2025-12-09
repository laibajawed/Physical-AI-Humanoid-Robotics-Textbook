// src/theme/Navbar/Logo/index.js
import React from 'react';
import Link from '@docusaurus/Link';
import ThemedImage from '@theme/ThemedImage';
import { useBaseUrlUtils } from '@docusaurus/useBaseUrl';

export default function Logo() {
  const { withBaseUrl } = useBaseUrlUtils();

  const siteTitle = 'Physical AI & Humanoid Robotics';

  const logo = {
    alt: 'Physical AI & Humanoid Robotics Logo',
    src: '/images.png',
    srcDark: '/images.png', // optional
    width: 38,
    height: 38,
  };

  const sources = {
    light: withBaseUrl(logo.src),
    dark: withBaseUrl(logo.srcDark || logo.src),
  };

  return (
    <Link to="/" className="navbar__brand" title={siteTitle}>
      {/* Logo image */}
      <ThemedImage
        sources={sources}
        alt={logo.alt}
        width={logo.width}
        height={logo.height}
        className="navbar__logo"
        style={{ borderRadius: '6px' }}
      />

      {/* Text – now inside the same <Link> so it’s clickable */}
      <strong
        className="navbar__title text--truncate"
        style={{
          marginLeft: '12px',
          color: 'var(--ifm-navbar-link-color)',
          fontWeight: 600,
          fontSize: '1.1rem',
        }}
      >
        {siteTitle}
      </strong>
    </Link>
  );
}