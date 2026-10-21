import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import { Card } from "../../components/common/ui";
import { PatientForm } from "./PatientForm";

export function NewPatientForm({ onCreated }: { onCreated: () => void }) {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const create = useMutation({
    mutationFn: api.createPatient,
    onSuccess: (p) => { qc.invalidateQueries({ queryKey: ["patients"] }); onCreated(); navigate(`/patients/${p.id}`); },
  });
  return (
    <Card className="p-4">
      <PatientForm submitLabel="Create patient" busy={create.isPending} error={create.error} onSubmit={(d) => create.mutate(d)} onCancel={onCreated} />
    </Card>
  );
}
