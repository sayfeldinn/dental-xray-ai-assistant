import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { humanize } from "../../lib/format";
import { TREATMENT_CATEGORIES, type Finding, type TreatmentCategory } from "../../lib/types";
import { Button, Card, ErrorNote, Field, Input, Select } from "../../components/common/ui";

/** A treatment the dentist writes themselves; stored as confirmed because it is already their decision. */
export function ManualTreatmentForm({ scanId, findings, onDone }: { scanId: string; findings: Finding[]; onDone: () => void }) {
  const [open, setOpen] = useState(false);
  const [f, setF] = useState({ treatment_category: "restorative" as TreatmentCategory, description: "", finding_id: "" });
  const create = useMutation({
    mutationFn: () => api.createTreatment({ scan_id: scanId, treatment_category: f.treatment_category, description: f.description.trim(), finding_id: f.finding_id || undefined }),
    onSuccess: () => { setOpen(false); setF({ ...f, description: "" }); onDone(); },
  });
  const submit = (e: FormEvent) => { e.preventDefault(); create.mutate(); };

  if (!open) return <Button variant="secondary" onClick={() => setOpen(true)}>+ Add your own treatment</Button>;
  return (
    <Card className="p-4">
      <form onSubmit={submit} className="grid gap-2 sm:grid-cols-4">
        <Field label="Category"><Select value={f.treatment_category} onChange={(e) => setF({ ...f, treatment_category: e.target.value as TreatmentCategory })}>{TREATMENT_CATEGORIES.map((c) => <option key={c} value={c}>{humanize(c)}</option>)}</Select></Field>
        <Field label="Linked finding (optional)">
          <Select value={f.finding_id} onChange={(e) => setF({ ...f, finding_id: e.target.value })}>
            <option value="">None</option>
            {findings.filter((x) => x.review_status !== "rejected").map((x) => <option key={x.id} value={x.id}>FDI {x.tooth_fdi} · {x.confirmed_disease ?? x.disease}</option>)}
          </Select>
        </Field>
        <div className="sm:col-span-2"><Field label="Description"><Input required value={f.description} onChange={(e) => setF({ ...f, description: e.target.value })} /></Field></div>
        <div className="flex gap-2 sm:col-span-4">
          <Button type="submit" disabled={create.isPending}>Save treatment</Button>
          <Button variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
          <ErrorNote error={create.error} />
        </div>
      </form>
    </Card>
  );
}
