/**
 * AuthGuard Component
 * 
 * Protects routes by requiring authentication.
 * Redirects unauthenticated users to the sign-in page.
 */

import React, { useEffect, ReactNode } from "react";
import { authClient } from "../../lib/auth-client";

interface AuthGuardProps {
  children: ReactNode;
  fallback?: ReactNode;
  redirectTo?: string;
}

/**
 * Wrap protected content with AuthGuard to require authentication.
 * 
 * @example
 * ```tsx
 * <AuthGuard>
 *   <ProtectedContent />
 * </AuthGuard>
 * ```
 */
export function AuthGuard({
  children,
  fallback,
  redirectTo = "/auth/signin",
}: AuthGuardProps) {
  const { data: session, isPending } = authClient.useSession();

  useEffect(() => {
    if (!isPending && !session?.user) {
      if (typeof window !== "undefined") {
        const currentPath = window.location.pathname + window.location.search;
        const redirectUrl = redirectTo + "?redirect=" + encodeURIComponent(currentPath);
        window.location.href = redirectUrl;
      }
    }
  }, [session, isPending, redirectTo]);

  if (isPending) {
    return fallback || <AuthGuardLoadingFallback />;
  }

  if (!session?.user) {
    return fallback || <AuthGuardLoadingFallback />;
  }

  return <>{children}</>;
}

function AuthGuardLoadingFallback() {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "200px",
      color: "var(--ifm-font-color-secondary, #666)",
    }}>
      <div style={{ textAlign: "center" }}>
        <div style={{
          width: "32px",
          height: "32px",
          border: "3px solid var(--ifm-color-emphasis-300)",
          borderTopColor: "var(--ifm-color-primary)",
          borderRadius: "50%",
          animation: "spin 1s linear infinite",
          margin: "0 auto 1rem",
        }} />
        <p>Loading...</p>
        <style>
          {"@keyframes spin { to { transform: rotate(360deg); } }"}
        </style>
      </div>
    </div>
  );
}

export default AuthGuard;
