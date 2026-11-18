# IC-FTAI 2026 — conference readiness checklist (18–26 Nov 2026)

**Rule for this week:** no model training, no pipeline changes, no merge to `main`, no
cloud redeploy experiments. Freeze v3 and make the materials match it. If a change is not
needed for the demo, it does not go in.

**Current state (2026-11-18):** v3 frozen; `develop` behind `main`; conference branch
`feature/conference-v3` based on `main` `c78a525`. Tests: **176 backend / 29 frontend**.
The binary deck/summary are still v2 and must be updated from `DECK_V3_REWRITE.md`.

---

## 1. Must-fix before submission

| # | Item | Owner | Done |
| ---: | --- | --- | :---: |
| 1 | Fill the three missing names/roles on the title slide and in `CITATION.cff` | Team Lead | ☐ |
| 2 | Apply `DECK_V3_REWRITE.md` to the PPTX: numbers, architecture, advisory, tests, team | Deck owner | ☐ |
| 3 | Replace the v2 screenshots with current UI (advisory panel, dashed missing boxes, threshold, provenance, zoom) | Frontend | ☐ |
| 4 | Replace architecture/loop diagrams; remove the v1 23-image charts | ML/design | ☐ |
| 5 | Rewrite the one-page summary from the abstract in `DECK_V3_REWRITE.md` §4 | Summary owner | ☐ |
| 6 | Run the claim→source check in `VERIFICATION.md` against the final PDF | ML + Team Lead | ☐ |
| 7 | Remove every "UNVERIFIED" highlight and competitor "verify" cell | Deck owner | ☐ |
| 8 | Confirm the test counts on the slide are **176/29** (not 171/25/14) | ML | ☐ |
| 9 | Add `LICENSE`, `NOTICE`, `CITATION.cff`, `MODEL_CARD.md` to the repo (done in this branch) | Repo owner | ✅ |
| 10 | Verify `weights-v3` release download and `start.sh` on a clean checkout | ML/QA | ☐ |
| 11 | Record the 2–3 minute demo video and store it offline | Demo driver | ☐ |
| 12 | Print the one-page summary and a Q&A card; pack the USB | Team Lead | ☐ |

---

## 2. Day-by-day plan

### Wed 18 Nov — freeze content

- [ ] Team call: confirm the three names/roles; confirm who presents, who drives, who
      keeps time, who handles Q&A.
- [ ] Apply all text changes to the PPTX from `DECK_V3_REWRITE.md` (slides 1–7 + B1–B10).
- [ ] Replace the summary text with the §4 abstract; keep it to one A4 page.
- [ ] Delete the old numbers everywhere: 97.54, 76.23, 75.41, 23 images, 122 detections,
      171, 25, 14, 196, "coordinator", "random forest".
- [ ] Run `grep -R` on the final text for those strings; zero hits.

### Thu 19 Nov — visuals and PDF

- [ ] Replace the architecture/loop diagrams (slides 3–4) and the per-class AP chart.
- [ ] Capture current UI screenshots at 1920×1080 (QA scan `e6b213ba…`).
- [ ] Replace the title/hero image with the v3 UI.
- [ ] Export PDF; check fonts, image resolution, no local URL/token, no cut-off text.
- [ ] Run the `VERIFICATION.md` claim table against the PDF; fix every mismatch.
- [ ] Check the constraints: 7 main slides + divider, abstract ≤250 words, 3:00 script.

### Fri 20 Nov — demo and video

- [ ] Start the local stack: Supabase, ML `:8001`, backend `:8000`, frontend `:8080`.
- [ ] Run `./scripts/demo_check.sh`; fix any red item.
- [ ] Walk the full loop once: login → patient → scan → review → threshold → treatment →
      feedback → provenance.
- [ ] Record a 2–3 minute screen video with voice-over; show the advisory panel and the
      missing-tooth dashed boxes.
- [ ] Save the video in two places (laptop + USB/cloud) and test playback offline.
- [ ] Capture a fallback set of screenshots for every demo step.

### Sat 21 Nov — rehearse and drill

- [ ] Rehearse the 3:00 script five times; record one run; cut to time.
- [ ] Q&A drill: 25 questions from `QA_Prep.md`; each answer ≤20 seconds.
- [ ] Rehearse the fallback: "the live site is not the demo; here is the local run/video."
- [ ] Print the one-page summary, Q&A card, and a one-page demo runbook.
- [ ] Pack: laptop, charger, HDMI/USB-C adapter, clicker, USB with video/screenshots,
      phone hotspot (not relied on).
