import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { ageFrom, dateTime } from "../../lib/format";
import type { Patient } from "../../lib/types";
import { Badge, Button, Card, Empty, ErrorNote, Spinner } from "../../components/common/ui";
import { PatientForm } from "./PatientForm";

const SCAN_TONE = { uploaded: "slate", processing: "violet", analyzed: "sky", reviewed: "emerald", failed: "rose" } as const;

export function PatientPage() {
  const { patientId = "" } = useParams();
  const patient = useQuery({ queryKey: ["patient", patientId], queryFn: () => api.getPatient(patientId) });
  const scans = useQuery({ queryKey: ["scans", patientId], queryFn: () => api.listScans(patientId) });

  if (patient.isLoading) return <Spinner />;
  if (patient.error) return <ErrorNote error={patient.error} />;
  const p = patient.data!;

  return (
    <div className="space-y-4">
      <Link to="/" className="text-sm text-brand-700 hover:underline">← Patients</Link>
      <ProfileCard p={p} />
      <PatientActions p={p} />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <h2 className="border-b border-slate-200 px-4 py-2.5 font-semibold">Panoramic scans</h2>
          {scans.isLoading && <Spinner />}
          <div className="p-3"><ErrorNote error={scans.error} /></div>
          {scans.data?.scans.length === 0 && <Empty>No scans yet. Upload one to start the review.</Empty>}
          <ul className="divide-y divide-slate-100">
            {scans.data?.scans.map((s) => (
              <li key={s.id} className="flex items-center gap-3 px-4 py-2.5 text-sm">
                <Link to={`/scans/${s.id}`} className="font-medium text-brand-700 hover:underline">{dateTime(s.created_at)}</Link>
                <span className="text-slate-500">{s.scan_type}</span>
                <span className="ml-auto"><Badge tone={SCAN_TONE[s.status]}>{s.status}</Badge></span>
              </li>
            ))}
          </ul>
        </Card>
        <UploadCard patientId={p.id} />
      </div>
    </div>
  );
}

function ProfileCard({ p }: { p: Patient }) {
  const chips = (items: string[], tone: "rose" | "violet" | "amber", empty: string) =>
    items.length ? items.map((x) => <Badge key={x} tone={tone}>{x}</Badge>) : <span className="text-sm text-slate-400">{empty}</span>;
  return (
    <Card className="p-4">
      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
        <h1 className="display text-3xl">{p.first_name} {p.last_name}</h1>
        <span className="text-sm text-slate-600">{ageFrom(p.date_of_birth)} years · {p.gender} · {p.weight_kg ? `${p.weight_kg} kg` : "weight not recorded"}</span>
      </div>
      <p className="mt-1 text-xs text-slate-500">These fields drive the contraindication checks. Keep them current before generating a plan.</p>
      <dl className="mt-3 grid gap-3 sm:grid-cols-3">
        <div><dt className="mb-1 text-xs font-medium uppercase text-slate-500">Allergies</dt><dd className="flex flex-wrap gap-1">{chips(p.allergies, "rose", "None recorded")}</dd></div>
        <div><dt className="mb-1 text-xs font-medium uppercase text-slate-500">Medications</dt><dd className="flex flex-wrap gap-1">{chips(p.current_medications, "violet", "None recorded")}</dd></div>
        <div><dt className="mb-1 text-xs font-medium uppercase text-slate-500">Conditions</dt><dd className="flex flex-wrap gap-1">{chips(p.medical_conditions, "amber", "None recorded")}</dd></div>
      </dl>
    </Card>
  );
}

function PatientActions({ p }: { p: Patient }) {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const update = useMutation({
    mutationFn: (data: Parameters<typeof api.updatePatient>[1]) => api.updatePatient(p.id, data),
    onSuccess: () => { setEditing(false); qc.invalidateQueries({ queryKey: ["patient", p.id] }); qc.invalidateQueries({ queryKey: ["patients"] }); },
  });
  const remove = useMutation({
    mutationFn: () => api.deletePatient(p.id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["patients"] }); navigate("/"); },
  });
  const confirmDelete = () => {
    if (window.confirm(`Delete ${p.first_name} ${p.last_name} and ALL their scans, findings, treatments and prescriptions? This cannot be undone.`)) remove.mutate();
  };

  if (editing) {
    return (
      <Card className="p-4">
        <h2 className="mb-3 font-semibold">Edit patient</h2>
        <PatientForm initial={p} submitLabel="Save changes" busy={update.isPending} error={update.error} onSubmit={(d) => update.mutate(d)} onCancel={() => setEditing(false)} />
      </Card>
    );
  }
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button variant="secondary" onClick={() => setEditing(true)}>Edit patient</Button>
      <Button variant="ghost" className="text-rose-700" disabled={remove.isPending} onClick={confirmDelete}>Delete patient</Button>
      <ErrorNote error={remove.error} />
    </div>
  );
}

function UploadCard({ patientId }: { patientId: string }) {
  const qc = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [analyze, setAnalyze] = useState(true);
  const upload = useMutation({
    mutationFn: () => api.uploadScan(patientId, file!, analyze),
    onSettled: () => qc.invalidateQueries({ queryKey: ["scans", patientId] }),
  });
  const submit = (e: FormEvent) => { e.preventDefault(); if (file) upload.mutate(); };

  return (
    <Card className="p-4">
      <h2 className="mb-3 font-semibold">Upload X-ray</h2>
      <form onSubmit={submit} className="space-y-3 text-sm">
        <input type="file" accept="image/png,image/jpeg,image/webp" aria-label="X-ray image" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="block w-full text-sm file:mr-3 file:rounded-md file:border-0 file:bg-brand-50 file:px-3 file:py-1.5 file:text-brand-700" />
        <label className="flex items-center gap-2"><input type="checkbox" checked={analyze} onChange={(e) => setAnalyze(e.target.checked)} /> Run AI analysis (needs the ML service on port 8001)</label>
        <Button type="submit" disabled={!file || upload.isPending}>{upload.isPending ? "Uploading and analysing…" : "Upload"}</Button>
        {upload.data && (
          <p className="text-emerald-700">
            Uploaded. {upload.data.findings_count} finding(s) to review. <Link className="underline" to={`/scans/${upload.data.scan_id}`}>Open scan</Link>
          </p>
        )}
        <ErrorNote error={upload.error} />
      </form>
    </Card>
  );
}
