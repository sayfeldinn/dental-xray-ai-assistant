/**
 * DentalAI display helpers.
 *
 * Pure functions only: no React, no network. Everything here is about turning API values into
 * something a dentist can read at a glance.
 */

/**
 * Parse an ISO date ("1990-05-12" or a full timestamp) as a *local* calendar date.
 * `new Date("1990-05-12")` is UTC midnight, which can land on the 11th in negative offsets and
 * make a patient a year younger, so the date part is read by hand.
 */
function localDate(value: string | Date): Date | null {
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (m) return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

/** Whole years between the date of birth and today, for the "34 years · female · 62 kg" line. */
export function ageFrom(dateOfBirth: string | Date): number {
  const born = localDate(dateOfBirth);
  if (!born) return 0;
  const today = new Date();
  let age = today.getFullYear() - born.getFullYear();
  const month = today.getMonth() - born.getMonth();
  if (month < 0 || (month === 0 && today.getDate() < born.getDate())) age -= 1;
  return Math.max(age, 0);
}

const WHEN = new Intl.DateTimeFormat(undefined, {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

/** "20 Oct 2026, 09:00" — used for scans, feedback rows and anything time-ordered. */
export function dateTime(value: string | Date): string {
  const d = value instanceof Date ? value : new Date(value);
  return Number.isNaN(d.getTime()) ? "" : WHEN.format(d);
}

/** "active_infection" -> "Active Infection". Never rewrites the words themselves. */
export function humanize(value: string): string {
  return value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/** 0.87 -> "87%". The API returns confidences in 0..1. */
export function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

const POSITIONS = [
  "", // index 0 unused: FDI tooth positions are 1-8
  "central incisor",
  "lateral incisor",
  "canine",
  "first premolar",
  "second premolar",
  "first molar",
  "second molar",
  "third molar",
];

const QUADRANTS = ["", "upper right", "upper left", "lower left", "lower right"];

/** "36" -> "lower left first molar". Returns "" for anything that is not a valid FDI code. */
export function toothName(toothFdi: string): string {
  const quadrant = Number(toothFdi.charAt(0));
  const position = Number(toothFdi.charAt(1));
  if (!QUADRANTS[quadrant] || !POSITIONS[position]) return "";
  return `${QUADRANTS[quadrant]} ${POSITIONS[position]}`;
}

/** "penicillin,  aspirin ," -> ["penicillin", "aspirin"]. Backs the comma-separated history fields. */
export function splitList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
