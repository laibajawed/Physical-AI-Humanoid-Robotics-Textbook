/**
 * useAuth Hook
 * 
 * A convenience wrapper around Better Auth's useSession hook
 * that provides a simpler interface for common auth operations.
 */

import { useCallback } from "react";
import { authClient, getAuthToken } from "../lib/auth-client";

export interface AuthState {
  /** Current user or null if not authenticated */
  user: {
    id: string;
    email: string;
    name: string;
    image?: string | null;
    emailVerified: boolean;
  } | null;
  /** Whether user is authenticated */
  isAuthenticated: boolean;
  /** Whether auth state is being loaded */
  isLoading: boolean;
  /** Error if authentication failed */
  error: Error | null;
}

export interface UseAuthReturn extends AuthState {
  /** Sign in with email and password */
  signIn: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  /** Sign up with email, password, and name */
  signUp: (email: string, password: string, name: string) => Promise<void>;
  /** Sign out the current user */
  signOut: () => Promise<void>;
  /** Refetch the session */
  refetch: () => void;
  /** Get JWT token for API requests */
  getToken: () => Promise<string | null>;
}

/**
 * Hook for managing authentication state and operations
 * 
 * @example
 * ```tsx
 * const { user, isAuthenticated, isLoading, signIn, signOut } = useAuth();
 * 
 * if (isLoading) return <Loading />;
 * if (!isAuthenticated) return <LoginForm onSubmit={signIn} />;
 * return <Dashboard user={user} onSignOut={signOut} />;
 * ```
 */
export function useAuth(): UseAuthReturn {
  const {
    data: session,
    isPending: isLoading,
    error,
    refetch,
  } = authClient.useSession();

  const user = session?.user ? {
    id: session.user.id,
    email: session.user.email,
    name: session.user.name,
    image: session.user.image,
    emailVerified: session.user.emailVerified,
  } : null;

  const isAuthenticated = !!user;

  const signIn = useCallback(async (
    email: string,
    password: string,
    rememberMe = true
  ) => {
    const { error } = await authClient.signIn.email({
      email,
      password,
      rememberMe,
    });
    
    if (error) {
      throw new Error(error.message || "Sign in failed");
    }
  }, []);

  const signUp = useCallback(async (
    email: string,
    password: string,
    name: string
  ) => {
    const { error } = await authClient.signUp.email({
      email,
      password,
      name,
    });
    
    if (error) {
      throw new Error(error.message || "Sign up failed");
    }
  }, []);

  const signOut = useCallback(async () => {
    await authClient.signOut();
  }, []);

  const getToken = useCallback(async () => {
    return getAuthToken();
  }, []);

  return {
    user,
    isAuthenticated,
    isLoading,
    error: error as Error | null,
    signIn,
    signUp,
    signOut,
    refetch,
    getToken,
  };
}

export default useAuth;
