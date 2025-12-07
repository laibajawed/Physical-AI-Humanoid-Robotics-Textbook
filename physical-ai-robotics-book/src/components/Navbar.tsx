import React from 'react';
import Navbar from '@theme-original/Navbar';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {useLocation} from '@docusaurus/router';

export default function NavbarWrapper(props: React.PropsWithChildren<{}>) {
  const location = useLocation();
  const isDocsPage = location.pathname.includes('/docs');

  return (
    <>
      <Navbar {...props} />
      {/* Add any custom navbar elements here if needed */}
      {isDocsPage && (
        <div className="custom-navbar-extensions">
          {/* Personalization and translation buttons will go here later */}
        </div>
      )}
    </>
  );
}