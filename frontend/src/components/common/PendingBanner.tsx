/** Always-visible statement of the product's positioning (ARCHITECTURE.md §1, TEAM_WORKFLOW.md §3.3). */
export function PendingBanner() {
  return (
    <div className="bg-brand-900 px-4 py-1.5 text-center text-xs text-brand-100">
      <strong>Assistive tool.</strong> AI findings and suggestions are pending dentist validation. Nothing is a diagnosis or
      prescription until the treating dentist confirms it.
    </div>
  );
}
