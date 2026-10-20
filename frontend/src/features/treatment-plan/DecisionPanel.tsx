import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { canSubmit, requirementFor, statusAfterModify } from "../../lib/gate";
import type { Prescription } from "../../lib/types";
import { SafetyBadge } from "../../components/common/badges";
import { Button, ErrorNote, Field, Input, Textarea } from "../../components/common/ui";
import { WarningList } from "./WarningList";
import { useSafetyCheck } from "./useSafetyCheck";

type Mode = "accept" | "modify" | "reject";

/**
 * Step 5: the dentist's decision on one proposed prescription.
 *   warning          -> must tick "I have reviewed the warnings"
 *   contraindicated  -> must give a clinical justification (stored, and logged to the feedback ledger)
 * The backend re-checks against the patient's current record and enforces the same gates (422 otherwise).
 */
export function DecisionPanel({ rx, onDone, onCancel }: { rx: Prescription; onDone: () => void; onCancel: () => void }) {
  const [mode, setMode] = useState<Mode>("accept");
  const [edit, setEdit] = useState({ drug_name: rx.drug_name, dosage: rx.dosage, frequency: rx.frequency, duration: rx.duration });
  const [ack, setAck] = useState(false);
  const [reason, setReason] = useState("");

  const check = useSafetyCheck({ patientId: rx.patient_id, drug: edit.drug_name, indication: rx.indication_type, dosage: edit.dosage, frequency: edit.frequency }, mode === "modify");
  const changed = (Object.keys(edit) as (keyof typeof edit)[]).filter((k) => edit[k].trim() !== rx[k]);

  const status = mode === "modify"
    ? check.data && !check.pending ? statusAfterModify(check.data.status, rx.drug_name, edit.drug_name, rx.contraindication_warnings) : null
    : rx.contraindication_status;
  const req = mode === "reject" || !status ? null : requirementFor(status);
  const ready = mode === "reject" || (mode === "accept" && canSubmit(req, ack, reason))
    || (mode === "modify" && changed.length > 0 && !check.pending && !!check.data && canSubmit(req, ack, reason));

  const decide = useMutation({
    mutationFn: () => api.decidePrescription(rx.id, mode === "reject" ? { decision: "rejected" } : {
      decision: mode === "accept" ? "accepted" : "modified",
      ...(mode === "modify" ? Object.fromEntries(changed.map((k) => [k, edit[k].trim()])) : {}),
      acknowledge_warnings: req === "acknowledge" ? ack : undefined,
      override_reason: req === "override" ? reason.trim() : undefined,
    }),
    onSuccess: onDone,
  });

  const set = (k: keyof typeof edit) => (e: { target: { value: string } }) => setEdit({ ...edit, [k]: e.target.value });

  return (
    <div className="mt-3 space-y-3 rounded-lg bg-white p-3 ring-1 ring-brand-600" aria-label={`Decision for ${rx.drug_name}`}>
      <div className="flex gap-1" role="radiogroup" aria-label="Decision">
        {(["accept", "modify", "reject"] as Mode[]).map((m) => (
          <button key={m} role="radio" aria-checked={mode === m} onClick={() => setMode(m)}
            className={`rounded-md px-3 py-1 text-sm capitalize ring-1 ${mode === m ? "bg-brand-600 text-white ring-brand-600" : "ring-slate-300 hover:bg-slate-50"}`}>{m}</button>
        ))}
      </div>

      {mode === "modify" && (
        <div className="space-y-2">
          <div className="grid gap-2 sm:grid-cols-2">
            <Field label="Drug"><Input value={edit.drug_name} onChange={set("drug_name")} /></Field>
            <Field label="Dosage"><Input value={edit.dosage} onChange={set("dosage")} /></Field>
            <Field label="Frequency"><Input value={edit.frequency} onChange={set("frequency")} /></Field>
            <Field label="Duration"><Input value={edit.duration} onChange={set("duration")} /></Field>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-600">Live safety check:</span>
            {check.pending ? <span className="text-slate-400">checking…</span> : status ? <SafetyBadge status={status} /> : null}
          </div>
          <ErrorNote error={check.error} />
          {check.data && !check.pending && <WarningList warnings={check.data.warnings} />}
        </div>
      )}

      {req === "acknowledge" && (
        <label className="flex items-start gap-2 rounded-md bg-amber-50 p-2 text-sm text-amber-900 ring-1 ring-amber-200">
          <input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} className="mt-0.5" />
          I have reviewed the safety warnings for this patient and still want to prescribe.
        </label>
      )}
      {req === "override" && (
        <Field label="Clinical justification for overriding a contraindication" hint="Required. Stored with the prescription and logged for audit.">
          <Textarea value={reason} onChange={(e) => setReason(e.target.value)} className="ring-rose-300" />
        </Field>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <Button variant={mode === "reject" ? "danger" : req === "override" ? "danger" : "success"} disabled={!ready || decide.isPending} onClick={() => decide.mutate()}>
          {mode === "reject" ? "Reject prescription" : req === "override" ? "Override and prescribe" : mode === "modify" ? "Save changes" : "Accept"}
        </Button>
        <Button variant="ghost" onClick={onCancel}>Cancel</Button>
        {mode === "modify" && changed.length === 0 && <span className="text-xs text-slate-500">Edit at least one field.</span>}
      </div>
      <ErrorNote error={decide.error} />
    </div>
  );
}
