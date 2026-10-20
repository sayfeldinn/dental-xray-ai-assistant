import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { humanize, toothName } from "../../lib/format";
import { TREATMENT_CATEGORIES, type Finding, type PlanAlert, type TreatmentCategory, type TreatmentWithPrescriptions } from "../../lib/types";
import { DecisionBadge } from "../../components/common/badges";
import { Badge, Button, Card, ErrorNote, Field, Select, Textarea } from "../../components/common/ui";
import { PrescriptionCard } from "./PrescriptionCard";
import { ManualPrescriptionForm } from "./ManualPrescriptionForm";

export function TreatmentCard({ t, finding, alerts, onChanged }: { t: TreatmentWithPrescriptions; finding?: Finding; alerts: PlanAlert[]; onChanged: () => void }) {
  const [mode, setMode] = useState<"view" | "modify" | "cancel">("view");
  const [category, setCategory] = useState<TreatmentCategory>(t.treatment_category);
  const [description, setDescription] = useState(t.description);
  const [notes, setNotes] = useState("");
  const [addingRx, setAddingRx] = useState(false);

  const decide = useMutation({
    mutationFn: (decision: "confirmed" | "modified" | "cancelled") => api.decideTreatment(t.id, {
      decision,
      ...(decision === "modified" ? { treatment_category: category !== t.treatment_category ? category : undefined, description: description.trim() !== t.description ? description.trim() : undefined } : {}),
      dentist_notes: notes.trim() || undefined,
    }),
    onSuccess: () => { setMode("view"); onChanged(); },
  });
  const modified = category !== t.treatment_category || description.trim() !== t.description;
  const decided = t.status === "confirmed" || t.status === "modified";

  return (
    <Card className="p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="sky">{humanize(t.treatment_category)}</Badge>
        {finding && <span className="text-sm font-medium">FDI {finding.tooth_fdi} · {finding.confirmed_disease ?? finding.disease} <span className="font-normal text-slate-500">({toothName(finding.tooth_fdi)})</span></span>}
        {!t.finding_id && <span className="text-sm text-slate-500">Dentist-authored</span>}
        <span className="ml-auto"><DecisionBadge status={t.status} /></span>
      </div>
      <p className="mt-2 text-sm">{t.description}</p>
      {t.clinical_justification && <p className="mt-1 text-xs text-slate-500">Why: {t.clinical_justification}</p>}
      {t.dentist_notes && <p className="mt-1 text-xs text-slate-600">Dentist notes: {t.dentist_notes}</p>}
      {alerts.map((a, i) => <p key={`${a.code}-${i}`}className="mt-2 rounded-md bg-amber-50 px-2 py-1 text-xs text-amber-900 ring-1 ring-amber-200">{a.message}</p>)}

      {t.status === "proposed" && mode === "view" && (
        <div className="mt-3 flex flex-wrap gap-2">
          <Button variant="success" disabled={decide.isPending} onClick={() => decide.mutate("confirmed")}>Confirm treatment</Button>
          <Button variant="secondary" onClick={() => setMode("modify")}>Modify</Button>
          <Button variant="ghost" onClick={() => setMode("cancel")}>Cancel treatment</Button>
        </div>
      )}
      {mode !== "view" && (
        <div className="mt-3 space-y-2 rounded-lg bg-slate-50 p-3 ring-1 ring-slate-200">
          {mode === "modify" && (
            <div className="grid gap-2 sm:grid-cols-3">
              <Field label="Category"><Select value={category} onChange={(e) => setCategory(e.target.value as TreatmentCategory)}>{TREATMENT_CATEGORIES.map((c) => <option key={c} value={c}>{humanize(c)}</option>)}</Select></Field>
              <div className="sm:col-span-2"><Field label="Description"><Textarea value={description} onChange={(e) => setDescription(e.target.value)} /></Field></div>
            </div>
          )}
          <Field label={mode === "cancel" ? "Reason (optional, logged)" : "Notes (optional)"}><Textarea value={notes} onChange={(e) => setNotes(e.target.value)} /></Field>
          <div className="flex gap-2">
            {mode === "modify"
              ? <Button disabled={!modified || decide.isPending} onClick={() => decide.mutate("modified")}>Save modified treatment</Button>
              : <Button variant="danger" disabled={decide.isPending} onClick={() => decide.mutate("cancelled")}>Cancel treatment</Button>}
            <Button variant="ghost" onClick={() => setMode("view")}>Back</Button>
          </div>
        </div>
      )}
      <ErrorNote error={decide.error} />

      {(t.prescriptions.length > 0 || decided) && (
        <div className="mt-4 space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Prescriptions</h3>
          {t.prescriptions.map((rx) => <PrescriptionCard key={rx.id} rx={rx} locked={t.status === "cancelled"} onChanged={onChanged} />)}
          {decided && (addingRx
            ? <ManualPrescriptionForm treatment={t} onDone={() => { setAddingRx(false); onChanged(); }} onCancel={() => setAddingRx(false)} />
            : <Button variant="ghost" className="-ml-2" onClick={() => setAddingRx(true)}>+ Add prescription</Button>)}
        </div>
      )}
    </Card>
  );
}
