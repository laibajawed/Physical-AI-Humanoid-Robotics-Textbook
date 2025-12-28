/**
 * Layout wrapper for ChatKit Frontend integration and Authentication.
 *
 * Adds ChatWidget and SelectionPopup globally to all pages.
 * Wraps /docs/* routes with AuthGuard to require authentication.
 *
 * @spec 006-chatkit-frontend
 * @spec 007-authentication-integration
 */

import React, { useCallback } from 'react';
import OriginalLayout from '@theme-original/Layout';
import BrowserOnly from '@docusaurus/BrowserOnly';
import { useLocation } from '@docusaurus/router';
import { ChatWidget } from '../../components/Chat';
import { SelectionPopup } from '../../components/TextSelection';
import { AuthGuard } from '../../components/Auth';
import { useChat } from '../../hooks/useChat';
import type { SelectionContext } from '../../types/chat';

/**
 * Inner component that uses the chat hook.
 * Separated to ensure hooks are called inside a component.
 */
function ChatIntegration(): React.ReactElement {
  const { setSelectedText, open } = useChat();

  // Handle "Ask about selection" click
  const handleAskAboutSelection = useCallback(
    (context: SelectionContext) => {
      setSelectedText(context);
      open();
    },
    [setSelectedText, open],
  );

  return (
    <>
      <SelectionPopup onAskAboutSelection={handleAskAboutSelection} />
      <ChatWidget />
    </>
  );
}

/**
 * Check if a path requires authentication.
 *
 * Per spec: /docs/* routes require authentication.
 * Homepage (/) and /auth/* routes are public.
 */
function isProtectedRoute(pathname: string): boolean {
  return pathname.startsWith('/docs');
}

/**
 * Layout wrapper that includes ChatWidget, SelectionPopup, and AuthGuard.
 *
 * Per spec 006: Chat available on all pages without per-page setup.
 * Per spec 007: /docs/* routes are protected and require authentication.
 *
 * State persists during navigation.
 *
 * BrowserOnly wrapper ensures chat and auth components only render on client-side
 * to avoid SSR issues with localStorage, window.getSelection, etc.
 */
export default function Layout(props: React.PropsWithChildren<{}>): React.ReactElement {
  const location = useLocation();
  const isProtected = isProtectedRoute(location.pathname);

  return (
    <>
      {isProtected ? (
        <BrowserOnly fallback={<OriginalLayout {...props} />}>
          {() => (
            <AuthGuard>
              <OriginalLayout {...props} />
            </AuthGuard>
          )}
        </BrowserOnly>
      ) : (
        <OriginalLayout {...props} />
      )}
      <BrowserOnly fallback={null}>
        {() => <ChatIntegration />}
      </BrowserOnly>
    </>
  );
}
