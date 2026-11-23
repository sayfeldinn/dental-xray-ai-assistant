# DentalAI — verified facts for IC-FTAI 2026 (v3)

**Status:** source of truth for the conference deck, one-page summary and Q&A.
**Updated:** 2026-11-18, on `feature/conference-v3` (based on `main` `c78a525`).
**Rule:** every number in the deck or summary must trace to a row here and to a file
in the repository. If a number is not here, do not put it on a slide.

> DentalAI is a **research prototype**, not a medical device. The dentist reviews and
> confirms every AI finding; the system never diagnoses, prescribes or writes to the
> record autonomously.

---

## 1. Scope and current status

| Item | Value |
| --- | --- |
| Conference | IEEE IC-FTAI 2026, Student Project Track, Alexandria, 23–26 Nov 2026 |
| Project | AI-assisted dental radiography + patient-history system |
| Current model | **v3** (frozen; `pipeline_version` in `raw_ml_output.model`) |
| Core task | Panoramic X-ray → tooth enumeration + 4 lesion classes + lesion-to-tooth association |
| Clinical loop | scan → AI → dentist review → treatment/drug safety → record → feedback |
| Validation stage | retrospective locked-50 + external Romanian set; **no reader study, no clinic pilot** |
| Regulatory | none; not a medical device |

---

## 2. Data and training

| Dataset | Use | Size | Notes |
| --- | --- | --- | --- |
| **DENTEX 2023** | Tooth detector (32 FDI classes); disease detector mix | Tooth: 540 train / 94 val. Disease mix: 10,120 train / 9,848 unique / 107 val | Official challenge data; CC BY-NC-SA 4.0 |
| **OralXrays-9** | Disease detector mix | Included in the 10,120/9,848/107 figures above | Upstream terms apply |
| **DentalOPG** | Advisory 11-class findings detector | DentalOPG test: 154 held-out images | Advisory only |
| **Romanian hospital set** | External validation only | 175 images (176 for findings) | Never used for training/selection |

**Locked-50:** the official DENTEX validation split — **50 images, 182 lesions** — was
never used for training or model selection. It is the final judge. A candidate is
promoted only if it beats the incumbent on **mAP@0.5, Caries AP@0.5, tooth accuracy and
joint accuracy** (`ml/eval/evaluate.py`).

The earlier v1 coordinator + random-forest pipeline is recoverable from tag
`ml-v1-baseline`; v2 training logs live in `docs/evidence/mlv2/`. Do not quote their
metrics as current.

---

## 3. Pipeline (v3)

```
panoramic X-ray (JPEG/PNG/WebP)
  ├─ tooth detector      YOLOv8s, 32 FDI classes, 1024 px
  ├─ disease detector    YOLOv8s, 4 classes, 1024 px
  │     └─ association: IoU → containment → nearest centre
  ├─ missing teeth       ResNet18 classifier + rule fallback (advisory)
  └─ findings            YOLOv8s, 11 classes, 640 px (advisory)
```

- Tooth classes: FDI 11–18, 21–28, 31–38, 41–48 (32).
- Disease classes: `Impacted`, `Caries`, `Periapical Lesion`, `Deep Caries`.
- Missing teeth: interior FDI gaps only; classifier F1 **0.796**, P **0.896**, R
  **0.717**, validation AUC **0.931**; rule baseline F1 **0.733**. Production gate:
  `conf 0.3`, `t_gap 0.4`. Advisory; never in the report.
- Findings: 11 classes (BDR, Bridge, Cap, Distoangular/Horizontal Impaction, Filling,
  Missing Teeth, Periodontitis, Root Canal, Unerupted Wisdom, Apical Abscess). Advisory;
  never in the report.
- The caries verifier was trained but is **off by default** and is not part of the v3
  production result. Do not claim it improves caries.

**What the app calls:** backend `DentexClient` → `ML_SERVICE_URL/predict` (default
`http://localhost:8001`). `/predict` honours `confidence_threshold` (UI: 0.20 / 0.30 /
0.50; default 0.20). Re-analysis is disabled after the first finding is reviewed.

---

## 4. Detection results — locked-50 (confidence 0.20)

