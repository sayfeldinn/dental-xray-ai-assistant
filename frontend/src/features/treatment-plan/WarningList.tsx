import type { SafetyWarning } from "../../lib/types";
import { SeverityBadge } from "../../components/common/badges";

export function WarningList({ warnings }: { warnings: SafetyWarning[] }) {
  if (!warnings.length) return null;
  return (
    <ul className="space-y-1.5">
      {warnings.map((w, i) => (
        <li key={`${w.rule_id}-${i}`} className="rounded-md bg-slate-50 p-2 text-xs ring-1 ring-slate-200">
          <div className="flex items-center gap-2">
            <SeverityBadge severity={w.severity} />
            <span className="font-mono text-slate-500">{w.rule_id}</span>
          </div>
          <p className="mt-1 text-slate-800">{w.message}</p>
          <p className="mt-0.5 text-slate-500">Source: {w.source}</p>
        </li>
      ))}
    </ul>
  );
}
