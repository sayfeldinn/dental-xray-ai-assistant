import { useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { DISEASES } from "../../lib/types";
import { Button, ErrorNote, Field, Input, Select } from "../../components/common/ui";

/** Report a lesion the AI did not flag. Logged as a false negative and sent to the retraining queue. */
export function MissedFindingForm({ scanId }: { scanId: string }) {
  const qc = useQueryClient();
  const [fdi, setFdi] = useState("");
  const [disease, setDisease] = useState<string>(DISEASES[0]);
  const [notes, setNotes] = useState("");
  const report = useMutation({
    mutationFn: () => api.reportMissed({ scan_id: scanId, tooth_fdi: fdi.trim(), disease, notes: notes.trim() || undefined }),
    onSuccess: () => { setFdi(""); setNotes(""); qc.invalidateQueries({ queryKey: ["feedback", scanId] }); },
  });
  const submit = (e: FormEvent) => { e.preventDefault(); report.mutate(); };

  return (
    <form onSubmit={submit} className="space-y-2 rounded-lg bg-slate-50 p-3 ring-1 ring-slate-200">
      <p className="text-sm font-medium">Missed by the AI?</p>
      <div className="grid grid-cols-2 gap-2">
        <Field label="Tooth (FDI)"><Input required pattern="[1-4][1-8]" title="Two digits: quadrant 1-4, tooth 1-8" placeholder="e.g. 36" value={fdi} onChange={(e) => setFdi(e.target.value)} /></Field>
        <Field label="Finding"><Select value={disease} onChange={(e) => setDisease(e.target.value)}>{DISEASES.map((d) => <option key={d}>{d}</option>)}</Select></Field>
      </div>
      <Input placeholder="Notes (optional)" value={notes} onChange={(e) => setNotes(e.target.value)} aria-label="Missed finding notes" />
      <div className="flex items-center gap-2">
        <Button type="submit" variant="secondary" disabled={report.isPending}>Report missed finding</Button>
        {report.isSuccess && <span className="text-xs text-emerald-700">Logged.</span>}
      </div>
      <ErrorNote error={report.error} />
    </form>
  );
}
