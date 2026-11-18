# IC-FTAI 2026 — v3 deck rewrite (slide by slide)

Use this file to update `DentalAI_IC-FTAI2026_Presentation.pptx` (and the PDF) on the
existing template. **Do not submit the current binary deck**: it is built on v2 and
contains obsolete numbers, "UNVERIFIED" names and competitor "verify" cells. This
rewrite is the authoritative content; every number traces to `FACTS.md`.

**Format:** 16:9, 7 main slides + "Backup — Q&A" divider + 10 backup slides.
**Main script:** ~3:00 (see §2). **One-page summary:** use the abstract in §4.

---

## 1. Slide map and timing

| # | Slide | Time | Purpose |
| ---: | --- | ---: | --- |
| 1 | Title | 0:10 | Who we are, one-line promise |
| 2 | The handoff problem | 0:20 | Why detection alone is not enough |
| 3 | The closed loop | 0:25 | Our contribution in one diagram |
| 4 | How v3 works | 0:30 | Architecture, advisory separation, provenance |
| 5 | Results | 0:45 | Locked-50, honest end-to-end, per-class |
| 6 | Safety by design | 0:30 | Rules, gates, three branches |
| 7 | Impact and next steps | 0:20 | Done, not done, next |
| — | Backup — Q&A | — | 10 backup slides |

The times total 3:00. The script in §2 is ~350 words (~2:55 at a measured pace).

---

## 2. Three-minute script (speaker notes)

> Good morning. Every day, dentists read panoramic X-rays under time pressure. Subtle
> caries is easy to miss, drug safety is checked from memory, and most AI tools stop at
> a bounding box. They do not connect the finding to the dentist's decision, the
> treatment, or the record. DentalAI closes that loop.
>
> Our v3 pipeline uses two detectors: a 32-class tooth detector and a four-class disease
> detector, both at 1024 pixels. A geometric association step assigns every lesion to an
> FDI tooth. Around that core, two advisory layers flag missing teeth and eleven other
> findings, but they never enter the clinical report. The dentist confirms, corrects, or
> rejects every finding. Only confirmed findings drive the rule engine: 26 source-backed
> rules for treatment and drug safety. A warning must be acknowledged; a contraindicated
> drug needs a written reason. Every decision and every correction is stored with the
> model version and threshold.
>
> We evaluate on the official DENTEX validation split: 50 images, 182 lesions, never
> used for training or model selection. At threshold 0.20, mAP at 0.5 is 54.2, with 44.6
> precision and 74.2 recall. On the 145 lesions we match, tooth number is 91.7 percent
> and disease label 89.0 percent. Counting missed lesions end-to-end, tooth accuracy is
> 73.1 percent and joint accuracy 65.9 percent. That is the honest number: a
> second-opinion screen, not an autonomous diagnosis.
>
> We also report the weaknesses. Caries is our hardest class: AP 35.3 in-hospital, and
> 17.7 on an external Romanian hospital set, where overall mAP drops to 43.3. A v4
> candidate was rejected because it lost 5.5 points of end-to-end joint accuracy. We do
> not hide the drop; it is why the dentist stays in the loop and why local validation is
> part of any pilot.
>
> The contribution is the loop: detection, dentist decision, cited treatment and drug
> safety, record, and feedback, with advisory layers kept separate and provenance stored
> per run. This is a research prototype: no reader study, no clinic pilot, no regulatory
> clearance. Next we are improving caries, adding DICOM, calibrating confidence, and
> planning a supervised clinician study. Thank you.

---

## 3. Main slides

### Slide 1 — Title

**Text**

```
DentalAI
A second opinion on every panoramic X-ray — the dentist stays in charge

[Team Lead — Name] · [Backend — Name] · [Frontend — Name]
Seif Ahmed — Integration/Repo · Abdullah Tarek Habashy — ML
Alexandria University (CDS) · Advisor: Ashraf Eshta

IEEE IC-FTAI 2026 · Student Project Track
Alexandria · 23–26 November 2026
```