- [ ] Freeze the repo: no code changes after this point unless the demo is broken.

### Sun 22 Nov — travel and final check

- [ ] Final `demo_check.sh` on the presentation laptop.
- [ ] Open the PDF, PPTX and video once on the presentation laptop.
- [ ] Confirm the conference upload deadline and file naming.
- [ ] Sleep. Do not train a model.

### 23–26 Nov — conference

- [ ] Arrive early; test the projector and audio.
- [ ] Start the local stack 30 minutes before the session (or use the video).
- [ ] Present with the 3:00 script; keep the backup slides for Q&A.
- [ ] After the talk: collect feedback, note the judges' questions, and log them for the
      next iteration.

---

## 3. Demo-day runbook (local)

| Step | Action | Expected |
| ---: | --- | --- |
| 1 | `npx supabase start` (if not running) | API `127.0.0.1:54321` 200 |
| 2 | `cd dentex_week3/api && ./start.sh` | `:8001` models loaded |
| 3 | `cd backend && ./start.sh` | `:8000/health` 200 |
| 4 | `cd frontend && npm run dev -- --host 0.0.0.0 --port 8080` | `:8080` 200 |
| 5 | `./scripts/demo_check.sh` | all green |
| 6 | Log in with the QA dentist | patient list |
| 7 | Open the QA patient/scan | v3 boxes + advisory panel |
| 8 | Show threshold 0.20 → 0.50 re-run | fewer, higher-confidence findings |
| 9 | Confirm/modify/reject a finding | sticky progress; gate |
| 10 | Generate plan; show the three branches | no drug / amoxicillin / clindamycin warning |
| 11 | Submit feedback; open provenance | logged; model version/threshold |

**Fallback:** if any service fails, switch to the recorded video, then the screenshot
set. Do not debug live for more than 30 seconds. The talk is the deliverable, not the
laptop.

---

## 4. Risk register

| Risk | Likelihood | Impact | Mitigation |
| --- | :---: | :---: | --- |
| Live cloud site down (522/523) | high | high | Do not use it; local stack + video |
| Local Docker/Supabase fails | medium | high | Video + screenshots; pre-start 30 min early |
| Projector resolution/HDMI | medium | medium | Adapter, 16:9 PDF, test early |
| Overrun 3:00 | medium | medium | Rehearse 5×; cut slide 5 detail |
| Judge asks for a number not in FACTS | medium | medium | Say "we have not measured that"; offer the closest verified number |
| Judge challenges caries/domain gap | high | low | Use B4/B5; lead with the limitation |
| Team name missing | high | medium | Fill before printing; role-only if not confirmed |
| Old v2 numbers in the deck | high | high | Run the forbidden-string grep; `VERIFICATION.md` |
| No internet at venue | medium | medium | Offline video, local stack, PDF, USB |

---

## 5. Do-not-say list

- "97.5% accuracy", "76.2% tooth", "75.4% joint" (v1, 23 images).
- "Coordinator + random forest" (v1).
- "No held-out mAP" (false since v3).
- "The model improves with feedback" (no retraining).
- "Clinically validated" / "clinician-reviewed rules" (no reader study/pilot).
- "Diagnoses" / "replaces the dentist" / "autonomous".
- "FDA/CE cleared" / "medical device".
- "Works on any X-ray" / "DICOM/PACS" (not implemented).
- "State-of-the-art" (no external SOTA comparison).
- "The live site is available" (it was down at writing).

---

## 6. Definition of done

- [ ] The final PDF has 7 main slides + backup, every number traceable to `FACTS.md`.
- [ ] The one-page summary is 1 page, abstract ≤250 words, same numbers.
- [ ] The title slide has the confirmed team names/roles.
- [ ] The demo runs locally end-to-end, and the video plays offline.
- [ ] The 3:00 script is rehearsed to time; Q&A answers are ≤20 seconds.
- [ ] The repo has LICENSE, NOTICE, CITATION, MODEL_CARD, and the v3 docs.
- [ ] No old v1/v2 numbers, no "UNVERIFIED", no competitor "verify" cells.
- [ ] The team agrees: **ship the honest v3 story, not the old v2 numbers.**
