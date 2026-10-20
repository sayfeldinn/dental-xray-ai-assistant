import { useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import { splitList } from "../../lib/format";
import { Button, Card, ErrorNote, Field, Input, Select, Textarea } from "../../components/common/ui";

export function NewPatientForm({ onCreated }: { onCreated: () => void }) {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [f, setF] = useState({ first_name: "", last_name: "", date_of_birth: "", gender: "female", weight_kg: "", allergies: "", current_medications: "", medical_conditions: "" });
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });

  const create = useMutation({
    mutationFn: () => api.createPatient({
      first_name: f.first_name.trim(), last_name: f.last_name.trim(), date_of_birth: f.date_of_birth,
      gender: f.gender as "male" | "female" | "other", weight_kg: f.weight_kg ? Number(f.weight_kg) : null,
      allergies: splitList(f.allergies), current_medications: splitList(f.current_medications),
      medical_conditions: splitList(f.medical_conditions), phone: null, email: null, notes: null,
    }),
    onSuccess: (p) => { qc.invalidateQueries({ queryKey: ["patients"] }); onCreated(); navigate(`/patients/${p.id}`); },
  });

  const submit = (e: FormEvent) => { e.preventDefault(); create.mutate(); };

  return (
    <Card className="p-4">
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Field label="First name"><Input required value={f.first_name} onChange={set("first_name")} /></Field>
        <Field label="Last name"><Input required value={f.last_name} onChange={set("last_name")} /></Field>
        <Field label="Date of birth"><Input required type="date" value={f.date_of_birth} onChange={set("date_of_birth")} /></Field>
        <Field label="Gender">
          <Select value={f.gender} onChange={set("gender")}><option value="female">Female</option><option value="male">Male</option><option value="other">Other</option></Select>
        </Field>
        <Field label="Weight (kg)" hint="Needed for pediatric dosing"><Input type="number" min="1" step="0.1" value={f.weight_kg} onChange={set("weight_kg")} /></Field>
        <Field label="Allergies" hint="Comma separated, e.g. penicillin"><Textarea value={f.allergies} onChange={set("allergies")} /></Field>
        <Field label="Current medications" hint="e.g. warfarin, lisinopril"><Textarea value={f.current_medications} onChange={set("current_medications")} /></Field>
        <Field label="Medical conditions" hint="e.g. asthma, prosthetic cardiac valve"><Textarea value={f.medical_conditions} onChange={set("medical_conditions")} /></Field>
        <div className="flex items-center gap-3 sm:col-span-2 lg:col-span-4">
          <Button type="submit" disabled={create.isPending}>{create.isPending ? "Saving…" : "Create patient"}</Button>
          <ErrorNote error={create.error} />
        </div>
      </form>
    </Card>
  );
}