**Visual:** current v3 review screen (disease boxes + dashed missing-tooth boxes +
advisory panel), cropped to the X-ray and the right-hand findings list. Replace
`hero_faded*.png` / `screen_review*.png` if they show the old v2 UI.

**Notes:** "Good morning. DentalAI is an assistive second opinion for panoramic
X-rays; the dentist reviews and decides every finding." (10 s)

**Fill before submission:** the three names/roles. The repo confirms Seif Ahmed
(integration/repo owner) and Abdullah Tarek Habashy (ML). Do not use "UNVERIFIED".

---

### Slide 2 — The handoff problem

**Headline:** Detection is not the bottleneck. The handoff is.

**Three columns**

| 1. Findings get missed | 2. Safety lives in memory | 3. AI stops at the box |
| --- | --- | --- |
| Subtle caries and periapical changes are easy to miss under time pressure. | Drug safety depends on the patient's full allergy/medication history, not memory. | A detector that ends at a bounding box leaves the decision, the plan and the record disconnected. |

**Bottom line:** "A finding is only useful if it reaches the dentist's decision — and the
decision is recorded."

**Visual:** three simple icons; no unsourced statistic. Do not use the old "23 images"
or "97.5%" figures.

**Notes:** "Most tools optimize the box. We optimized what happens after the box: the
review, the safety check, and the record." (25 s)

---

### Slide 3 — The closed loop

**Headline:** We don't replace the dentist. We close the loop around them.

**Diagram (left → right, one row, loop back)**

```
[ Scan ] → [ AI proposes ] → [ Dentist decides ] → [ Treatment + drug safety ]
                  ↑                                        ↓
             [ Feedback ledger ] ← [ Patient record ] ← [ Confirmed plan ]
```

**Four principles (short)**

1. Every AI finding is **pending** until the dentist confirms, corrects or rejects it.
2. Only confirmed findings reach the **deterministic rule engine**.
3. Advisory layers stay **outside** the report and the treatment plan.
4. Every run stores **model version, weights and threshold** for audit.

**Notes:** "This is the contribution: the loop, not a new detector. The dentist is the
decision-maker at every step." (30 s)

---

### Slide 4 — How v3 works

**Headline:** Two detectors, one association step, two advisory layers.

**Pipeline diagram**

```
Panoramic X-ray (JPEG/PNG/WebP, 1024 px)
        │
        ├─ Tooth detector     YOLOv8s · 32 FDI classes ──┐
        ├─ Disease detector   YOLOv8s · 4 classes ───────┤
        │                                                 ▼
        │                                   IoU → containment → nearest centre
        │                                                 │
        │                                   (tooth, disease) findings
        │
        ├─ Missing teeth      ResNet18 + rules   [advisory · dashed boxes]
        └─ 11-class findings  YOLOv8s            [advisory · separate panel]
```

**Right column: system**

- React UI → FastAPI backend → ML microservice (`:8001`).
- Supabase Auth/DB/Storage; RLS; private bucket; signed URLs.
- Threshold 0.20 / 0.30 / 0.50; re-analysis blocked after the first review.
- `raw_ml_output.model` stores weights, thresholds and `pipeline_version`; the scan page
  shows them in a collapsed **Model provenance** card.

**Footnote:** "Advisory layers are flagged `*_advisory: true` and never enter the
report."

**Visual:** replace `model_arch.png` / `pipeline_strip.png` / `system_arch.png`; the old
diagrams show the coordinator + random forest.

**Notes:** "The tooth detector labels every tooth directly, so a missing tooth does not
shift the numbering. The disease detector finds four lesion classes; association assigns
each lesion to a tooth." (35 s)

---

### Slide 5 — Results on the locked-50

**Headline:** 54.2 mAP@0.5 — and the honest end-to-end number.

**Left: headline metrics**

| Metric | v3 |
| --- | ---: |
| mAP@0.5 | **54.2** |
| mAP@0.5:0.95 | 38.2 |
| Precision | 44.6 |
| Recall | **74.2** |

