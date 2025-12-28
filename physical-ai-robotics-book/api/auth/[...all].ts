/**
 * Better Auth Vercel Serverless Function Handler
 * 
 * This file handles all authentication routes via the /api/auth/* path.
 * It uses Hono as the HTTP framework for Vercel Serverless Functions.
 */

import { Hono } from "hono";
import { handle } from "hono/vercel";
import { auth } from "../../src/lib/auth";

// Create Hono app
const app = new Hono().basePath("/api/auth");

// Handle all Better Auth routes
app.on(["POST", "GET"], "/*", (c) => {
  return auth.handler(c.req.raw);
});

// Export handlers for Vercel
export const GET = handle(app);
export const POST = handle(app);
