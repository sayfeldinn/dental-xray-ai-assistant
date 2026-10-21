import { useState, type FormEvent } from "react";
import { Button, ErrorNote, Field, Input } from "../../components/common/ui";
import { useAuth } from "./AuthProvider";

/** Shown after the dentist follows a password-reset email link. */
export function NewPasswordPage() {
  const { setPassword } = useAuth();
  const [password, setPw] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true); setError(null);
    try { await setPassword(password); } catch (err) { setError(err); } finally { setBusy(false); }
  };
  return (
    <div className="w-full max-w-sm">
      <div>
        <h1 className="display text-3xl">Choose a new password</h1>
        <form onSubmit={submit} className="mt-4 space-y-3">
          <Field label="New password" hint="At least 8 characters">
            <Input required type="password" minLength={8} value={password} onChange={(e) => setPw(e.target.value)} autoComplete="new-password" />
          </Field>
          <Button type="submit" className="w-full" disabled={busy}>Save password</Button>
          <ErrorNote error={error} />
        </form>
      </div>
    </div>
  );
}
