import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(" ");

type Variant = "primary" | "secondary" | "danger" | "ghost" | "success";
const VARIANTS: Record<Variant, string> = {
  primary: "bg-brand-600 text-white hover:bg-brand-700 disabled:bg-brand-600/40",
  success: "bg-emerald-600 text-white hover:bg-emerald-700 disabled:bg-emerald-600/40",
  danger: "bg-red-800 text-white hover:bg-red-900 disabled:bg-red-800/40",   // darker than the brand crimson so destructive reads differently
  secondary: "bg-white text-ink ring-1 ring-brand-200 hover:bg-brand-50 disabled:text-slate-400",
  ghost: "text-ink/70 hover:bg-brand-50 disabled:text-slate-300",
};

export function Button({ variant = "primary", className, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      type="button"
      {...props}
      className={cx("inline-flex items-center justify-center gap-1.5 rounded-full px-4 py-1.5 text-sm font-semibold transition-colors disabled:cursor-not-allowed", VARIANTS[variant], className)}
    />
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <section className={cx("rounded-2xl bg-white ring-1 ring-brand-100", className)}>{children}</section>;
}

export type Tone = "slate" | "amber" | "emerald" | "rose" | "sky" | "violet";
const TONES: Record<Tone, string> = {
  slate: "bg-slate-100 text-slate-700 ring-slate-200",
  amber: "bg-amber-50 text-amber-800 ring-amber-200",
  emerald: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  rose: "bg-rose-50 text-rose-800 ring-rose-200",
  sky: "bg-sky-50 text-sky-800 ring-sky-200",
  violet: "bg-violet-50 text-violet-800 ring-violet-200",
};

export function Badge({ tone = "slate", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={cx("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset whitespace-nowrap", TONES[tone])}>{children}</span>;
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-2 p-4 text-sm text-slate-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-100 border-t-brand-600" />
      {label}
    </div>
  );
}

export function ErrorNote({ error }: { error: unknown }) {
  if (!error) return null;
  const msg = error instanceof Error ? error.message : String(error);
  return <p role="alert" className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800 ring-1 ring-rose-200">{msg}</p>;
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="p-6 text-center text-sm text-slate-500">{children}</p>;
}

/**
 * Prev/next pager for the paginated list endpoints. Renders nothing when everything fits on
 * one page, so it never clutters small lists.
 */
export function Pagination({ page, pageSize, total, onPage, label = "results" }: {
  page: number; pageSize: number; total: number; onPage: (page: number) => void; label?: string;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (total <= pageSize) return null;
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);
  return (
    <div className="flex items-center justify-between gap-3 border-t border-brand-100 px-4 py-2.5 text-sm">
      <span className="text-slate-500">
        {from}–{to} of {total} {label}
      </span>
      <div className="flex items-center gap-2">
        <Button variant="secondary" disabled={page <= 1} onClick={() => onPage(page - 1)}>Previous</Button>
        <span className="text-xs text-slate-500">Page {page} of {pages}</span>
        <Button variant="secondary" disabled={page >= pages} onClick={() => onPage(page + 1)}>Next</Button>
      </div>
    </div>
  );
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  // The hint sits outside <label> so the field's accessible name is just the label.
  return (
    <div className="text-sm">
      <label className="block">
        <span className="mb-1 block font-medium text-ink/80">{label}</span>
        {children}
      </label>
      {hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
    </div>
  );
}

const INPUT = "w-full rounded-xl border-0 bg-white px-3 py-2 text-sm ring-1 ring-brand-200/80 placeholder:text-ink/35 focus:ring-2 focus:ring-brand-600 focus:outline-none";
export const Input = (p: InputHTMLAttributes<HTMLInputElement>) => <input {...p} className={cx(INPUT, p.className)} />;
export const Textarea = (p: TextareaHTMLAttributes<HTMLTextAreaElement>) => <textarea rows={2} {...p} className={cx(INPUT, p.className)} />;
export const Select = (p: SelectHTMLAttributes<HTMLSelectElement>) => <select {...p} className={cx(INPUT, "bg-white", p.className)} />;
