/**
 * Better Auth React Client
 * 
 * This module provides the client-side authentication functionality.
 * It connects to the Better Auth server running on Vercel Functions.
 */

import { createAuthClient } from "better-auth/react";
import { jwtClient } from "better-auth/client/plugins";

// Get auth server URL
// Points to the standalone Better Auth service on Railway
const AUTH_SERVICE_URL = "https://better-auth-service-production-e374.up.railway.app";

// Create the auth client with JWT plugin for token access
export const authClient = createAuthClient({
  // Base URL - auth server URL
  baseURL: AUTH_SERVICE_URL,

  // Fetch options for cross-domain cookies
  fetchOptions: {
    credentials: "include", // CRITICAL: Send cookies cross-domain
  },

  // Plugins
  plugins: [
    // JWT client for getting tokens (needed to send to FastAPI backend)
    jwtClient(),
  ],
});

// Export individual methods for convenience
export const {
  signIn,
  signUp,
  signOut,
  useSession,
  getSession,
} = authClient;

// Export types
export type Session = typeof authClient.$Infer.Session;
export type User = typeof authClient.$Infer.Session.user;

/**
 * Get JWT token for authenticated API requests to FastAPI backend
 * 
 * @returns JWT token string or null if not authenticated
 */
export async function getAuthToken(): Promise<string | null> {
  try {
    const result = await authClient.token();
    return result.data?.token || null;
  } catch (error) {
    console.error("Failed to get auth token:", error);
    return null;
  }
}

/**
 * Check if user is currently authenticated
 * 
 * @returns boolean indicating authentication status
 */
export async function isAuthenticated(): Promise<boolean> {
  try {
    const session = await authClient.getSession();
    return !!session.data?.user;
  } catch {
    return false;
  }
}
