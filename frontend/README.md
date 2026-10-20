# DentalAI Frontend

React 18 + Vite 6 + Tailwind 4 + TanStack Query, in TypeScript. The dentist's workstation for the 6-step loop.
It talks **only** to the FastAPI backend (`VITE_API_URL`, default `http://localhost:8000`) and holds no Supabase key.

```bash
npm install
npm run dev         # http://localhost:5173 (the backend's CORS list already allows it)
npm run typecheck
npm test            # vitest, 21 tests, no network
npm run build       # typecheck + production bundle in dist/
```

## Layout

```
src/
  lib/          api.ts (typed client, ApiError), types.ts (mirrors backend/app/domain), gate.ts, format.ts
  components/common/   ui.tsx (Button, Card, Badge, inputs), badges.tsx, PendingBanner.tsx
  features/
    patients/         list + search, new patient, patient page (safety history, scans, upload)
    scan-review/      ScanPage (tabs), XrayViewer (SVG boxes in image pixels), FindingCard, MissedFindingForm
    treatment-plan/   PlanTab (clinical context + generate), TreatmentCard, PrescriptionCard,
                      DecisionPanel (Step 5 gates), Manual treatment/prescription forms, useSafetyCheck
    feedback-log/     FeedbackTab (ledger table + summary)
```

## Rules

1. **No clinical logic here.** Safety status comes from the backend. While editing a drug, the UI calls `POST /prescriptions/check`.
   The single mirrored rule (the R-18 substitution notice survives a modify when the drug is unchanged) is documented in `src/lib/gate.ts`.
2. **The backend is the authority.** The UI disables Accept until the warning is acknowledged or a contraindication is justified,
   but the server re-checks and returns 422 if anything changed; the message is shown as is.
3. **Every AI output is visibly pending** until the dentist acts (banner, badges, "Proposed: pending dentist decision").
