/**
 * Standalone Better Auth server for local development.
 *
 * This server runs Better Auth on port 3001 during local development.
 * The frontend should proxy /api/auth/* requests to this server.
 *
 * Usage: node auth-server.js
 */

const { serve } = require("@hono/node-server");
const { Hono } = require("hono");
const { cors } = require("hono/cors");

// We need to transpile the TypeScript auth module
require("ts-node/register");

const { auth } = require("./src/lib/auth.ts");

const app = new Hono();

// Enable CORS for local development
app.use("/*", cors({
  origin: ["http://localhost:3000", "http://localhost:5173"],
  credentials: true,
}));

// Handle all Better Auth routes
app.on(["POST", "GET"], "/api/auth/*", (c) => {
  return auth.handler(c.req.raw);
});

// Health check
app.get("/health", (c) => c.json({ status: "ok" }));

const port = 3001;
console.log(`Better Auth server running on http://localhost:${port}`);

serve({
  fetch: app.fetch,
  port,
});
