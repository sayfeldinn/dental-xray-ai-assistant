import type { DentistStatus, ReviewStatus, SafetyStatus, Severity, TreatmentStatus } from "../../lib/types";
import { Badge, type Tone } from "./ui";

const REVIEW: Record<ReviewStatus, [Tone, string]> = {
  pending: ["amber", "Pending dentist validation"],
  confirmed: ["emerald", "Confirmed"],
  modified: ["sky", "Modified by dentist"],
  rejected: ["slate", "Rejected"],
};
export const ReviewBadge = ({ status }: { status: ReviewStatus }) => <Badge tone={REVIEW[status][0]}>{REVIEW[status][1]}</Badge>;

const SAFETY: Record<SafetyStatus, [Tone, string]> = {
  clear: ["emerald", "No safety flags"],
  warning: ["amber", "Warning"],
  contraindicated: ["rose", "Contraindicated"],
};
export const SafetyBadge = ({ status }: { status: SafetyStatus }) => <Badge tone={SAFETY[status][0]}>{SAFETY[status][1]}</Badge>;

const SEVERITY: Record<Severity, Tone> = { info: "sky", warning: "amber", contraindicated: "rose" };
export const SeverityBadge = ({ severity }: { severity: Severity }) => <Badge tone={SEVERITY[severity]}>{severity}</Badge>;

const DECISION: Record<DentistStatus | TreatmentStatus, Tone> = {
  proposed: "amber", accepted: "emerald", confirmed: "emerald", modified: "sky", rejected: "slate",
  cancelled: "slate", in_progress: "violet", completed: "emerald",
};
export const DecisionBadge = ({ status }: { status: DentistStatus | TreatmentStatus }) => (
  <Badge tone={DECISION[status]}>{status === "proposed" ? "Proposed: pending dentist decision" : status.replace("_", " ")}</Badge>
);
