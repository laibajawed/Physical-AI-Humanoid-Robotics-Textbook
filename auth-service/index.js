/**
 * Better Auth Standalone Server for Railway
 *
 * This Express server handles all authentication operations:
 * - Email/password signup and signin
 * - Session management
 * - JWKS endpoint for backend JWT validation
 */

import express from 'express';
import cors from 'cors';
import { betterAuth } from 'better-auth';
import { jwt } from 'better-auth/plugins';
import { Pool } from '@neondatabase/serverless';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// CORS configuration
const allowedOrigins = process.env.CORS_ORIGINS
  ? process.env.CORS_ORIGINS.split(',').map(o => o.trim())
  : ['http://localhost:3000'];

app.use(cors({
  origin: allowedOrigins,
  credentials: true,
}));

app.use(express.json());

// Initialize Better Auth
const auth = betterAuth({
  // Database configuration - Neon Serverless
  database: new Pool({
    connectionString: process.env.DATABASE_URL,
  }),

  // Secret for signing sessions and JWTs
  secret: process.env.BETTER_AUTH_SECRET,

  // Base URL configuration
  baseURL: process.env.BETTER_AUTH_URL || `http://localhost:${PORT}`,
  basePath: '/api/auth',

  // Email and password authentication
  emailAndPassword: {
    enabled: true,
    minPasswordLength: 8,
    maxPasswordLength: 128,
    autoSignIn: true,
  },

  // Session configuration
  session: {
    cookieCache: {
      enabled: true,
      maxAge: 60 * 5, // 5 minutes
    },
    expiresIn: 60 * 60 * 24 * 30, // 30 days
    updateAge: 60 * 60 * 24, // Update every 24 hours
  },

  // Advanced configuration for cross-domain cookies
  advanced: {
    // Use secure cookies in production (required for sameSite=none)
    useSecureCookies: true,
    // Cookie attributes for cross-domain authentication
    defaultCookieAttributes: {
      sameSite: 'none', // Required for cross-domain cookies (Railway -> Vercel)
      secure: true, // Required when sameSite=none
      httpOnly: true, // Security best practice
    },
  },

  // Plugins
  plugins: [
    jwt(), // JWT plugin for JWKS endpoint
  ],

  // Trusted origins for CORS
  trustedOrigins: allowedOrigins,
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'better-auth',
    timestamp: new Date().toISOString(),
  });
});

// Mount Better Auth handler as middleware for /api/auth
app.use('/api/auth', async (req, res) => {
  // Convert Express request to Web Request for Better Auth
  // Important: req.url only contains path after /api/auth, so we need to prepend it
  const fullPath = `/api/auth${req.url}`;
  const baseUrl = `${req.protocol}://${req.get('host')}`;
  const url = new URL(fullPath, baseUrl);

  const webRequest = new Request(url, {
    method: req.method,
    headers: req.headers,
    body: req.method !== 'GET' && req.method !== 'HEAD' ? JSON.stringify(req.body) : undefined,
  });

  const response = await auth.handler(webRequest);

  // Convert Web Response back to Express response
  res.status(response.status);
  response.headers.forEach((value, key) => {
    res.setHeader(key, value);
  });

  const body = await response.text();
  res.send(body);
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ Better Auth server running on port ${PORT}`);
  console.log(`📍 Base URL: ${process.env.BETTER_AUTH_URL || `http://localhost:${PORT}`}`);
  console.log(`🔐 Auth endpoints: /api/auth/*`);
  console.log(`🔑 JWKS endpoint: /api/auth/.well-known/jwks.json`);
});
