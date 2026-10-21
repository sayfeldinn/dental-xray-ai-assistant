/**
 * DentalAI decision gates — the single client-side mirror of a backend rule.
 *
 * The backend is the only place where clinical rules live (docs/AGENT_ONBOARDING.md, rule 3).
 * This file mirrors exactly one of them, **CLINICAL_GUIDELINES.md §5.13**:
 *
 *   "Dentist decisions are re-checked against the *current* patient record at decision time.
 *    `warning` needs `acknowledge_warnings`; `contraindicated` needs a written `override_reason`."
 *
 * It exists so the dentist sees *why* a button is disabled instead of getting a 422 after clicking.
 * The server re-checks the same conditions (`POST /prescriptions/{id}/decision`) and always wins:
 * if the two ever disagree, the backend's answer is the correct one.
 */

import type { SafetyStatus, SafetyWarning } from "./types";

/** What the dentist must supply before a prescription can be submitted. */
export type GateRequirement = "acknowledge" | "override";

/** CLINICAL_GUIDELINES.md §5.13: flagged drugs cannot be silently accepted. */
export function requirementFor(status: SafetyStatus): GateRequirement | null {
  if (status === "contraindicated") return "override";
  if (status === "warning") return "acknowledge";
  return null;
}

/** True when the requirement (if any) has been satisfied. Rejection never needs anything. */
export function canSubmit(requirement: GateRequirement | null, acknowledged: boolean, overrideReason: string): boolean {
  if (requirement === "override") return overrideReason.trim().length > 0;
  if (requirement === "acknowledge") return acknowledged;
  return true;
}

const RANK: Record<SafetyStatus, number> = { clear: 0, warning: 1, contraindicated: 2 };

/**
 * Status to gate the decision on after the dentist edits a proposal in the "modify" mode.
 *
 * The live check (`POST /prescriptions/check`) describes the *new* drug; the warnings stored on the
 * prescription describe the drug that was proposed. If the dentist swapped the drug, the stored
 * warnings no longer apply and the live result stands. If the drug is unchanged, the stricter of
 * the two wins, so an edit can never loosen a flag that is already on the record.
 */
export function statusAfterModify(
  liveStatus: SafetyStatus,
  originalDrug: string,
  newDrug: string,
  storedWarnings: SafetyWarning[],
): SafetyStatus {
  const sameDrug = originalDrug.trim().toLowerCase() === newDrug.trim().toLowerCase();
  if (!sameDrug) return liveStatus;

  const storedStatus = storedWarnings.reduce<SafetyStatus>((worst, item) => {
    // Severity includes "info" (counselling only): info never gates a decision.
    const status: SafetyStatus | null =
      item.severity === "contraindicated" ? "contraindicated" : item.severity === "warning" ? "warning" : null;
    if (!status) return worst;
    return RANK[status] > RANK[worst] ? status : worst;
  }, "clear");
  return RANK[liveStatus] >= RANK[storedStatus] ? liveStatus : storedStatus;
}
