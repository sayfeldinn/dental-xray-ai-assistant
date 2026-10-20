import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { pct, toothName } from "../../lib/format";
import { DISEASES, type Finding } from "../../lib/types";
import { ReviewBadge } from "../../components/common/badges";
import { Button, ErrorNote, Select, Textarea } from "../../components/common/ui";

/** Step 3: the dentist confirms, rejects or relabels one AI detection. Rejections and relabels feed the feedback ledger. */
export function FindingCard({ finding: f, selected, onSelect }: { finding: Finding; selected: boolean; onSelect: () => void }) {
  const qc = useQueryClient();
  const [editing, setEditing] = useState(f.review_status === "pending");
  const [disease, setDisease] = useState(f.confirmed_disease ?? f.disease);
  const [notes, setNotes] = useState(f.dentist_notes ?? "");

  const review = useMutation({
    mutationFn: (status: "confirmed" | "rejected" | "modified") => api.reviewFinding({
      finding_id: f.id, review_status: status, dentist_notes: notes.trim() || undefined,
      confirmed_disease: status === "modified" ? disease : undefined,
    }),
    onSuccess: () => {
      setEditing(false);
      qc.invalidateQueries({ queryKey: ["findings", f.scan_id] });
      qc.invalidateQueries({ queryKey: ["feedback", f.scan_id] });
    },
  });

  const relabelled = disease !== f.disease;
  return (
    <li className={`rounded-lg p-3 ring-1 transition ${selected ? "bg-brand-50 ring-brand-600" : "bg-white ring-slate-200"}`} onClick={onSelect}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-semibold">FDI {f.tooth_fdi}</span>
        <span className="text-xs text-slate-500">{toothName(f.tooth_fdi)}</span>
        <span className="ml-auto"><ReviewBadge status={f.review_status} /></span>
      </div>
      <p className="mt-1 text-sm">
        AI: <strong>{f.disease}</strong> <span className="text-slate-500">({pct(f.disease_confidence)} confidence)</span>
        {f.confirmed_disease && f.confirmed_disease !== f.disease && <> → dentist: <strong>{f.confirmed_disease}</strong></>}
      </p>
      {f.dentist_notes && !editing && <p className="mt-1 text-xs text-slate-600">Note: {f.dentist_notes}</p>}

      {editing ? (
        <div className="mt-2 space-y-2" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-600">Diagnosis</span>
            <Select value={disease} onChange={(e) => setDisease(e.target.value)} aria-label={`Diagnosis for tooth ${f.tooth_fdi}`} className="max-w-48">
              {DISEASES.map((d) => <option key={d}>{d}</option>)}
            </Select>
          </div>
          <Textarea placeholder="Notes (optional)" value={notes} onChange={(e) => setNotes(e.target.value)} aria-label="Notes" />
          <div className="flex flex-wrap gap-2">
            {relabelled
              ? <Button variant="primary" disabled={review.isPending} onClick={() => review.mutate("modified")}>Save as {disease}</Button>
              : <Button variant="success" disabled={review.isPending} onClick={() => review.mutate("confirmed")}>Confirm</Button>}
            <Button variant="secondary" disabled={review.isPending} onClick={() => review.mutate("rejected")}>Reject (false positive)</Button>
            {f.review_status !== "pending" && <Button variant="ghost" onClick={() => setEditing(false)}>Cancel</Button>}
          </div>
          <ErrorNote error={review.error} />
        </div>
      ) : (
        <Button variant="ghost" className="mt-1 -ml-2" onClick={(e) => { e.stopPropagation(); setEditing(true); }}>Change review</Button>
      )}
    </li>
  );
}