50/50 images scored · 182 ground-truth lesions · 303 predictions · greedy one-to-one
matching at IoU ≥ 0.5.

| Class | GT | Pred | Precision (95% CI) | Recall (95% CI) | F1 | AP@0.5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Impacted | 40 | 48 | 75.0% [61.2, 85.1] | 90.0% [76.9, 96.0] | 81.8% | **75.0** |
| Caries | 101 | 201 | 35.3% [29.0, 42.2] | 70.3% [60.8, 78.3] | 47.0% | **35.3** |
| Periapical Lesion | 9 | 9 | 55.6% [26.7, 81.1] | 55.6% [26.7, 81.1] | 55.6% | **55.6** |
| Deep Caries | 32 | 45 | 51.1% [37.0, 65.0] | 71.9% [54.6, 84.4] | 59.7% | **51.1** |
| **micro avg** | **182** | **303** | **44.6% [39.1, 50.2]** | **74.2% [67.4, 80.0]** | **55.7%** | **54.2** |

**mAP@0.5 = 54.2 · mAP@0.5:0.95 = 38.2 · mAP@0.75 = 42.5 · AR@0.5:0.95 = 51.3**
(macro over the four classes; AR is COCO-style mean recall across 0.5:0.95 on the
returned detections. v2 for comparison: mAP@0.75 42.7 · AR 47.1.)

---

## 5. Label and end-to-end accuracy

**On the 145 lesions the model matched** (IoU ≥ 0.5, any label):

| Metric | Rate (95% CI) | Correct / total |
| --- | ---: | ---: |
| Disease label | **89.0%** [82.8, 93.1] | 129 / 145 |
| Tooth number | **91.7%** [86.1, 95.2] | 133 / 145 |
| Quadrant | **100.0%** [97.4, 100.0] | 145 / 145 |
| Disease **and** tooth (joint) | **82.8%** [75.8, 88.0] | 120 / 145 |

**End-to-end** (all 182 ground-truth lesions; missed lesions count as errors):

| Metric | Rate | Correct / total |
| --- | ---: | ---: |
| Tooth number | **73.1%** | 133 / 182 |
| Joint (disease + tooth) | **65.9%** | 120 / 182 |

**Disease confusion matrix (rows = GT, columns = prediction):**

| GT \ pred | Impacted | Caries | Periapical | Deep Caries |
| --- | ---: | ---: | ---: | ---: |
| Impacted | 36 | 0 | 0 | 2 |
| Caries | 0 | 68 | 0 | 5 |
| Periapical | 0 | 2 | 5 | 0 |
| Deep Caries | 0 | 6 | 1 | 20 |

**Tooth accuracy by quadrant (matched):** Q1 82.4% (n=34), Q2 89.7% (n=29), Q3 100.0%
(n=46), Q4 91.7% (n=36).

> Label accuracy is **conditional on detection**. It is not sensitivity. The end-to-end
> row is the honest headline when a clinician asks "how often is the tooth right?"

---

## 6. Operating point / threshold sweep

| Threshold | Precision | Recall | F1 | Disease acc on matches | n |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.20 (default) | 44.6% | 74.2% | 55.7% | 89.0% | 145 |
| 0.25 | 48.2% | 73.6% | 58.3% | 88.9% | 144 |
| 0.30 | 51.4% | 69.2% | 59.0% | 88.9% | 135 |
| 0.40 | 61.5% | 64.8% | 63.1% | 91.3% | 126 |
| 0.50 | 68.0% | 57.1% | 62.1% | 92.7% | 110 |

The UI exposes 0.20 / 0.30 / 0.50. Higher thresholds trade recall for precision. The
threshold is an operating-point choice; confidences are **not calibrated**.

---

## 7. Model iterations and significance

| Metric | v2 | v3 | Δ | 95% CI (paired bootstrap) | P(v3 > v2) |
| --- | ---: | ---: | ---: | ---: | ---: |
| mAP@0.5 | 51.7 | 54.2 | +2.5 | [−6.9, +12.4] | 0.714 (ns) |
| Recall | 64.3 | 74.2 | **+9.9** | [+4.5, +15.8] | 1.000 |
| Tooth (end-to-end) | 65.4 | 73.1 | **+7.7** | [+2.7, +13.0] | 0.998 |
| Joint (end-to-end) | 57.1 | 65.9 | **+8.8** | [+2.8, +14.9] | 1.000 |

