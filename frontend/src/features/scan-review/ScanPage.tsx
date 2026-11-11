import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { dateTime } from "../../lib/format";
import { Button, Card, Empty, ErrorNote, Spinner } from "../../components/common/ui";
import { XrayViewer } from "./XrayViewer";
import { FindingCard } from "./FindingCard";
import { MissedFindingForm } from "./MissedFindingForm";
import { PlanTab } from "../treatment-plan/PlanTab";
import { FeedbackTab } from "../feedback-log/FeedbackTab";

const TABS = [["findings", "1. Review findings"], ["plan", "2. Treatment plan"], ["feedback", "Feedback log"]] as const;
type Tab = (typeof TABS)[number][0];

export function ScanPage() {
  const { scanId = "" } = useParams();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("findings");
  const [selected, setSelected] = useState<string | null>(null);
  const [reanalyzeConfidence, setReanalyzeConfidence] = useState(0.2);
  const scan = useQuery({ queryKey: ["scan", scanId], queryFn: () => api.getScan(scanId) });
  const findings = useQuery({ queryKey: ["findings", scanId], queryFn: () => api.listFindings(scanId) });
  const patient = useQuery({ queryKey: ["patient", scan.data?.patient_id], queryFn: () => api.getPatient(scan.data!.patient_id), enabled: !!scan.data });

  const reanalyze = useMutation({
    mutationFn: () => api.reanalyzeScan(scanId, reanalyzeConfidence),
    onSettled: () => { qc.invalidateQueries({ queryKey: ["scan", scanId] }); qc.invalidateQueries({ queryKey: ["findings", scanId] }); },
  });
  const remove = useMutation({
    mutationFn: () => api.deleteScan(scanId),
    onSuccess: () => navigate(scan.data ? `/patients/${scan.data.patient_id}` : "/"),
  });

  if (scan.isLoading) return <Spinner />;
  if (scan.error) return <ErrorNote error={scan.error} />;
  const s = scan.data!;
  // Stable order (by tooth, then confidence) so cards don't jump when a review refetches the list.
  const list = [...(findings.data?.findings ?? [])].sort(
    (a, b) => a.tooth_fdi.localeCompare(b.tooth_fdi) || b.disease_confidence - a.disease_confidence);
  const pending = list.filter((f) => f.review_status === "pending").length;
  // Advisory layers are stored in raw_ml_output; they never enter the clinical report.
  const raw = s.raw_ml_output ?? {};
  const missing = raw.missing_teeth ?? [];
  const advisory = raw.findings ?? [];

  // Selecting a box should bring its card into view; the card is already rendered.
  const selectFinding = (id: string) => {
    setSelected(id);
    requestAnimationFrame(() => {
      const el = document.getElementById(`finding-${id}`);
      if (el && typeof el.scrollIntoView === "function") {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <Link to={`/patients/${s.patient_id}`} className="text-sm text-brand-700 hover:underline">
          ← {patient.data ? `${patient.data.first_name} ${patient.data.last_name}` : "Patient"}
        </Link>
        <span className="text-sm text-slate-500">Scan of {dateTime(s.created_at)} · {s.status}</span>
        <span className="ml-auto flex gap-2">
          {list.every((f) => f.review_status === "pending") && (
            <>
              <label className="flex items-center gap-1 text-sm text-slate-600">
                Threshold
                <select value={reanalyzeConfidence} onChange={(e) => setReanalyzeConfidence(Number(e.target.value))}
                  className="rounded-md border border-slate-300 px-1.5 py-1">
                  <option value={0.2}>0.20</option>
                  <option value={0.3}>0.30</option>
                  <option value={0.5}>0.50</option>
                </select>
              </label>
              <Button variant="secondary" disabled={reanalyze.isPending} onClick={() => reanalyze.mutate()}
                title="Run the AI again (only before any finding is reviewed)">{reanalyze.isPending ? "Analysing…" : "Re-run AI analysis"}</Button>
            </>
          )}
          <Button variant="ghost" className="text-rose-700" disabled={remove.isPending}
            onClick={() => window.confirm("Delete this scan with its findings, treatments and feedback? This cannot be undone.") && remove.mutate()}>Delete scan</Button>
        </span>
      </div>
      <ErrorNote error={reanalyze.error ?? remove.error} />
      {s.status === "failed" && <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800 ring-1 ring-rose-200">The AI analysis failed for this scan{s.notes ? `: ${s.notes}` : ""}. Start the ML service and re-run the analysis.</p>}

      <nav className="flex gap-1 border-b border-slate-200" role="tablist">
        {TABS.map(([key, label]) => (
          <button key={key} role="tab" aria-selected={tab === key} onClick={() => setTab(key)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${tab === key ? "border-brand-600 text-brand-700" : "border-transparent text-slate-500 hover:text-slate-800"}`}>
            {label}{key === "findings" && pending > 0 && <span className="ml-1.5 rounded-full bg-amber-100 px-1.5 text-xs text-amber-800">{pending}</span>}
          </button>
        ))}
      </nav>

      {tab === "findings" && (
        <div className="grid gap-4 lg:grid-cols-5">
          {/* Pinned on wide screens: selecting a box scrolls the card list, and the X-ray must stay in view. */}
          <div className="space-y-3 lg:sticky lg:top-24 lg:col-span-3 lg:max-h-[calc(100vh-7rem)] lg:self-start lg:overflow-y-auto">
            <XrayViewer src={s.image_url} width={s.image_width} height={s.image_height} findings={list} missing={missing} selectedId={selected} onSelect={selectFinding} />
            <p className="text-xs text-slate-500">Boxes: <span className="text-amber-600">pending</span> · <span className="text-emerald-600">confirmed</span> · <span className="text-sky-600">modified</span> · <span className="text-slate-400">rejected</span> · <span className="text-sky-500">missing (dashed, advisory)</span>. Click a box to select its finding.</p>
            {s.ai_report && (
              <Card className="p-3">
                <details>
                  <summary className="cursor-pointer text-sm font-medium">AI-generated report <span className="font-normal text-amber-700">(pending dentist validation)</span></summary>
                  <pre className="mt-2 whitespace-pre-wrap font-sans text-sm text-slate-700">{s.ai_report}</pre>
                </details>
              </Card>
            )}
            {(missing.length > 0 || advisory.length > 0) && (
              <Card className="p-3">
                <details>
                  <summary className="cursor-pointer text-sm font-medium">
                    Advisory AI signals
                    <span className="ml-2 font-normal text-amber-700">
                      {missing.length > 0 && `${missing.length} missing`}
                      {missing.length > 0 && advisory.length > 0 && " · "}
                      {advisory.length > 0 && `${advisory.length} findings`}
                      {" "}(not in the clinical report)
                    </span>
                  </summary>
                  {missing.length > 0 && (
                    <div className="mt-3">
                      <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Missing teeth ({missing.length})</h3>
                      <ul className="mt-1 grid gap-1 text-sm sm:grid-cols-2">
                        {missing.map((m) => (
                          <li key={m.tooth_fdi} className="flex items-center justify-between gap-2 rounded bg-sky-50 px-2 py-1">
                            <span className="font-medium text-sky-900">Tooth {m.tooth_fdi}</span>
                            <span className="text-xs text-slate-600">
                              {m.gap_probability != null ? `${Math.round(m.gap_probability * 100)}% gap` : "rule"}
                              {" · between "}{m.bounded_by.join("/")}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {advisory.length > 0 && (
                    <div className="mt-3">
                      <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Findings model ({advisory.length})</h3>
                      <ul className="mt-1 grid gap-1 text-sm sm:grid-cols-2">
                        {advisory.slice(0, 12).map((f, i) => (
                          <li key={`${f.finding}-${i}`} className="flex items-center justify-between gap-2 rounded bg-slate-50 px-2 py-1">
                            <span className="text-slate-800">{f.finding}</span>
                            <span className="text-xs text-slate-600">{Math.round(f.confidence * 100)}%</span>
                          </li>
                        ))}
                      </ul>
                      {advisory.length > 12 && <p className="mt-1 text-xs text-slate-500">+{advisory.length - 12} more boxes.</p>}
                    </div>
                  )}
                </details>
              </Card>
            )}
          </div>
          <div className="space-y-3 lg:col-span-2">
            <h2 className="font-semibold">AI findings ({list.length})</h2>
            {findings.isLoading && <Spinner />}
            <ErrorNote error={findings.error} />
            {!findings.isLoading && list.length === 0 && <Empty>The AI flagged nothing on this scan.</Empty>}
            <ul className="space-y-2">
              {list.map((f) => (
                <li key={f.id} id={`finding-${f.id}`}>
                  <FindingCard finding={f} selected={f.id === selected} onSelect={() => setSelected(f.id)} />
                </li>
              ))}
            </ul>
            <MissedFindingForm scanId={s.id} />
          </div>
        </div>
      )}
      {tab === "plan" && <PlanTab scanId={s.id} patientId={s.patient_id} findings={list} pendingCount={pending} />}
      {tab === "feedback" && <FeedbackTab scanId={s.id} />}
    </div>
  );
}