**Middle: per-class AP@0.5**

| Class | AP |
| --- | ---: |
| Impacted | 75.0 |
| Caries | **35.3** |
| Periapical Lesion | 55.6 |
| Deep Caries | 51.1 |

**Right: what the dentist experiences**

| Metric | Matched (n=145) | End-to-end (n=182) |
| --- | ---: | ---: |
| Tooth number | 91.7% | **73.1%** |
| Disease label | 89.0% | — |
| Joint | 82.8% | **65.9%** |

**Footer:** "Official DENTEX validation: 50 images, 182 lesions, never trained on;
confidence 0.20; 95% CIs in backup B2. v2→v3: recall +9.9 pp, tooth +7.7 pp, joint +8.8
pp (significant); mAP +2.5 pp (ns)."

**Visual:** per-class AP bar chart (`locked50_per_class.png`, to create); keep the v3
`gt_vs_pred_val_*.png` panel if space allows. Remove `heldout_chart.png` (v1 23-image
chart) and `training_fit_chart.png`.

**Notes:** "The mAP is not the headline. The headline is end-to-end: if we count every
lesion in the set, the tooth is right 73.1% of the time and tooth plus disease 65.9%.
That is a second-opinion screen." (45 s)

---

### Slide 6 — Safety by design

**Headline:** The AI proposes. The dentist decides. The rules are auditable.

**Three branches (table)**

| Clinical situation | System proposal | Safety gate |
| --- | --- | --- |
| Caries, no infection | Restorative referral | **No systemic antibiotic** |
| Periapical lesion + active infection | Amoxicillin 500 mg q8h | Allergy/medication check; no conflict |
| Same + penicillin allergy | Clindamycin alternative | Visible warning (R-18); written reason required |

**Bottom row**

- **26 source-backed rules** (ADA 2019, AHA 2021, AAPD, FDA, AGS Beers 2023; PROJECT
  where no source).
- Warnings require acknowledgement; a contraindicated drug requires a written reason.
- Every decision is stored with the dentist's id; the AI report is never committed
  automatically.
- Missing teeth and 11-class findings are **advisory only** — separate panel, not in the
  report or the plan.

**Visual:** replace the old decision-drawer screenshot with a current one showing a
contraindication banner and the advisory panel.

**Notes:** "Plain caries never gets antibiotics. An active infection can get
amoxicillin, but a penicillin allergy switches to clindamycin with a warning the dentist
must acknowledge." (35 s)

---

### Slide 7 — Impact and next steps

**Headline:** A working loop, with the limits stated.

**Done**

- Full clinician loop: auth → upload → AI → review → treatment/drug safety → record →
  feedback.
- v3 locked-50 + external Romanian validation; v4 rejected on the promotion rule.
- 176 backend + 29 frontend tests; 3 CI jobs; local e2e run.
- Public repo + `weights-v3` release; model card, license, provenance.

**Not done**

- No clinician reader study, no prospective pilot, no regulatory clearance.
- Caries AP 35.3 in-hospital / 17.7 external.
- No DICOM/PACS; confidence not calibrated; no retraining from feedback.

**Next**

1. Caries-specific improvement (hard negatives, per-class thresholds, higher resolution,
   segmentation).
2. DICOM/PACS + calibration.
3. Supervised clinician reader study and pilot.

**Footer:** "Thank you — questions? Repo and weights: [QR]"

**Visual:** `repo_qr.png` (verify it points to the public repo); current landing/review
screenshot if space allows.

**Notes:** "This is a research prototype. The next step is a supervised clinician study,
not a claim of clinical readiness." (25 s)

---

## 4. One-page summary abstract (≤250 words)

**Title:** DentalAI: an auditable human-in-the-loop assistant for panoramic dental
radiography

**Abstract**

