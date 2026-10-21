import { useState, type FormEvent } from "react";
import { splitList } from "../../lib/format";
import type { Patient, PatientCreate } from "../../lib/types";
import { Button, ErrorNote, Field, Input, Select, Textarea } from "../../components/common/ui";

/** Create or edit a patient. The safety-relevant fields drive every contraindication check. */
export function PatientForm({ initial, submitLabel, busy, error, onSubmit, onCancel }: {
  initial?: Patient;
  submitLabel: string;
  busy: boolean;
  error: unknown;
  onSubmit: (data: PatientCreate) => void;
  onCancel?: () => void;
}) {
  const [f, setF] = useState({
    first_name: initial?.first_name ?? "", last_name: initial?.last_name ?? "", date_of_birth: initial?.date_of_birth ?? "",
    gender: initial?.gender ?? "female", weight_kg: initial?.weight_kg?.toString() ?? "", phone: initial?.phone ?? "",
    allergies: initial?.allergies.join(", ") ?? "", current_medications: initial?.current_medications.join(", ") ?? "",
    medical_conditions: initial?.medical_conditions.join(", ") ?? "", notes: initial?.notes ?? "",
  });
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit({
      first_name: f.first_name.trim(), last_name: f.last_name.trim(), date_of_birth: f.date_of_birth,
      gender: f.gender as Patient["gender"], weight_kg: f.weight_kg ? Number(f.weight_kg) : null,
      allergies: splitList(f.allergies), current_medications: splitList(f.current_medications),
      medical_conditions: splitList(f.medical_conditions), phone: f.phone.trim() || null, email: initial?.email ?? null,
      notes: f.notes.trim() || null,
    });
  };

  return (
    <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <Field label="First name"><Input required value={f.first_name} onChange={set("first_name")} /></Field>
      <Field label="Last name"><Input required value={f.last_name} onChange={set("last_name")} /></Field>
      <Field label="Date of birth"><Input required type="date" value={f.date_of_birth} onChange={set("date_of_birth")} /></Field>
      <Field label="Gender">
        <Select value={f.gender} onChange={set("gender")}><option value="female">Female</option><option value="male">Male</option><option value="other">Other</option></Select>
      </Field>
      <Field label="Weight (kg)" hint="Needed for pediatric dosing"><Input type="number" min="1" step="0.1" value={f.weight_kg} onChange={set("weight_kg")} /></Field>
      <Field label="Phone"><Input value={f.phone} onChange={set("phone")} autoComplete="off" /></Field>
      <div className="sm:col-span-2"><Field label="Notes"><Input value={f.notes} onChange={set("notes")} /></Field></div>
      <Field label="Allergies" hint="Comma separated, e.g. penicillin"><Textarea value={f.allergies} onChange={set("allergies")} /></Field>
      <Field label="Current medications" hint="e.g. warfarin, lisinopril"><Textarea value={f.current_medications} onChange={set("current_medications")} /></Field>
      <div className="sm:col-span-2"><Field label="Medical conditions" hint="e.g. asthma, prosthetic cardiac valve, renal impairment"><Textarea value={f.medical_conditions} onChange={set("medical_conditions")} /></Field></div>
      <div className="flex flex-wrap items-center gap-3 sm:col-span-2 lg:col-span-4">
        <Button type="submit" disabled={busy}>{busy ? "Saving…" : submitLabel}</Button>
        {onCancel && <Button variant="ghost" onClick={onCancel}>Cancel</Button>}
        <ErrorNote error={error} />
      </div>
    </form>
  );
}
