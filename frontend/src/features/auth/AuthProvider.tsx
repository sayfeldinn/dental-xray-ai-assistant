import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { useQueryClient } from "@tanstack/react-query";
import { configureAuth } from "../../lib/api";
import { supabase } from "../../lib/supabase";

interface AuthState {
  session: Session | null;
  loading: boolean;
  /** True after the user followed a password-reset link and must choose a new password. */
  recovering: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, fullName: string) => Promise<{ needsConfirmation: boolean }>;
  sendReset: (email: string) => Promise<void>;
  setPassword: (password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

const fail = (error: { message: string } | null) => { if (error) throw new Error(error.message); };

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [recovering, setRecovering] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => { setSession(data.session); setLoading(false); });
    const { data } = supabase.auth.onAuthStateChange((event, s) => {
      setSession(s);
      if (event === "PASSWORD_RECOVERY") setRecovering(true);
      if (event === "SIGNED_OUT") qc.clear();   // never show one dentist's cached data to the next
    });
    configureAuth(
      async () => (await supabase.auth.getSession()).data.session?.access_token ?? null,
      () => { void supabase.auth.signOut(); },
    );
    return () => data.subscription.unsubscribe();
  }, [qc]);

  const value = useMemo<AuthState>(() => ({
    session, loading, recovering,
    signIn: async (email, password) => fail((await supabase.auth.signInWithPassword({ email, password })).error),
    signUp: async (email, password, fullName) => {
      const { data, error } = await supabase.auth.signUp({
        email, password, options: { data: { full_name: fullName }, emailRedirectTo: window.location.origin },
      });
      fail(error);
      return { needsConfirmation: !data.session };
    },
    sendReset: async (email) => fail((await supabase.auth.resetPasswordForEmail(email, { redirectTo: window.location.origin })).error),
    setPassword: async (password) => { fail((await supabase.auth.updateUser({ password })).error); setRecovering(false); },
    signOut: async () => { await supabase.auth.signOut(); },
  }), [session, loading, recovering]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
