/**
 * DentalAI Supabase client.
 *
 * Supabase provides Auth (dentist accounts), Postgres and the private `xray-scans` storage bucket.
 * The browser only ever holds the *publishable* key plus the dentist's own access token; the
 * service-role key stays in the backend (`SUPABASE_SERVICE_ROLE_KEY`, never a `VITE_` variable).
 *
 * When `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` are missing the app still boots and the login
 * page explains what to set, rather than crashing on an unconfigured client (see `authConfigured`).
 */

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

/** False when the env vars are absent: sign-in is disabled and LoginPage says why. */
export const authConfigured = Boolean(url && anonKey);

/** One client for the whole app (see docs/ARCHITECTURE.md). */
export const supabase: SupabaseClient = createClient(
  url ?? "http://127.0.0.1:54321", // Supabase CLI default; never reached in a configured build
  anonKey ?? "anon-key-not-configured",
  { auth: { persistSession: true, autoRefreshToken: true } },
);
