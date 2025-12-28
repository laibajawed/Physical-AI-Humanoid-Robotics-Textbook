/**
 * Better Auth Server Configuration
 * 
 * This module configures Better Auth for the Physical AI & Robotics book.
 * It provides email/password authentication with PostgreSQL (Neon) storage.
 */

import { betterAuth } from "better-auth";
import { jwt } from "better-auth/plugins";
import { Pool } from "@neondatabase/serverless";

// Get database URL from environment
const getDatabaseUrl = (): string => {
  const url = process.env.DATABASE_URL;
  if (!url) {
    throw new Error("DATABASE_URL environment variable is required");
  }
  return url;
};

// Get base URL from environment
const getBaseUrl = (): string => {
  return process.env.BETTER_AUTH_URL || "http://localhost:3000";
};

// Get secret from environment
const getSecret = (): string => {
  const secret = process.env.BETTER_AUTH_SECRET;
  if (!secret) {
    throw new Error("BETTER_AUTH_SECRET environment variable is required");
  }
  return secret;
};

export const auth = betterAuth({
  // Database configuration - Neon Serverless (compatible with Vercel)
  database: new Pool({
    connectionString: getDatabaseUrl(),
  }),

  // Secret for signing sessions and JWTs
  secret: getSecret(),

  // Base URL configuration
  baseURL: getBaseUrl(),
  basePath: "/api/auth",

  // Email and password authentication
  emailAndPassword: {
    enabled: true,
    minPasswordLength: 8,
    maxPasswordLength: 128,
    autoSignIn: true, // Auto sign in after signup
  },

  // Session configuration
  session: {
    // Cookie-based session caching for performance
    cookieCache: {
      enabled: true,
      maxAge: 60 * 5, // 5 minutes
    },
    // Session expiration
    expiresIn: 60 * 60 * 24 * 30, // 30 days (default for rememberMe)
    updateAge: 60 * 60 * 24, // Update session every 24 hours
  },

  // Plugins
  plugins: [
    // JWT plugin for JWKS endpoint (required for backend validation)
    jwt(),
  ],

  // Trusted origins for CORS
  trustedOrigins: [
    "http://localhost:3000",
    "http://localhost:5173",
    process.env.BETTER_AUTH_URL || "http://localhost:3000",
  ].filter(Boolean),
});

// Export types for use in components
export type Session = typeof auth.$Infer.Session;
export type User = typeof auth.$Infer.Session.user;
