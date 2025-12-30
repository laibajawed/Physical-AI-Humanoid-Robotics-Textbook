/**
 * Standalone Better Auth server for local development.
 *
 * Runs on port 3001 to handle authentication API routes.
 *
 * Usage: npx tsx auth-server.ts
 */

// IMPORTANT: Load environment variables SYNCHRONOUSLY before anything else
import { config } from "dotenv";
import { resolve } from "path";

// Load .env.local first (has highest priority), then .env as fallback
const envLocalPath = resolve(process.cwd(), ".env.local");
const envPath = resolve(process.cwd(), ".env");

console.log("Loading environment from:", envLocalPath);
const result = config({ path: envLocalPath });
if (result.error) {
  console.log(".env.local not found, trying .env");
  config({ path: envPath });
} else {
  console.log("Loaded .env.local successfully");
}

// Verify DATABASE_URL is loaded before importing auth
if (!process.env.DATABASE_URL) {
  console.error("ERROR: DATABASE_URL not found in environment");
  console.error("Make sure .env.local exists with DATABASE_URL set");
  process.exit(1);
}

console.log("DATABASE_URL loaded:", process.env.DATABASE_URL?.substring(0, 30) + "...");
console.log("BETTER_AUTH_URL:", process.env.BETTER_AUTH_URL);

// Now start the server (auth module will be imported with env vars already set)
async function startServer() {
  const { serve } = await import("@hono/node-server");
  const { Hono } = await import("hono");
  const { cors } = await import("hono/cors");
  const { auth } = await import("./src/lib/auth.mts");

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

  // Root redirect/status
  app.get("/", (c) => c.json({
    message: "Better Auth development server",
    endpoints: {
      health: "/health",
      auth: "/api/auth/*"
    }
  }));

  // Health check
  app.get("/health", (c) => c.json({ status: "ok" }));

  const port = 3001;
  console.log(`Better Auth server running on http://localhost:${port}`);

  serve({
    fetch: app.fetch,
    port,
  });
}

startServer().catch((err) => {
  console.error("Failed to start server:", err);
  process.exit(1);
});
