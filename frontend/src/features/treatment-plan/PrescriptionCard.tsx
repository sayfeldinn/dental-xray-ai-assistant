import { useState } from "react";
import type { Prescription } from "../../lib/types";
import { humanize } from "../../lib/format";
import { DecisionBadge, SafetyBadge } from "../../components/common/badges";
import { Button } from "../../components/common/ui";
import { DecisionPanel } from "./DecisionPanel";
import { WarningList } from "./WarningList";

export function PrescriptionCard({ rx, locked, onChanged }: { rx: Prescription; locked: boolean; onChanged: () => void }) {
  const [deciding, setDeciding] = useState(false);
  return (
    <div className="rounded-lg bg-slate-50/60 p-3 ring-1 ring-slate-200">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-semibold">{rx.drug_name}</span>
        <span className="text-xs text-slate-500">{humanize(rx.indication_type)}</span>
        <span className="ml-auto flex gap-1"><SafetyBadge status={rx.contraindication_status} /><DecisionBadge status={rx.dentist_status} /></span>
      </div>
      <p className="mt-1 text-sm">{rx.dosage} · {rx.frequency} · {rx.duration}</p>
      {rx.instructions && <p className="mt-1 text-xs text-slate-600">{rx.instructions}</p>}
      {rx.dentist_override_reason && <p className="mt-1 text-xs text-rose-700">Override reason: {rx.dentist_override_reason}</p>}
      <div className="mt-2"><WarningList warnings={rx.contraindication_warnings} /></div>
      {rx.dentist_status === "proposed" && !deciding && (
        <Button className="mt-2" disabled={locked} title={locked ? "The treatment was cancelled" : undefined} onClick={() => setDeciding(true)}>Review prescription</Button>
      )}
      {deciding && <DecisionPanel rx={rx} onCancel={() => setDeciding(false)} onDone={() => { setDeciding(false); onChanged(); }} />}
    </div>
  );
}
