/**
 * Demo-mode Supabase stand-in.
 *
 * Used only when VITE_DEMO_MODE=true so the UI is usable without a real
 * Supabase project. Any non-empty email + password signs in; the session is
 * kept in localStorage so a refresh keeps you signed in.
 */
import { DEMO_IMAGE } from './demoData';

const STORAGE_KEY = 'dentalai.demo.session';

const listeners = new Set();

function readSession() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function writeSession(session) {
  try {
    if (session) localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* storage unavailable - session just will not persist */
  }
}

function makeSession(email) {
  const now = Math.floor(Date.now() / 1000);
  return {
    access_token: `demo.${now}.${Math.random().toString(36).slice(2)}`,
    token_type: 'bearer',
    expires_in: 3600,
    expires_at: now + 3600,
    user: {
      id: 'demo-user',
      email,
      user_metadata: { full_name: 'Demo Dentist' },
      app_metadata: { provider: 'email' },
      aud: 'authenticated',
      created_at: new Date().toISOString(),
    },
  };
}

function emit(event, session) {
  listeners.forEach((listener) => {
    try {
      listener(event, session);
    } catch {
      /* a broken listener must not break auth */
    }
  });
}

function authError(message) {
  return { message, status: 400, error_description: message };
}

export function createDemoSupabase() {
  return {
    auth: {
      async getSession() {
        return { data: { session: readSession() }, error: null };
      },

      onAuthStateChange(callback) {
        listeners.add(callback);
        return {
          data: {
            subscription: {
              unsubscribe: () => listeners.delete(callback),
            },
          },
        };
      },

      async signInWithPassword({ email, password }) {
        if (!email || !password) {
          return { data: { user: null, session: null }, error: authError('Email and password are required') };
        }
        const session = makeSession(email);
        writeSession(session);
        emit('SIGNED_IN', session);
        return { data: { user: session.user, session }, error: null };
      },

      async signUp({ email, options }) {
        if (!email) {
          return { data: { user: null, session: null }, error: authError('Email is required') };
        }
        const session = makeSession(email);
        if (options?.data?.full_name) session.user.user_metadata.full_name = options.data.full_name;
        writeSession(session);
        emit('SIGNED_IN', session);
        return { data: { user: session.user, session }, error: null };
      },

      async signOut() {
        writeSession(null);
        emit('SIGNED_OUT', null);
        return { error: null };
      },

      async getUser() {
        const session = readSession();
        return { data: { user: session?.user ?? null }, error: null };
      },
    },

    storage: {
      from(bucket) {
        return {
          async upload(path) {
            return { data: { path, bucket }, error: null };
          },
          getPublicUrl(path) {
            return { data: { publicUrl: DEMO_IMAGE, path } };
          },
          async list() {
            return { data: [], error: null };
          },
        };
      },
    },

    from() {
      return {
        select: () => ({ data: [], error: null }),
      };
    },
  };
}
