/**
 * DentalAI shared types.
 *
 * Every shape here mirrors a Pydantic model in `backend/app/domain/` so the UI and the API
 * cannot drift apart. If you change one, change the other in the same PR (see docs/ARCHITECTURE.md).
 *
 * UUIDs and dates arrive from JSON, so they are strings here even though the backend types them
 * as UUID/datetime. Nullable backend fields are `T | null` (not optional) unless the API can omit
 * them entirely.
 */

/* ------------------------------------------------------------------ enums */

/** Dentist's verdict on one AI detection (Step 3). */
export type ReviewStatus = "pending" | "confirmed" | "rejected" | "modified";

/** Outcome of checking one drug against one patient. */
export type SafetyStatus = "clear" | "warning" | "contraindicated";

/** Severity of a single structured warning. */
export type Severity = "info" | "warning" | "contraindicated";

/** Why a drug is being proposed (the engine never guesses; the dentist supplies the indication). */
export type IndicationType = "active_infection" | "pre_procedure_prophylaxis" | "pain_management";

/** Dentist's verdict on one proposed prescription (Step 5). */
export type DentistStatus = "proposed" | "accepted" | "modified" | "rejected";

/** Lifecycle of a treatment proposal (Step 5). */
export type TreatmentStatus =
  | "proposed"
  | "confirmed"
  | "modified"
  | "in_progress"
  | "completed"
  | "cancelled";

/** Condition-specific management paths produced by the recommendation engine (Step 4). */
export type TreatmentCategory =
  | "restorative"
  | "endodontic"
  | "surgical_extraction"
  | "periodontal"
  | "preventive"
  | "monitoring";

/** Scan lifecycle: `failed` means the ML service did not answer and the scan is kept for retry. */
export type ScanStatus = "uploaded" | "processing" | "analyzed" | "reviewed" | "failed";

/** Where in the clinical loop a correction happened (Step 6 ledger). */
export type FeedbackStage = "finding_detection" | "treatment_recommendation" | "prescription_dosing";

/** What kind of departure from the AI the dentist recorded (Step 6 ledger). */
export type CorrectionType =
  | "false_positive"
  | "false_negative"
  | "misclassification"
  | "drug_override"
  | "dosage_adjusted"
  | "custom_note";

export type Gender = "male" | "female" | "other";

/* ------------------------------------------------------------- constants */

/** Pathology classes the DENTEX pipeline emits (docs/CLINICAL_GUIDELINES.md §1). */
export const DISEASES = ["Caries", "Deep Caries", "Periapical Lesion", "Impacted"] as const;
export type Disease = (typeof DISEASES)[number];

/** Same order as `TreatmentCategory`; the select lists render these through `humanize()`. */
export const TREATMENT_CATEGORIES: TreatmentCategory[] = [
  "restorative",
  "endodontic",
  "surgical_extraction",
  "periodontal",
  "preventive",
  "monitoring",
];

/* -------------------------------------------------------------- entities */

