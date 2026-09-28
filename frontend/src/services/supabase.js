/**
 * Supabase client configuration
 */
import { createClient } from '@supabase/supabase-js';
import { createDemoSupabase } from './demoSupabase';

// Demo mode (VITE_DEMO_MODE=true) serves fixture data from the browser and
// needs no Supabase project. Set it to false once real credentials exist.
export const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true';

function buildClient() {
  if (isDemoMode) {
    return createDemoSupabase();
  }

  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
  const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error('Missing Supabase environment variables');
  }

  return createClient(supabaseUrl, supabaseAnonKey);
}

export const supabase = buildClient();
