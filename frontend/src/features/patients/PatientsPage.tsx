import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { ageFrom } from "../../lib/format";
import { Badge, Button, Card, Empty, ErrorNote, Input, Spinner } from "../../components/common/ui";
import { NewPatientForm } from "./NewPatientForm";

export function PatientsPage() {
  const [search, setSearch] = useState("");
  const [creating, setCreating] = useState(false);
  const patients = useQuery({ queryKey: ["patients", search], queryFn: () => api.listPatients(search || undefined) });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">Patients</h1>
        <Input placeholder="Search by name…" value={search} onChange={(e) => setSearch(e.target.value)} className="ml-auto max-w-xs" aria-label="Search patients" />
        <Button onClick={() => setCreating((v) => !v)}>{creating ? "Close" : "New patient"}</Button>
      </div>

      {creating && <NewPatientForm onCreated={() => setCreating(false)} />}

      <Card>
        {patients.isLoading && <Spinner />}
        <div className="p-3"><ErrorNote error={patients.error} /></div>
        {patients.data?.patients.length === 0 && <Empty>No patients found.</Empty>}
        {!!patients.data?.patients.length && (
          <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr><th className="px-4 py-2">Name</th><th className="px-4 py-2">Age</th><th className="px-4 py-2">Weight</th><th className="px-4 py-2">Safety-relevant history</th></tr>
            </thead>
            <tbody>
              {patients.data.patients.map((p) => (
                <tr key={p.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                  <td className="px-4 py-2.5 font-medium">
                    <Link to={`/patients/${p.id}`} className="text-brand-700 hover:underline">{p.first_name} {p.last_name}</Link>
                  </td>
                  <td className="px-4 py-2.5">{ageFrom(p.date_of_birth)}</td>
                  <td className="px-4 py-2.5">{p.weight_kg ? `${p.weight_kg} kg` : <span className="text-slate-400">not recorded</span>}</td>
                  <td className="px-4 py-2.5">
                    <div className="flex flex-wrap gap-1">
                      {p.allergies.map((a) => <Badge key={a} tone="rose">Allergy: {a}</Badge>)}
                      {p.current_medications.map((m) => <Badge key={m} tone="violet">{m}</Badge>)}
                      {p.medical_conditions.map((c) => <Badge key={c} tone="amber">{c}</Badge>)}
                      {!p.allergies.length && !p.current_medications.length && !p.medical_conditions.length && <span className="text-slate-400">none recorded</span>}
                    </div>
                  </td>
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