> Panoramic radiographs are read under time pressure, and AI detectors usually stop at a
> bounding box. We present DentalAI, an assistive system that connects detection to the
> dentist's decision, a cited treatment and drug-safety check, the patient record, and a
> feedback ledger. The v3 pipeline combines a 32-class FDI tooth detector and a four-class
> disease detector at 1024 px, associates each lesion to a tooth, and adds two clearly
> labelled advisory layers — missing teeth and an 11-class findings model — that never
> enter the clinical report. Every AI finding is pending until a dentist confirms,
> corrects or rejects it; only confirmed findings reach 26 source-backed rules. On the
> official DENTEX validation split (50 images, 182 lesions, never used for training or
> selection), v3 achieves mAP@0.5 54.2, precision 44.6 and recall 74.2; on matched
> lesions, tooth number is 91.7% and disease label 89.0%, with end-to-end tooth 73.1% and
> joint 65.9%. Caries remains the weakest class (AP 35.3), and mAP falls to 43.3 on an
> external Romanian hospital set (Caries AP 17.7). The system is a research prototype
> with no reader study or clinic pilot. The contribution is an auditable
> human-in-the-loop workflow, not a claim of autonomous diagnosis.

**Keywords:** dental radiography; panoramic X-ray; clinical decision support; object
detection; human-in-the-loop.

**Word count:** 197. Keep the summary to one A4 page; do not add the old v1 numbers.

---

## 5. Backup slides (B1–B10)

### B1 — Evaluation protocol

- Locked-50 = official DENTEX validation: 50 images / 182 lesions; never trained or
  selected on.
- Frozen production pipeline, conf 0.20; greedy one-to-one matching at IoU ≥ 0.5.
- COCO-style AP; Wilson 95% CIs for rates; image-level paired bootstrap (2,000
  replicates) and McNemar for v2/v3/v4 comparisons.
- Promotion rule: must beat incumbent on mAP@0.5, Caries AP, tooth accuracy and joint
  accuracy. v3 promoted 2026-11-03; v4 rejected 2026-11-04.
- The judge is `dentex_week3/evaluate.py`; no ad-hoc script is accepted.

### B2 — Per-class detection and confusion

| Class | GT | Pred | P (95% CI) | R (95% CI) | F1 | AP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Impacted | 40 | 48 | 75.0 [61.2–85.1] | 90.0 [76.9–96.0] | 81.8 | 75.0 |
| Caries | 101 | 201 | 35.3 [29.0–42.2] | 70.3 [60.8–78.3] | 47.0 | 35.3 |
| Periapical | 9 | 9 | 55.6 [26.7–81.1] | 55.6 [26.7–81.1] | 55.6 | 55.6 |
| Deep Caries | 32 | 45 | 51.1 [37.0–65.0] | 71.9 [54.6–84.4] | 59.7 | 51.1 |
| Micro | 182 | 303 | 44.6 [39.1–50.2] | 74.2 [67.4–80.0] | 55.7 | 54.2 |

**Confusion (GT rows):** Impacted 36/0/0/2; Caries 0/68/0/5; Periapical 0/2/5/0; Deep
Caries 0/6/1/20. **Matched label accuracy (95% CI):** tooth 133/145 = 91.7%
[86.1–95.2]; disease 129/145 = 89.0% [82.8–93.1]; joint 120/145 = 82.8% [75.8–88.0];
quadrant 145/145 = 100% [97.4–100]. **End-to-end:** tooth 133/182 = 73.1%; joint
120/182 = 65.9%.

### B3 — Iterations: v1 → v2 → v3, and why v4 lost

| Metric | v1 | v2 | v3 |
| --- | ---: | ---: | ---: |
| mAP@0.5 | 49.8 | 51.7 | **54.2** |
| Recall | 56.6 | 64.3 | **74.2** |
| Tooth (end-to-end) | 75.9 | 65.4 | **73.1** |
| Joint (end-to-end) | 66.4 | 57.1 | **65.9** |
| Caries AP | 28.2 | 33.3 | **35.3** |

