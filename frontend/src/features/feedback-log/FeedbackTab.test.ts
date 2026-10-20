import { describeChange } from "./FeedbackTab";
import type { FeedbackLog } from "../../lib/types";

const log = (ai: Record<string, unknown>, dentist: Record<string, unknown>): FeedbackLog => ({
  id: "l", scan_id: "s", stage: "finding_detection", correction_type: "misclassification", ai_original_data: ai,
  dentist_corrected_data: dentist, notes: null, created_at: "2026-10-20T09:00:00Z",
});

test("only differing fields are shown", () => {
  expect(describeChange(log({ tooth_fdi: "36", disease: "Caries", disease_confidence: 0.9 }, { tooth_fdi: "36", disease: "Deep Caries" })))
    .toEqual([{ field: "Disease", ai: "Caries", dentist: "Deep Caries" }]);
});

test("the decision is shown only for a rejection", () => {
  const rx = (decision: string) => log({ drug_name: "Ibuprofen", dosage: "400 mg" }, { drug_name: "Ibuprofen", dosage: "200 mg", decision });
  expect(describeChange(rx("modified")).map((c) => c.field)).toEqual(["Dosage"]);
  expect(describeChange(rx("rejected")).map((c) => c.field)).toEqual(["Dosage", "Decision"]);
});

test("a rejection shows the disease removed", () => {
  expect(describeChange(log({ tooth_fdi: "36", disease: "Caries" }, { tooth_fdi: "36", disease: null, review_status: "rejected" })))
    .toEqual([{ field: "Disease", ai: "Caries", dentist: "—" }]);
});
