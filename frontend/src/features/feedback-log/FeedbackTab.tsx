import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { dateTime, humanize } from "../../lib/format";
import type { FeedbackLog } from "../../lib/types";
import { Badge, Card, Empty, ErrorNote, Spinner } from "../../components/common/ui";

const KEYS = ["tooth_fdi", "disease", "treatment_category", "description", "status", "drug_name", "dosage", "frequency", "duration", "decision", "override_reason"];

/** Only the fields that differ, so the row reads "AI said X, dentist said Y". */
export function describeChange(log: FeedbackLog): { field: string; ai: string; dentist: string }[] {
  const show = (v: unknown) => (v === null || v === undefined || v === "" ? "—" : String(v));
  return KEYS.filter((k) => k in log.dentist_corrected_data || k in log.ai_original_data)
    .filter((k) => k !== "tooth_fdi")   // shown once as the row's context
    .filter((k) => k !== "decision" || log.dentist_corrected_data[k] === "rejected")   // the correction type already says "modified"
    .filter((k) => show(log.ai_original_data[k]) !== show(log.dentist_corrected_data[k]))
    .map((k) => ({ field: humanize(k), ai: show(log.ai_original_data[k]), dentist: show(log.dentist_corrected_data[k]) }));
}

/** Step 6: every place the dentist departed from the AI on this scan (newest first). */
export function FeedbackTab({ scanId }: { scanId: string }) {
  const logs = useQuery({ queryKey: ["feedback", scanId], queryFn: () => api.listFeedback(scanId) });
  const summary = useQuery({ queryKey: ["feedback", scanId, "summary"], queryFn: () => api.feedbackSummary(scanId) });

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">Corrections are recorded automatically when you reject or relabel a finding, report a missed one, or change, override or reject a proposal. Detection corrections are also sent to the model's retraining queue.</p>
      {summary.data && summary.data.total > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(summary.data.by_correction_type).map(([k, n]) => <Badge key={k} tone="violet">{humanize(k)}: {n}</Badge>)}
        </div>
      )}
      <Card>
        {logs.isLoading && <Spinner />}
        <div className="p-3"><ErrorNote error={logs.error} /></div>
        {logs.data?.total === 0 && <Empty>No corrections yet: everything the AI proposed so far was accepted, or not reviewed.</Empty>}
        {!!logs.data?.total && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr><th className="px-4 py-2">When</th><th className="px-4 py-2">Stage</th><th className="px-4 py-2">Correction</th><th className="px-4 py-2">AI → Dentist</th><th className="px-4 py-2">Notes</th></tr>
              </thead>
              <tbody>
                {logs.data.logs.map((l) => (
                  <tr key={l.id} className="border-b border-slate-100 align-top last:border-0">
                    <td className="whitespace-nowrap px-4 py-2 text-slate-500">{dateTime(l.created_at)}</td>
                    <td className="px-4 py-2">{humanize(l.stage)}</td>
                    <td className="px-4 py-2"><Badge tone="violet">{humanize(l.correction_type)}</Badge></td>
                    <td className="px-4 py-2">
                      {"tooth_fdi" in l.ai_original_data && <span className="mr-1 text-slate-500">FDI {String(l.ai_original_data.tooth_fdi)}:</span>}
                      {describeChange(l).map((c) => <div key={c.field}><span className="text-slate-500">{c.field}:</span> {c.ai} → <strong>{c.dentist}</strong></div>)}
                    </td>
                    <td className="px-4 py-2 text-slate-600">{l.notes ?? ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
