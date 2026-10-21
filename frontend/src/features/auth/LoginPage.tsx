import { useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { authConfigured } from "../../lib/supabase";
import { Button, ErrorNote, Field, Input } from "../../components/common/ui";
import { useAuth } from "./AuthProvider";

type Mode = "signin" | "signup" | "reset";

export function LoginPage() {
  const { signIn, signUp, sendReset } = useAuth();
  const [params] = useSearchParams();
  const [mode, setMode] = useState<Mode>(params.get("mode") === "signup" ? "signup" : "signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [info, setInfo] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true); setError(null); setInfo(null);
    try {
      if (mode === "signin") await signIn(email.trim(), password);
      if (mode === "signup") {
        const { needsConfirmation } = await signUp(email.trim(), password, name.trim());
        if (needsConfirmation) setInfo("Account created. Check your email to confirm it, then sign in.");
      }
      if (mode === "reset") { await sendReset(email.trim()); setInfo("If that email has an account, a reset link is on its way."); }
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  const title = { signin: "Sign in", signup: "Create a dentist account", reset: "Reset your password" }[mode];
  return (
    <div className="w-full max-w-sm">
      <div>
        <h1 className="display text-3xl">{title}</h1>
        <p className="mt-2 text-sm text-ink/60">DentalAI is for licensed dental professionals. You only see your own patients.</p>
        {!authConfigured && <p className="mt-3"><ErrorNote error="Supabase Auth is not configured: set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY." /></p>}
        <form onSubmit={submit} className="mt-4 space-y-3">
          {mode === "signup" && <Field label="Full name"><Input required value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" /></Field>}
          <Field label="Email"><Input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" /></Field>
          {mode !== "reset" && (
            <Field label="Password" hint={mode === "signup" ? "At least 8 characters" : undefined}>
              <Input required type="password" minLength={mode === "signup" ? 8 : undefined} value={password} onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === "signup" ? "new-password" : "current-password"} />
            </Field>
          )}
          <Button type="submit" className="w-full" disabled={busy || !authConfigured}>{busy ? "Please wait…" : title}</Button>
          <ErrorNote error={error} />
          {info && <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800 ring-1 ring-emerald-200">{info}</p>}
        </form>
        <div className="mt-4 flex flex-wrap justify-between gap-2 text-sm">
          {mode !== "signin" && <button className="text-brand-700 hover:underline" onClick={() => setMode("signin")}>Back to sign in</button>}
          {mode === "signin" && <button className="text-brand-700 hover:underline" onClick={() => setMode("signup")}>Create an account</button>}
          {mode === "signin" && <button className="text-ink/60 hover:underline" onClick={() => setMode("reset")}>Forgot password?</button>}
        </div>
      </div>
    </div>
  );
}
