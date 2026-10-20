import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../../lib/api";
import type { IndicationType, Treatment } from "../../lib/types";
import { humanize } from "../../lib/format";
import { SafetyBadge } from "../../components/common/badges";
import { Button, ErrorNote, Field, Input, Select } from "../../components/common/ui";
import { WarningList } from "./WarningList";
import { useSafetyCheck } from "./useSafetyCheck";

const INDICATIONS: IndicationType[] = ["active_infection", "pre_procedure_prophylaxis", "pain_management"];
const KNOWN = ["Amoxicillin", "Clindamycin", "Azithromycin", "Cephalexin", "Metronidazole", "Ibuprofen", "Paracetamol"];

/** A dentist-authored prescription. It is safety-checked and still needs a decision, like an AI proposal. */
export function ManualPrescriptionForm({ treatment, onDone, onCancel }: { treatment: Treatment; onDone: () => void; onCancel: () => void }) {
  const [f, setF] = useState({ drug_name: "", dosage: "", frequency: "", duration: "", indication_type: "pain_management" as IndicationType });
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  const check = useSafetyCheck({ patientId: treatment.patient_id, drug: f.drug_name, indication: f.indication_type, dosage: f.dosage, frequency: f.frequency }, true);
  const create = useMutation({ mutationFn: () => api.createPrescription({ treatment_id: treatment.id, ...f }), onSuccess: onDone });
  const submit = (e: FormEvent) => { e.preventDefault(); create.mutate(); };

  return (
    <form onSubmit={submit} className="space-y-2 rounded-lg bg-white p-3 ring-1 ring-slate-300">
      <div className="grid gap-2 sm:grid-cols-5">
        <Field label="Drug"><Input required list="known-drugs" value={f.drug_name} onChange={set("drug_name")} /></Field>
        <Field label="Dosage"><Input required placeholder="400 mg" value={f.dosage} onChange={set("dosage")} /></Field>
        <Field label="Frequency"><Input required placeholder="every 6 hours" value={f.frequency} onChange={set("frequency")} /></Field>
        <Field label="Duration"><Input required placeholder="3 days" value={f.duration} onChange={set("duration")} /></Field>
        <Field label="Indication"><Select value={f.indication_type} onChange={set("indication_type")}>{INDICATIONS.map((i) => <option key={i} value={i}>{humanize(i)}</option>)}</Select></Field>
      </div>
      <datalist id="known-drugs">{KNOWN.map((d) => <option key={d} value={d} />)}</datalist>
      {f.drug_name.trim().length > 1 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm"><span className="text-slate-600">Safety check:</span>{check.pending ? <span className="text-slate-400">checking…</span> : check.data && <SafetyBadge status={check.data.status} />}</div>
          {check.data && !check.pending && <WarningList warnings={check.data.warnings} />}
        </div>
      )}
      <div className="flex gap-2">
        <Button type="submit" disabled={create.isPending}>Add (still needs your decision)</Button>
        <Button variant="ghost" onClick={onCancel}>Cancel</Button>
      </div>
      <ErrorNote error={create.error ?? check.error} />
    </form>
  );
}
