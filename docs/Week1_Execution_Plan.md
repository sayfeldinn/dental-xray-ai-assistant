# DentalAI — Week 1 Execution Plan

*Team Roles, Day-by-Day Tasks & Existing Tools to Reuse*

**Team of 5 — One-Month Competition Build, Week 1 of 4**

*This plan assigns every team member concrete daily tasks for Week 1, lists every existing model, dataset, and tool the team will reuse instead of rebuilding, and defines exactly what must exist by Friday.*

## Contents

1. [Week 1 Objective](#1-week-1-objective)
2. [Team Roles for Week 1](#2-team-roles-for-week-1)
3. [Existing Tools & Models We Are Reusing (Not Building)](#3-existing-tools--models-we-are-reusing-not-building)
4. [Day-by-Day Plan](#4-day-by-day-plan)
5. [Dentist Meeting — Preparation Detail](#5-dentist-meeting--preparation-detail)
6. [End-of-Week 1 Deliverables Checklist](#6-end-of-week-1-deliverables-checklist)
7. [Risks & Blockers to Watch](#7-risks--blockers-to-watch)
8. [What NOT To Do This Week](#8-what-not-to-do-this-week)

## 1. Week 1 Objective

**By end of day Friday, the following must all be true:**

- The dentist meeting has happened, and the finding-to-treatment table and drug list are corrected and documented (no longer drafts).
- DENTEX, Tufts, and Roboflow datasets are downloaded, merged, and converted into one training-ready format.
- A first model fine-tuning run has started — it does not need to be accurate yet, it needs to exist.
- The patient record schema is implemented, including every field the contraindication check needs.
- The recommendation engine's rules are coded from the validated table, even if only stub-tested.
- Review-screen and confirmation-screen UI shells exist, wired to mock data.
- A set of synthetic patient profiles is drafted, covering all three demo branches (no-drug, drug-no-conflict, drug-with-conflict).

*Everything in this plan assumes the team is not building anything already solved elsewhere — Section 3 lists exactly what to reuse.*

## 2. Team Roles for Week 1

| Role | Week 1 Focus |
| --- | --- |
| Person A — ML Engineer | Acquire and prepare all training data; select and start fine-tuning the detection model. |
| Person B — Backend Engineer | Finalize system architecture; build the patient record schema; start the recommendation engine skeleton. |
| Person C — Frontend Engineer | Set up the frontend stack; build wireframes/shells for the review and confirmation screens. |
| Person D — Integration/QA Engineer | Set up the shared repo and project board; design synthetic patient profiles and contraindication test cases. |
| Person E — Team Lead / Clinical Liaison | Schedule and run the dentist meeting; document validated outputs; coordinate the team daily. |

*Swap in real names once assigned. Roles carry over unchanged into Weeks 2–4 (see the main project documentation, Section 9.3).*

## 3. Existing Tools & Models We Are Reusing (Not Building)

**This is the most important section for moving fast. Every row below is something the team should install, download, or call — not write from scratch.**

| Need | Use This | Why Not Build It Ourselves |
| --- | --- | --- |
| Object detection architecture | Pretrained YOLOv8/v9/v11 (Ultralytics), fine-tuned | Already shown to work on dental panoramic X-rays as a baseline in published dental datasets; fine-tuning takes hours, not weeks |
| DENTEX data loading & format conversion | Official DENTEX GitHub repo (ibrahimethemhamamci/dentex) — includes winning-participant code that converts the dataset to COCO and YOLO formats | The challenge organizers and top entrants already solved this exact preprocessing problem |
| DENTEX dataset access | Hugging Face DENTEX dataset page (train, validation, and test sets are all public) | No scraping, no approval process, no waiting |
| Merging DENTEX + Tufts + Roboflow data, augmentation | Roboflow platform (free tier) plus its ready-made YOLO training notebooks | Handles format conversion and augmentation across datasets in one place instead of custom scripts |
| Patient record storage + authentication | Supabase (managed Postgres + Auth + Storage, free tier) | Avoids building custom database and login infrastructure in week one |
| Backend API layer | FastAPI (Python) | Same language as the ML model; minimal glue code between inference and API |
| Bounding-box overlay on the X-ray image | Existing open-source React canvas/annotation components | An image annotation UI is a solved problem; do not build one from scratch |
| Drug name standardization | RxNorm / RxNav lookup API (name and ingredient lookup only) | Free, NIH-maintained standard vocabulary for the six drugs in scope |

> **⚠ Do not use the RxNav drug-drug interaction API.** It was retired by the NLM and now returns HTTP 404 — this was confirmed directly, including recent reports from other developers hitting the same dead endpoint. With only five or six drugs in scope, hand-curate the interaction/contraindication table with the partner dentist instead (Section 5) — it will be more reliable than a live API call for this narrow a list.

*Not relevant to Week 1, but worth knowing for the future roadmap: if a partner clinic ever has a CBCT machine, an existing free tool called OraSeg already does one-click 3D tooth/jaw segmentation (Dice score 0.83) — reference it rather than training a new 3D model, even later.*

## 4. Day-by-Day Plan

### Day 1 (Monday)

- Team Lead: make the dentist meeting the #1 priority today — confirm a date (target Day 2 or 3), send the question list prepared earlier, confirm who from the team attends.
- ML Engineer: confirm Hugging Face access to the full DENTEX dataset; clone the official DENTEX repo; read the winning-participant preprocessing code.
- Backend Engineer: set up the repo structure; lock the stack (FastAPI + Supabase); draft patient record schema v1 (patient, scan, finding, confirmation, recommended vs. confirmed treatment).
- Frontend Engineer: set up the React project and component library; sketch the review-screen wireframe (scan + bounding-box overlay + confirm/reject controls).
- Integration/QA Engineer: set up the shared repo, branching strategy, and project board with every task in this document as a ticket.

### Day 2 (Tuesday)

- Dentist meeting happens if scheduled today — Team Lead runs it using the prepared question list; take detailed notes on the finding-to-treatment table and drug list.
- ML Engineer: begin converting DENTEX to YOLO format using the reused winning-solution scripts; download Tufts and the selected Roboflow dental sets.
- Backend Engineer: refine the patient record schema to include every field the dentist meeting surfaces (allergies, current medications, conditions); start the recommendation engine skeleton.
- Frontend Engineer: continue the review-screen wireframe; sketch the confirmation-screen wireframe including where treatment recommendations and warnings appear.
- Integration/QA Engineer: draft the first set of synthetic patient profiles (at least five, covering different ages, allergies, and current medications).

### Day 3 (Wednesday) — backup dentist-meeting day if needed

- Team Lead: finalize and document the validated finding-to-treatment table and drug list from the meeting; update the project documentation.
- ML Engineer: merge datasets in Roboflow; kick off the first YOLO fine-tuning run (let it run in the background over the following days).
- Backend Engineer: implement the recommendation engine rules using the validated table; build the contraindication-check logic skeleton.
- Frontend Engineer: build the review-screen UI shell with mock bounding boxes standing in for real model output.
- Integration/QA Engineer: write out the specific test cases for the contraindication logic (known allergy, known interaction, age/weight extremes) so Backend can test against them directly.

### Day 4 (Thursday)

- ML Engineer: check on the training run; adjust hyperparameters or augmentation if early results look off.
- Backend Engineer: connect the recommendation engine to the Supabase patient record; run it against Integration/QA's test cases and fix what fails.
- Frontend Engineer: build the confirmation-screen UI shell; wire it to mock recommendation output so it displays a proposed drug, dosage, and any warning.
- Integration/QA Engineer: start drafting the demo script outline covering the three required branches (no-drug, drug-no-conflict, drug-with-conflict); manually test the synthetic profiles against the current recommendation logic.
- Team Lead: sync with everyone individually, update the risk log (Section 7), prepare the Week 2 handoff.

### Day 5 (Friday)

- Whole team: informal end-of-week checkpoint — show the model running inference on one sample scan, the backend rules running against one synthetic profile, and the UI shells, even unpolished.
- Team Lead: record what was and wasn't finished against Section 6's checklist; confirm the Week 2 plan with the team.
- Everyone: log any open blockers before the weekend so Monday starts immediately, not with re-discovery.

*Weekend: optional buffer. Model training can keep running unattended without needing anyone at the keyboard; use the time only if someone is behind on their Friday deliverables.*

## 5. Dentist Meeting — Preparation Detail

**This meeting is the single most schedule-sensitive item in Week 1 — Backend and ML work from Day 2 onward depends on its answers.**

- Attendees: Team Lead (runs it) plus ideally the Backend Engineer (owns the patient-record fields the answers will shape).
- Materials to bring: the draft finding-to-treatment table, the draft six-drug list, and the full question set already prepared (imaging equipment, diagnosis-to-treatment mapping, drug/dosage practice, patient history habits, and awareness of existing tools like Diagnocat, Pearl, Atomica, or DentalRx).
- Required output by end of meeting: a corrected finding-to-treatment table, a corrected drug list, and a short hand-curated list of known contraindications/interactions for that specific drug list — this replaces the need for any external interaction API.
- If the meeting slips past Day 3: do not block the whole team on it. Backend and ML proceed with the current draft table clearly marked "unvalidated" and revise as soon as the meeting happens — better to build on a marked assumption than to stall the week.

## 6. End-of-Week 1 Deliverables Checklist

Status recorded by Lead + QA on 2026-09-27. Evidence and the full verification table are in
[#23](https://github.com/sayfeldinn/dental-xray-ai-assistant/issues/23). **3 met · 4 partial · 1 not met.**

- [ ] Dentist meeting completed; finding-to-treatment table and drug list corrected and documented
      — **not met.** #6 and #11 open with 0 comments since Day 1; everything in `docs/qa/` is `UNVALIDATED`.
- [~] DENTEX + Tufts + Roboflow datasets downloaded, merged, and converted to training format
      — **diverged.** DENTEX purged (box granularity), Roboflow unused. Actual set: **Tufts + Loki Silvres**.
      Awaiting Lead decision: accept the substitution or re-plan.
- [x] First model fine-tuning run started — two runs in `ml/Evaluation_Report.md`; checkpoint
      frozen as Release `v0.1-dental-yolov8s`. (#16)
- [~] Patient record schema implemented in Supabase with all contraindication-relevant fields
      — **partial.** Tables + JSONB fields in (#3, #8), but **`weight_kg` is not a column** and age
      is never computed → 3 of 9 rules have no data path (#33 gap A).
- [~] Recommendation engine skeleton coded from the validated table, stub-tested
      — **partial.** Engine built and tested (19 passed / 10 xfailed), but the table was **never
      validated** (#11).
- [x] Review-screen and confirmation-screen UI shells built against mock data — landed in PR #35
      (`Review.jsx`, `Treatments.jsx`, routed). Built against the real API rather than mock.
      Author marked the PR "testing in progress".
- [x] Five or more synthetic patient profiles drafted, covering all three demo branches —
      6 profiles (P-001…P-006), §3 branch matrix covers all three branches. (#10, PR #26)
- [~] Shared repo, branching strategy, and project board fully set up and in active use
      — **mostly.** Repo + CI + board live (25 issues, all with Status). Branching documented in
      `CONTRIBUTING.md` but **violated twice by direct pushes to `main`**; no branch protection on
      the free plan, so **CI is the only enforcement**.

> `[~]` = partial. The original plan used `- [ ]` only; partial states are recorded here rather
> than silently checking an item that is not finished.

## 7. Risks & Blockers to Watch

- Dentist meeting slips — mitigate by treating it as the #1 priority on Day 1 and having a backup async question list ready if an in-person meeting can't happen in time.
- Dataset access issues — should not occur, since DENTEX's full dataset is confirmed public on Hugging Face; verify this on Day 1 regardless.
- Stack decision paralysis — lock the stack choices on Day 1 (FastAPI + Supabase + React) and do not revisit them mid-week.
- Scope creep from excitement — see Section 8; the team will be tempted to "just quickly try" something out of scope. Don't.

## 8. What NOT To Do This Week

- ⚠ No 3D visualization work of any kind — cut from the build entirely (see main documentation, Section 6.1).
- ⚠ No attempt to integrate a drug-interaction API — the viable free one is discontinued; use the dentist-validated table instead.
- ⚠ No patient-app or NFC card work — future roadmap only.
- ⚠ No live model retraining infrastructure — correction logging only; retraining is a documented future step, not a Week 1 (or Week 4) build target.
- ⚠ No custom-built image annotation tool — reuse existing components (Section 3).