**v2→v3:** mAP +2.5 ns; recall +9.9 (CI +4.5–+15.8); tooth +7.7 (+2.7–+13.0); joint
+8.8 (+2.8–+14.9); McNemar detection p=0.0029, tooth p=0.0094, joint p=0.0070.

**v4 rejected:** mAP 55.1 (+0.8 ns); recall 71.4 (−2.7); tooth 70.3 (−2.7); joint 60.4
(**−5.5, p=0.029**); Deep Caries AP +12.5 but the promotion rule failed.

### B4 — External validation (Romanian hospital)

| Metric | Locked-50 | Romanian (175) |
| --- | ---: | ---: |
| mAP@0.5 | 54.2 | **43.3** |
| mAP@0.5:0.95 | 38.2 | 24.6 |
| Precision | 44.6 | 48.8 |
| Recall | 74.2 | 50.3 |
| Caries AP | 35.3 | **17.7** |
| Impacted AP | 75.0 | 77.7 |
| Periapical AP | 55.6 | 34.6 |

No Deep Caries GT in this external set. The drop is domain shift (different scanner,
population, annotation conversion); it motivates local validation and the dentist loop.

### B5 — Caries and the operating point

- Caries: 101 GT, 201 predictions; P 35.3, R 70.3, AP 35.3. The model over-predicts
  caries at 0.20; the dentist rejects false positives.
- Threshold sweep: 0.20 P44.6/R74.2; 0.30 P51.4/R69.2; 0.50 P68.0/R57.1. The UI exposes
  all three; 0.20 is the recall-oriented default.
- Confidences are **not calibrated**; the threshold is an operating point.
- Planned: hard-negative mining, per-class thresholds, higher resolution/segmentation, a
  caries-specific verifier (trained but off by default; not in v3 results).

### B6 — Advisory layers (not clinical outputs)

| Layer | Result | Why advisory |
| --- | --- | --- |
| Missing teeth (ResNet18 + rules) | F1 0.796, P 0.896, R 0.717, AUC 0.931; rule baseline 0.733 | Interior gaps only; dashed boxes; dentist confirms |
| 11-class findings (DentalOPG) | In-hospital mAP 59.4 / P 57.6 / R 62.7; cross-hospital mAP **11.8** | No DENTEX GT; external drop; panel only |

Both are `*_advisory: true`, excluded from the report, the confirmed-findings gate and the
treatment engine. The findings model's external mAP is why it is not a clinical output.

### B7 — Clinical rules and safety gates

- **26 rules** R-01…R-26; each cites ADA 2019 / AHA 2021 / AAPD / FDA / AGS Beers 2023 or
  is marked PROJECT.
- Three tested branches: caries → restorative, no drug; periapical + infection →
  amoxicillin 500 mg q8h, no conflict; + penicillin allergy → clindamycin + visible
  warning (R-18).
- Warnings require acknowledgement; contraindicated drug requires a written reason; the
  AI report is never committed automatically.
- **Source-backed, not clinician-validated.** No clinician review session is recorded;
  the UI says "pending validation".

### B8 — Privacy, security, and tests

- Supabase Auth; JWT verified server-side; per-dentist ownership; cross-dentist access
  404.
- RLS on all clinical tables with **no client policies**; private `xray-scans` bucket;
  short-lived signed URLs; service-role key server-side only.
- Public demo uses synthetic patients + public DENTEX images; PDPL 151/2020 assessment
  planned before a pilot.
- **176 backend + 29 frontend tests**, typecheck clean, 3 CI jobs (guard/backend/frontend),
  local e2e run 2026-11-05. The 172/16 counts in that run record are historical.

### B9 — Feedback and provenance

- Rejections, relabels, missed lesions, overrides, dose changes and cancellations are
  logged in an append-only ledger; detection corrections go to the ML CSV queue.
- **No retraining job/run exists.** Say "feedback is captured for future retraining", not
  "the model improves".
- Each `/predict` stores weights, thresholds and `pipeline_version` in
  `raw_ml_output.model`; re-analysis is blocked after the first review, so the audit trail
  refers to what the dentist saw.

