import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../lib/api";
import type { IndicationType } from "../../lib/types";

function useDebounced<T>(value: T, ms = 400): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

/** Live, stateless contraindication check while the dentist edits a drug (POST /prescriptions/check). */
export function useSafetyCheck(args: { patientId: string; drug: string; indication: IndicationType; dosage: string; frequency: string }, enabled: boolean) {
  const d = useDebounced(args);
  const ready = enabled && d.drug.trim().length > 1;
  const settled = JSON.stringify(d) === JSON.stringify(args);
  const q = useQuery({
    queryKey: ["check", d],
    queryFn: () => api.checkPrescription({ patient_id: d.patientId, drug_name: d.drug.trim(), indication_type: d.indication, dosage: d.dosage || undefined, frequency: d.frequency || undefined }),
    enabled: ready,
  });
  return { ...q, pending: ready && (!settled || q.isFetching) };
}
