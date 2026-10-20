import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import type { Finding, PlanAlert } from "../../lib/types";
import { Button, Card, Empty, ErrorNote, Spinner } from "../../components/common/ui";
import { TreatmentCard } from "./TreatmentCard";
import { ManualTreatmentForm } from "./ManualTreatmentForm";

/** Steps 4-5: generate proposals from validated findings, then decide each treatment and prescription. */
export function PlanTab({ scanId, findings, pendingCount }: { scanId: string; patientId: string; findings: Finding[]; pendingCount: number }) {
  const qc = useQueryClient();
  const [ctx, setCtx] = useState({ active_infection: false, pain: false });
  const [alerts, setAlerts] = useState<Record<string, PlanAlert[]>>({});
  const treatments = useQuery({ queryKey: ["treatments", scanId], queryFn: () => api.listTreatments(scanId) });
  const refresh = () => { qc.invalidateQueries({ queryKey: ["treatments", scanId] }); qc.invalidateQueries({ queryKey: ["feedback", scanId] }); };

  const generate = useMutation({
    mutationFn: () => api.generate(scanId, ctx),
    onSuccess: (res) => { setAlerts(Object.fromEntries(res.plans.map((p) => [p.treatment.id, p.alerts]))); refresh(); },
  });
  const validated = findings.filter((f) => f.review_status === "confirmed" || f.review_status === "modified").length;
  const byId = new Map(findings.map((f) => [f.id, f]));

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <h2 className="font-semibold">Clinical context</h2>
        <p className="mt-1 text-xs text-slate-500">Facts the X-ray cannot show. Drugs are proposed only when you report them.</p>
        <div className="mt-3 flex flex-col gap-2 text-sm sm:flex-row sm:gap-6">
          <label className="flex items-start gap-2">
            <input type="checkbox" checked={ctx.active_infection} onChange={(e) => setCtx({ ...ctx, active_infection: e.target.checked })} className="mt-0.5" />
            <span>Active infection<span className="block text-xs text-slate-500">Abscess with swelling/pus, or systemic signs. Pain alone is not an indication for antibiotics (ADA 2019).</span></span>
          </label>
          <label className="flex items-start gap-2">
            <input type="checkbox" checked={ctx.pain} onChange={(e) => setCtx({ ...ctx, pain: e.target.checked })} className="mt-0.5" />
            <span>Pain needing analgesia</span>
          </label>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <Button disabled={generate.isPending || validated === 0} onClick={() => generate.mutate()}>
            {generate.isPending ? "Generating…" : treatments.data?.total ? "Regenerate proposals" : "Generate proposals"}
          </Button>
          <span className="text-xs text-slate-500">
            Uses {validated} validated finding(s).{pendingCount > 0 && <span className="text-amber-700"> {pendingCount} pending finding(s) are ignored until reviewed.</span>}
            {" "}Regenerating replaces only proposals you have not acted on.
          </span>
        </div>
        {generate.data && generate.data.skipped_finding_ids.length > 0 && (
          <p className="mt-2 text-xs text-slate-600">{generate.data.skipped_finding_ids.length} finding(s) kept as they were because you already decided their treatment.</p>
        )}
        <div className="mt-2"><ErrorNote error={generate.error} /></div>
      </Card>

      {treatments.isLoading && <Spinner />}
      <ErrorNote error={treatments.error} />
      {treatments.data?.total === 0 && <Empty>No treatments yet. Review the findings, then generate proposals.</Empty>}
      {treatments.data?.treatments.map((t) => (
        <TreatmentCard key={t.id} t={t} finding={t.finding_id ? byId.get(t.finding_id) : undefined} alerts={alerts[t.id] ?? []} onChanged={refresh} />
      ))}
      <ManualTreatmentForm scanId={scanId} findings={findings} onDone={refresh} />
    </div>
  );
}