### B10 — Limitations, status, team, license

**Limitations**

- Small locked set (50 images); periapical only 9 GT (wide CI).
- Caries weak (35.3 in-hospital, 17.7 external); domain shift real.
- No reader study, no prospective pilot, no regulatory clearance.
- No DICOM/PACS; confidence uncalibrated; no retraining; no commercial license for
  DENTEX-derived weights.

**Team:** Alexandria University (CDS); Seif Ahmed (integration/repo), Abdullah Tarek
Habashy (ML), plus backend, frontend and QA/team-lead roles; advisor Ashraf Eshta;
partner dentist Mohamed Fatah.

**License:** code MIT; DENTEX CC BY-NC-SA 4.0; weights research/non-commercial. Repo:
github.com/sayfeldinn/dental-xray-ai-assistant · weights-v3 release.

---

## 6. Figure and asset replacement list

Current assets are in `submission/assets/`. Keep the v3 detection/GT-vs-pred images;
replace the rest.

| Asset | Action | Notes |
| --- | --- | --- |
| `gt_vs_pred_val_2/28/31.png` | **Keep** | v3 GT vs prediction; good for slide 5/backup |
| `detection_val_*.png` | **Keep** | v3 detections; check they show the 4 classes |
| `repo_qr.png` | **Verify** | Must point to the public repo; regenerate if stale |
| `model_arch.png`, `pipeline_strip.png`, `system_arch.png` | **Replace** | Old coordinator/RF diagrams; use slide 3/4 diagrams |
| `loop_large.png` | **Replace/update** | Must show v3 loop and advisory separation |
| `heldout_chart.png` | **Remove** | v1 23-image chart; replaced by locked-50 per-class chart |
| `training_fit_chart.png` | **Remove/replace** | Old training-fit chart; not a generalization result |
| `screen_review*.png`, `screen_finding_review.png`, `screen_plan.png`, `screen_contraindication.png`, `screen_landing.png`, `screen_login.png`, `screen_patient_record.png` | **Recapture** | Current UI only: v3 advisory panel, dashed missing boxes, threshold select, provenance, zoom |
| `hero_faded*.png` | **Replace if v2** | Title slide should show the v3 UI |
| `locked50_per_class.png` | **Create** | Bar chart: 75.0 / 35.3 / 55.6 / 51.1 |
| `v2_v3_delta.png` | **Create** | Recall +9.9, tooth +7.7, joint +8.8; mAP +2.5 ns |
| `external_validation.png` | **Create** | Locked-50 vs Romanian mAP/Caries AP |
| `safety_branches.png` | **Create** | Three branches + gate icons |

Screenshot recipe: start the local stack, log in with the QA dentist, open the QA scan
`e6b213ba-f1ca-4b60-87de-a127e7c14507` (9 findings, 6 missing boxes, 19 advisory), and
capture at 1920×1080. Use the 0.20 run for the main shot and the 0.50 re-run for the
threshold backup. Do not include the local Supabase URL or any token in the shot.

---

## 7. Apply-to-PPTX checklist

- [ ] Replace all old numbers: 97.54 / 76.23 / 75.41 / 23 images / 122 detections / 171 /
      25 / 14 / 196 → the v3 numbers in `FACTS.md`.
- [ ] Replace "coordinator + random forest" with "tooth + disease detectors + association".
- [ ] Remove "UNVERIFIED" highlights and competitor "verify" cells.
- [ ] Add the 7-slide structure + backup divider + B1–B10.
- [ ] Replace the architecture/loop diagrams and all old screenshots.
- [ ] Add speaker notes from §2 to the main slides.
- [ ] Add the abstract from §4 to the one-page summary.
- [ ] Fill the three missing names/roles on the title slide and in `CITATION.cff`.
- [ ] Check the 3:00 script at rehearsal; cut slide 5 detail if over.
- [ ] Export PDF; verify fonts, image resolution, and that no local URL/token is visible.
- [ ] Run the claim→source check in `VERIFICATION.md` against the final PDF.