export interface Patient {
  id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: Gender;
  phone: string | null;
  email: string | null;
  address: string | null;
  /** Required for pediatric dosing. */
  weight_kg: number | null;
  allergies: string[];
  current_medications: string[];
  medical_conditions: string[];
  notes: string | null;
  dentist_id?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface PatientCreate {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: Gender;
  weight_kg?: number | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  allergies: string[];
  current_medications: string[];
  medical_conditions: string[];
  notes?: string | null;
}

export type PatientUpdate = Partial<PatientCreate>;

export interface PatientListResponse {
  patients: Patient[];
  total: number;
  page: number;
  page_size: number;
}

export interface Scan {
  id: string;
  patient_id: string;
  scan_type: string;
  /** Short-lived signed URL into the private `xray-scans` bucket. */
  image_url: string;
  storage_path: string | null;
  status: ScanStatus;
  image_width: number | null;
  image_height: number | null;
  notes: string | null;
  /** Free-text report written by the ML service; always pending dentist validation. */
  ai_report: string | null;
  created_at: string;
  updated_at?: string;
}

export interface ScanListResponse {
  scans: Scan[];
  total: number;
  page: number;
  page_size: number;
}

export interface ScanAnalysisResponse {
  scan_id: string;
  status: ScanStatus;
  ai_report: string | null;
  findings_count: number;
}

export interface Finding {
  id: string;
  scan_id: string;
  patient_id: string;
  quadrant: number;
  tooth_id: number;
  /** FDI notation, e.g. "36". */
  tooth_fdi: string;
  disease: string;
  disease_confidence: number;
  tooth_confidence?: number | null;
  association_confidence?: number | null;
  /** Bounding box in image pixels: [x1, y1, x2, y2]. */
  box: number[];
  review_status: ReviewStatus;
  /** The dentist's relabel; when set it wins over `disease`. */
  confirmed_disease: string | null;
  dentist_notes: string | null;
  reviewed_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface FindingListResponse {
  findings: Finding[];
  total: number;
}

export interface SafetyWarning {
  /** Stable machine-readable code, e.g. ALLERGY_PENICILLIN. */
  code: string;
  /** Rule register ID from docs/CLINICAL_GUIDELINES.md §4, e.g. R-01. */
  rule_id: string;
  severity: Severity;
  drug: string;
  message: string;
  /** Published source behind the rule, or the PROJECT marker. */
  source: string;
}

export interface SafetyCheckResult {
  drug_name: string;
  indication_type: IndicationType;
  status: SafetyStatus;
  warnings: SafetyWarning[];
  disclaimer?: string;
}

export interface Treatment {
  id: string;
  patient_id: string;
  scan_id: string;
  finding_id: string | null;
  treatment_category: TreatmentCategory;
  description: string;
  requires_prescription: boolean;
  clinical_justification: string | null;
  status: TreatmentStatus;
  dentist_notes: string | null;
  confirmed_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface TreatmentWithPrescriptions extends Treatment {
  prescriptions: Prescription[];
}

export interface TreatmentListResponse {
  treatments: TreatmentWithPrescriptions[];
  total: number;
  disclaimer?: string;
}

export interface Prescription {
  id: string;
  treatment_id: string;
  patient_id: string;
  finding_id: string | null;
  drug_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  indication_type: IndicationType;
  instructions: string | null;
  contraindication_status: SafetyStatus;
  contraindication_warnings: SafetyWarning[];
  dentist_status: DentistStatus;
  dentist_override_reason: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface PlanAlert {
  code: string;
  message: string;
}

export interface TreatmentPlan {
  treatment: Treatment;
  prescriptions: Prescription[];
  alerts: PlanAlert[];
}

export interface RecommendationResponse {
  scan_id: string;
  plans: TreatmentPlan[];
  /** Findings left untouched because the dentist already acted on their treatment. */
  skipped_finding_ids: string[];
  disclaimer?: string;
}

export interface FeedbackLog {
  id: string;
  scan_id: string;
  stage: FeedbackStage;
  correction_type: CorrectionType;
  ai_original_data: Record<string, unknown>;
  dentist_corrected_data: Record<string, unknown>;
  notes: string | null;
  created_at: string;
  dentist_id?: string | null;
}

export interface FeedbackListResponse {
  logs: FeedbackLog[];
  total: number;
}

export interface FeedbackSummary {
  total: number;
  by_stage: Record<string, number>;
  by_correction_type: Record<string, number>;
}

/* ------------------------------------------------------------- payloads */

/** Facts the X-ray cannot show; drugs are only proposed when the dentist reports them. */
export interface ClinicalContext {
  active_infection: boolean;
  pain: boolean;
}

export interface FindingReviewInput {
  finding_id: string;
  review_status: "confirmed" | "rejected" | "modified";
  /** Required when `review_status` is "modified". */
  confirmed_disease?: string;
  dentist_notes?: string;
}

export interface MissedFindingReportInput {
  scan_id: string;
  tooth_fdi: string;
  disease: string;
  notes?: string;
}

export interface TreatmentCreateInput {
  scan_id: string;
  finding_id?: string;
  treatment_category: TreatmentCategory;
  description: string;
  clinical_justification?: string;
  dentist_notes?: string;
}

export interface TreatmentDecisionInput {
  decision: "confirmed" | "modified" | "cancelled";
  /** Only allowed with `decision: "modified"`. */
  treatment_category?: TreatmentCategory;
  /** Only allowed with `decision: "modified"`. */
  description?: string;
  dentist_notes?: string;
}

export interface PrescriptionCreateInput {
  treatment_id: string;
  drug_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  indication_type: IndicationType;
  instructions?: string;
}

export interface PrescriptionCheckInput {
  patient_id: string;
  drug_name: string;
  indication_type: IndicationType;
  dosage?: string;
  /** Enables the daily-dose check, e.g. "every 6 hours". */
  frequency?: string;
}

export interface PrescriptionDecisionInput {
  decision: "accepted" | "modified" | "rejected";
  /** Edited fields are only allowed with `decision: "modified"`. */
  drug_name?: string;
  dosage?: string;
  frequency?: string;
  duration?: string;
  instructions?: string;
  /** Required to accept a prescription whose status is "warning". */
  acknowledge_warnings?: boolean;
  /** Required to accept a prescription whose status is "contraindicated". */
  override_reason?: string;
}