McNemar exact (per-lesion): detection 26 vs 8, p = 0.0029; tooth 20 vs 6, p = 0.0094;
joint 24 vs 8, p = 0.0070.

**v4 was rejected** (2026-11-04): mAP +0.8 pp (ns), recall −2.7 pp, tooth −2.7 pp,
joint **−5.5 pp** (p = 0.029). It did improve Deep Caries AP (+12.5 pp) but failed the
promotion rule. Do not present v4 as the model.

---

## 8. External validation — Romanian hospital set

175 images, tooth-converted GT, no Deep Caries GT in this set:

| Metric | Value |
| --- | ---: |
| mAP@0.5 | **43.3** |
| mAP@0.5:0.95 | 24.6 |
| Precision | 48.8 |
| Recall | 50.3 |
| AP@0.5 Impacted | 77.7 |
| AP@0.5 Caries | **17.7** |
| AP@0.5 Periapical | 34.6 |

The drop from 54.2 → 43.3 mAP is a real domain-shift result. Say it on the limitations
slide; do not hide it. It is evidence for external validation, not a failure to explain
away.

---

## 9. Advisory layers (not in the clinical report)

| Layer | Result | Status |
| --- | --- | --- |
| Missing teeth (ResNet18 + rules) | F1 **0.796**, P **0.896**, R **0.717**, val AUC **0.931**; split-half mean 0.798; rule baseline 0.733 | advisory; dashed boxes + panel |
| 11-class findings (DentalOPG) | In-hospital mAP@0.5 **59.4**, P 57.6, R 62.7 (154 images); cross-hospital mAP **11.8**, P 21.1, R 19.4 (176 images) | advisory; panel only |

Both layers are explicitly labelled `*_advisory: true` in the API and visually separated
in the UI. They are excluded from the report, the confirmed-findings gate and the
treatment engine. The findings model's cross-hospital mAP of 11.8 is why it is not a
clinical output.

---

## 10. Clinical loop and safety

- **Six steps:** scan ingestion → AI detection → dentist confirm/modify/reject →
  recommendation → prescription decision → feedback/audit.
- **26 contraindication rules** (R-01…R-26), deterministic, cited to ADA 2019 / AHA 2021
  / AAPD / FDA / AGS Beers 2023 or marked PROJECT. **Source-backed, not
  clinician-validated.**
- **Three demo branches:** (1) caries, no infection → restorative referral, no drug;
  (2) periapical lesion + active infection → amoxicillin 500 mg q8h, no conflict;
  (3) same + penicillin allergy → clindamycin with visible warning (R-18).
- **Safety gates:** warnings require acknowledgement; a contraindicated drug requires a
  written justification; the AI report is never committed without dentist action.
- **Provenance:** model weights, thresholds and `pipeline_version` are stored with every
  AI run and shown in the scan page's **Model provenance** card; re-analysis is blocked
  after the first review.
- **No LLM** is used for drug selection or dosing.

**No clinic pilot and no clinician validation are recorded in the repo.** The partner
dentist has not reviewed the rules in a recorded session. Do not claim either.

---

## 11. Feedback loop

- Rejections, relabels, missed lesions, drug overrides, dose changes and treatment
  cancellations are logged in the append-only feedback ledger; detection corrections
  also go to the ML CSV queue.
- **No retraining job or retraining run exists.** The model is frozen. Never say "the
  model improves with feedback"; say "feedback is captured for future retraining."

---

## 12. Tests, CI and reproducibility

| Gate | Command | Current (2026-11-18) |
| --- | --- | --- |
| Backend | `cd backend && python3 -m pytest -q` | **176 passed** |
| Frontend | `cd frontend && npm run typecheck && npm test` | **29 passed** (7 files); typecheck clean |
| Model | `python ml/eval/evaluate.py` | v3 frozen on locked-50 |
| E2E | local Supabase + host-network backend | passed 2026-11-05; see `docs/qa/e2e-clinician-flow.md` |
| CI | GitHub Actions: guard, backend, frontend | green on `main` |

