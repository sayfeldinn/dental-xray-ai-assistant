/**
 * DentalAI API client — the only place that talks to the FastAPI backend.
 *
 * Every `/api/v1` route is authenticated and ownership-checked on the server, so requests carry the
 * dentist's Supabase access token (installed by `configureAuth` from `AuthProvider`). One dentist's
 * data never reaches another: the UI does no filtering of its own.
 *
 * Failures are thrown as `ApiError` (status + backend message), which `ErrorNote` renders verbatim —
 * the backend writes clinician-readable messages, so they are shown unchanged.
 */

import type {
  ClinicalContext,
  FeedbackListResponse,
  FeedbackLog,
  FeedbackSummary,
  Finding,
  FindingListResponse,
  FindingReviewInput,
  MissedFindingReportInput,
  Patient,
  PatientCreate,
  PatientListResponse,
  PatientUpdate,
  Prescription,
  PrescriptionCheckInput,
  PrescriptionCreateInput,
  PrescriptionDecisionInput,
  RecommendationResponse,
  SafetyCheckResult,
  Scan,
  ScanAnalysisResponse,
  ScanListResponse,
  Treatment,
  TreatmentCreateInput,
  TreatmentDecisionInput,
  TreatmentListResponse,
} from "./types";

const BASE_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");
const API_PREFIX = import.meta.env.VITE_API_V1_PREFIX ?? "/api/v1";

/** HTTP failure from the backend. `message` is the backend's own `detail` string. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type TokenGetter = () => Promise<string | null>;

let getToken: TokenGetter = async () => null;
let onUnauthorized: () => void = () => {};

/** Called once by `AuthProvider` so every request carries the session token. */
export function configureAuth(getAccessToken: TokenGetter, unauthorized: () => void): void {
  getToken = getAccessToken;
  onUnauthorized = unauthorized;
}

/** FastAPI returns {"detail": "..."} for domain errors and a list of them for 422 validation errors. */
async function messageOf(response: Response): Promise<string> {
  const fallback = response.statusText || `Request failed with status ${response.status}`;
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "detail" in body) {
      const detail = (body as { detail: unknown }).detail;
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail)) {
        const messages = detail
          .map((item) => (typeof item === "object" && item !== null ? String((item as { msg?: unknown }).msg ?? "") : ""))
          .filter(Boolean);
        if (messages.length) return messages.join(" · ");
      }
    }
  } catch {
    /* not JSON (proxy error page, empty body): fall through to the status text */
  }
  return fallback;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = await getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body !== undefined && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${API_PREFIX}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "Cannot reach the DentalAI API. Is the backend running?");
  }

  if (!response.ok) {
    if (response.status === 401) onUnauthorized(); // session expired: AuthProvider clears the cached data
    throw new ApiError(response.status, await messageOf(response));
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

const json = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });

function query(params: Record<string, string | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) if (value) search.set(key, value);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export const api = {
  /* patients */
  listPatients: (opts: { search?: string; page?: number; page_size?: number } = {}) =>
    request<PatientListResponse>(`/patients${query({
      search: opts.search,
      page: opts.page !== undefined ? String(opts.page) : undefined,
      page_size: opts.page_size !== undefined ? String(opts.page_size) : undefined,
    })}`),
  getPatient: (patientId: string) => request<Patient>(`/patients/${patientId}`),
  createPatient: (data: PatientCreate) => request<Patient>("/patients", json(data)),
  updatePatient: (patientId: string, data: PatientUpdate) =>
    request<Patient>(`/patients/${patientId}`, { method: "PUT", body: JSON.stringify(data) }),
  deletePatient: (patientId: string) => request<void>(`/patients/${patientId}`, { method: "DELETE" }),

  /* scans: the upload goes through FormData so the image is streamed as multipart */
  listScans: (patientId: string, opts: { page?: number; page_size?: number } = {}) =>
    request<ScanListResponse>(`/scans${query({
      patient_id: patientId,
      page: opts.page !== undefined ? String(opts.page) : undefined,
      page_size: opts.page_size !== undefined ? String(opts.page_size) : undefined,
    })}`),
  getScan: (scanId: string) => request<Scan>(`/scans/${scanId}`),
  uploadScan: (patientId: string, file: File, autoAnalyze: boolean) => {
    const form = new FormData();
    form.append("file", file);
    form.append("patient_id", patientId);
    form.append("auto_analyze", String(autoAnalyze));
    return request<ScanAnalysisResponse>("/scans/upload", { method: "POST", body: form });
  },
  reanalyzeScan: (scanId: string) => request<ScanAnalysisResponse>(`/scans/${scanId}/reanalyze`, json({})),
  deleteScan: (scanId: string) => request<void>(`/scans/${scanId}`, { method: "DELETE" }),

  /* findings */
  listFindings: (scanId: string) => request<FindingListResponse>(`/scans/${scanId}/findings`),
  reviewFinding: (input: FindingReviewInput) => request<Finding>("/findings/review", json(input)),

  /* recommendations + decisions */
  generate: (scanId: string, clinicalContext: ClinicalContext) =>
    request<RecommendationResponse>(`/recommendations/scans/${scanId}`, json({ clinical_context: clinicalContext })),
  listTreatments: (scanId: string) => request<TreatmentListResponse>(`/treatments${query({ scan_id: scanId })}`),
  createTreatment: (input: TreatmentCreateInput) => request<Treatment>("/treatments", json(input)),
  decideTreatment: (treatmentId: string, input: TreatmentDecisionInput) =>
    request<Treatment>(`/treatments/${treatmentId}/decision`, json(input)),

  /* prescriptions */
  createPrescription: (input: PrescriptionCreateInput) => request<Prescription>("/prescriptions", json(input)),
  checkPrescription: (input: PrescriptionCheckInput) => request<SafetyCheckResult>("/prescriptions/check", json(input)),
  decidePrescription: (prescriptionId: string, input: PrescriptionDecisionInput) =>
    request<Prescription>(`/prescriptions/${prescriptionId}/decision`, json(input)),

  /* feedback ledger (Step 6) */
  listFeedback: (scanId: string) => request<FeedbackListResponse>(`/feedback${query({ scan_id: scanId })}`),
  feedbackSummary: (scanId: string) => request<FeedbackSummary>(`/feedback/summary${query({ scan_id: scanId })}`),
  reportMissed: (input: MissedFindingReportInput) => request<FeedbackLog>("/feedback/missed-findings", json(input)),
};
