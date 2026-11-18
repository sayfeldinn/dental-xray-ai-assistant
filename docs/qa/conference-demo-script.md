# Conference demo script — local stack (IC-FTAI 2026)

**Goal:** a 2–3 minute live walkthrough (and a recorded backup) that shows the v3 loop,
the advisory separation, the threshold control and the provenance card. The talk is
3:00; the demo is a supporting segment, not a debugging session.

**Demo path:** local Supabase + local ML + local backend + local frontend. The public
Cloudflare Pages UI was unreachable (522/523) at writing; do not promise it.

---

## 1. Pre-flight (30 minutes before)

```bash
# terminal 1 — database
npx supabase start                       # API 127.0.0.1:54321

# terminal 2 — ML
cd dentex_week3/api && ./start.sh        # ML :8001

# terminal 3 — backend
cd backend && ./start.sh                 # API :8000

# terminal 4 — frontend
cd frontend && npm run dev -- --host 0.0.0.0 --port 8080

# terminal 5 — pre-flight (from the repo root)
./scripts/demo_check.sh                  # all green
```

Open `http://localhost:8080/login` in a clean browser window (no devtools, no local URL
in the address bar during the recording if possible). Log in with the local QA dentist
`qa.e2e@dentalai.local`; the password is in the team's local run notes, **not** in this
public repo. Do not show the password on screen.

**Fixtures (local DB):**

| Item | ID / value |
| --- | --- |
| QA patient | `715a685f-8ed6-48dd-a54d-9c735eef6875` |
| 0.20 scan (9 findings, 6 missing boxes, 19 advisory) | `e6b213ba-f1ca-4b60-87de-a127e7c14507` |
| 0.50 scan (8 findings) | `5f25a5ba-542e-4910-bf5b-7c88b7c824b2` |
| Direct scan URL | `http://localhost:8080/scans/e6b213ba-f1ca-4b60-87de-a127e7c14507` |

If the local DB was reset, re-run `python scripts/e2e_clinician_flow.py` (see
`docs/qa/e2e-clinician-flow.md`) or re-upload the DENTEX `train_12.png` at 0.20 and 0.50.

---

## 2. Two-and-a-half-minute walkthrough

### 0:00–0:15 — Login and patient

- Open the login page; sign in as the QA dentist.
- Patients list → open the QA patient (or use the direct patient URL).
- Say: "Every dentist sees only their own patients; the AI never writes without a
  review."

### 0:15–0:50 — The scan and the boxes

- Open scan `e6b213ba…` (0.20 run).
- Point at the colour legend: pending / confirmed / modified / rejected / missing
  (dashed).
- Wheel-zoom once, drag-pan once, reset. Click a box → the matching card scrolls into
  view.
- Say: "The tooth detector labels FDI teeth directly; the disease detector finds four
  lesion classes; the association assigns each lesion to a tooth."

### 0:50–1:15 — Advisory separation

- Expand **Advisory AI signals**: 6 missing teeth + 19 findings.
- Point at the "not in the clinical report" label and the dashed missing boxes.
- Say: "These layers are advisory. They never enter the report or the treatment plan;
  the dentist confirms every clinical finding."

### 1:15–1:35 — Threshold

- Point at the **Threshold** select (0.20 / 0.30 / 0.50) and the **Re-run AI analysis**
  button. Explain: 0.20 is recall-oriented (9 findings); 0.50 is precision-oriented
  (8 findings).
- For the recorded video, cut to the 0.50 scan `5f25a5ba…` to show the comparison without
  mutating the 0.20 fixture. Live, you can re-run a fresh upload at 0.50.
- Say: "Higher threshold trades recall for precision; the dentist chooses the operating
  point."

### 1:35–2:05 — Review and safety

- Confirm the highest-confidence periapical finding; show the pending count drop and the
  re-run control disappear (the audit gate).
- Go to **2. Treatment plan**; show the confirmed-finding gate and the proposal.
- On the QA patient (penicillin allergy), show the **clindamycin** alternative and the
  visible warning / acknowledgement requirement.
- Say: "Caries alone never gets antibiotics. An active infection can get amoxicillin;
  a penicillin allergy switches to clindamycin with a warning the dentist must
  acknowledge."

### 2:05–2:30 — Feedback and provenance

- Reject one low-confidence finding; open **Feedback log**; show the ledger row.
- Expand **Model provenance**: pipeline v3, tooth/disease/findings weights,
  missing-teeth gate.
- Say: "Every correction is logged for future retraining, but the model is frozen this
  week. Every run stores its weights and threshold for audit."

### 2:30–2:40 — Close

- Return to the scan or the landing page.
- Say: "This is a research prototype: no reader study, no clinic pilot. The next step is
  a supervised clinician study."

---

## 3. Recording voice-over (optional, 2:30)

> "This is the local DentalAI stack. I sign in as a dentist; I only see my own patients.
> Here is a panoramic X-ray analysed by v3. The tooth detector labels FDI teeth, the
> disease detector finds four lesion classes, and the association assigns each lesion to
> a tooth. The dashed blue boxes and the advisory panel are missing teeth and the
> 11-class findings model; they are clearly labelled and never enter the report.
> The threshold control changes the operating point: 0.20 is recall-oriented, 0.50 is
> precision-oriented. I confirm a periapical finding; only confirmed findings can be
> planned. The patient has a penicillin allergy, so the system proposes clindamycin with
> a warning I must acknowledge. Rejecting a finding writes a feedback row; the model is
> not retrained this week. The provenance card shows the exact pipeline, weights and
> gate stored with this run. This is a research prototype — no reader study, no clinic
> pilot."

---

## 4. Fallback

| Failure | Action |
| --- | --- |
| Any service is down | Stop debugging after 30 seconds; play the recorded video. |
| Supabase/DB reset | Use the video/screenshots; re-run the e2e script only after the talk. |
| Projector/HDMI | Use the PDF/backup laptop; the video is on the USB. |
| No internet | Everything is local; the video and PDF are offline. |
| A judge asks for a number | Open the backup slide; if not in `FACTS.md`, say "we have not measured that." |

**Do not** delete the QA scan, re-run the 0.20 fixture at 0.50 during the live demo, or
show the local Supabase keys/token. **Do not** claim the public site is live.

---

## 5. Screenshot shot list (for the deck)

Capture at 1920×1080, browser zoom 100%, no devtools:

1. Scan page, 0.20 run, boxes + legend + right-hand findings list.
2. Advisory panel expanded (missing teeth + findings model).
3. Provenance card expanded.
4. Threshold select + re-run control (before any review).
5. Treatment plan with the clindamycin warning.
6. Feedback log with one correction.
7. Landing page (optional, for the title).

Store them in `submission/assets/` with clear names (`screen_v3_*.png`) and update the
deck; the old `screen_*.png` files are v2.