The 2026-11-05 e2e record shows 172/16 because it was written before the latest test
additions. Use **176/29** in the deck. The container reproduction of the model scored
mAP 54.9 vs 54.2 local — a <1 pp float/backend difference; use 54.2 as canonical.

---

## 13. Privacy and security

- Supabase Auth; backend verifies the JWT and scopes every request to the dentist.
- RLS on all clinical tables with **no client policies**; private `xray-scans` bucket;
  short-lived signed URLs; service-role key server-side only.
- Cross-dentist access returns 404.
- Local development uses the Supabase CLI stack at `127.0.0.1:54321`; the old cloud
  project is not the demo path. The public Cloudflare Pages URL was unreachable at the
  time of writing (522/523), so the conference demo is **local + recorded video**.
- Do not upload identifiable patient data to the public demo.

---

## 14. Team and affiliation

| Item | Value | Status |
| --- | --- | --- |
| Affiliation | Alexandria University (CDS) | confirmed in repo |
| ML Engineer (research & evaluation lead) | `sayfeldinn` | confirmed |
| Full-stack / Platform Engineer (backend + frontend + DevOps) | `Seif-shawky` | confirmed |
| Team size | 2 | confirmed |
| Duration | 21 Sep – Nov 2026 | update from the old 18 Oct date |
| Repo | https://github.com/sayfeldinn/dental-xray-ai-assistant | public |
| Weights | `weights-v3` release | public; tensor-identical to validated weights |

The team is exactly two people. The deck must not contain "UNVERIFIED" highlights,
competitor "verify" cells, or any additional team members. Use the two roles above;
the same block goes on the title slide and in `CITATION.cff`.

---

## 15. Claims we must not make

| Do not say | Why |
| --- | --- |
| "97.5% accuracy" / "76.2% tooth accuracy" / "75.4% joint" | v1 numbers on 23 images; obsolete |
| "23 held-out images / 122 detections" | v1 benchmark; current is locked-50 / 182 lesions |
| "No held-out mAP/recall" | false since v3; mAP 54.2, recall 74.2 |
| "Coordinator + random forest" | v1; v3 is tooth + disease detectors + association |
| "The model improves with feedback" | feedback is logged; no retraining |
| "Clinically validated" / "clinician-reviewed rules" | no reader study/pilot; rules source-backed only |
| "Diagnoses caries" / "replaces the dentist" | assistive only; dentist confirms every finding |
| "Works on any dental X-ray" | panoramic JPEG/PNG/WebP only; no DICOM |
| "State-of-the-art" / "best open-source" | the open-code DENTEX baseline scored AP50 60.2 on the hidden test vs our 54.2 on val-50 (different sample/evaluator); we are below it and say so |
| "We reproduced the DENTEX winners' numbers" | the 4-class test GT and the baseline's weights are not public; no same-protocol comparison is possible |
| "FDA/CE cleared" | not a medical device |
| "The live site is available" | Cloudflare Pages was 522/523 at writing; use local/video |

---

## 16. Source index

| Claim | Source |
| --- | --- |
| Locked-50 detection, per-class, label accuracy, threshold sweep | `ml/eval/evaluation_report_v3.md` |
| Machine-readable locked-50 summary | `ml/weights/final_evaluation.json` |
| v2→v3 significance, McNemar | `ml/eval/paired_significance_v2_v3.md` |
| v4 rejection | `ml/eval/paired_significance_v3_v4.md` |
| External Romanian set | `ml/eval/disease_cross_hospital.json` |
| Missing teeth | `ml/eval/missing_teeth_model_results.json` |
| Findings | `ml/eval/findings_test_metrics.json`, `findings_cross_hospital.json` |
| Architecture, thresholds, training provenance | `ml/pipeline/pipeline_config.json` |
| Clinical rules | `docs/CLINICAL_GUIDELINES.md` (R-01…R-26) |
| Tests/e2e | `backend/tests/`, `frontend/src/**/*.test.*`, `docs/qa/e2e-clinician-flow.md` |
| License/data terms | `LICENSE`, `NOTICE`, `MODEL_CARD.md` |
