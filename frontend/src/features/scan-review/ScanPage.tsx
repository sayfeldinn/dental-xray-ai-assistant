import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { dateTime } from "../../lib/format";
import { Card, Empty, ErrorNote, Spinner } from "../../components/common/ui";
import { XrayViewer } from "./XrayViewer";
import { FindingCard } from "./FindingCard";
import { MissedFindingForm } from "./MissedFindingForm";
import { PlanTab } from "../treatment-plan/PlanTab";
import { FeedbackTab } from "../feedback-log/FeedbackTab";

const TABS = [["findings", "1. Review findings"], ["plan", "2. Treatment plan"], ["feedback", "Feedback log"]] as const;
type Tab = (typeof TABS)[number][0];

export function ScanPage() {
  const { scanId = "" } = useParams();
  const [tab, setTab] = useState<Tab>("findings");
  const [selected, setSelected] = useState<string | null>(null);
  const scan = useQuery({ queryKey: ["scan", scanId], queryFn: () => api.getScan(scanId) });
  const findings = useQuery({ queryKey: ["findings", scanId], queryFn: () => api.listFindings(scanId) });
  const patient = useQuery({ queryKey: ["patient", scan.data?.patient_id], queryFn: () => api.getPatient(scan.data!.patient_id), enabled: !!scan.data });

  if (scan.isLoading) return <Spinner />;
  if (scan.error) return <ErrorNote error={scan.error} />;
  const s = scan.data!;
  // Stable order (by tooth, then confidence) so cards don't jump when a review refetches the list.
  const list = [...(findings.data?.findings ?? [])].sort(
    (a, b) => a.tooth_fdi.localeCompare(b.tooth_fdi) || b.disease_confidence - a.disease_confidence);
  const pending = list.filter((f) => f.review_status === "pending").length;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <Link to={`/patients/${s.patient_id}`} className="text-sm text-brand-700 hover:underline">
          ← {patient.data ? `${patient.data.first_name} ${patient.data.last_name}` : "Patient"}
        </Link>
        <span className="text-sm text-slate-500">Scan of {dateTime(s.created_at)} · {s.status}</span>
      </div>

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
          <div className="space-y-3 lg:col-span-3">
            <XrayViewer src={s.image_url} width={s.image_width} height={s.image_height} findings={list} selectedId={selected} onSelect={setSelected} />
            <p className="text-xs text-slate-500">Boxes: <span className="text-amber-600">pending</span> · <span className="text-emerald-600">confirmed</span> · <span className="text-sky-600">modified</span> · <span className="text-slate-400">rejected</span>. Click a box to select its finding.</p>
            {s.ai_report && (
              <Card className="p-3">
                <details>
                  <summary className="cursor-pointer text-sm font-medium">AI-generated report <span className="font-normal text-amber-700">(pending dentist validation)</span></summary>
                  <pre className="mt-2 whitespace-pre-wrap font-sans text-sm text-slate-700">{s.ai_report}</pre>
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
              {list.map((f) => <FindingCard key={f.id} finding={f} selected={f.id === selected} onSelect={() => setSelected(f.id)} />)}
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
