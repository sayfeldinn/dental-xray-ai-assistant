# DentalAI — Verified Facts for the IC-FTAI 2026 Submission

Source of truth: the repository at commit `3b295e9` ("phases done", 2026-10-20) plus the uncommitted Phase 6 work
(auth, security, Docker, UI redesign) in the working tree on 2026-10-21. Every claim in the summary and the deck must
trace to a row here. `[UNVERIFIED]` = not provable from the repo; it appears highlighted in the drafts.

---

## 1. Datasets

| Dataset | Used in the **shipped** pipeline? | Evidence |
| --- | --- | --- |
| **DENTEX Challenge 2023** (Kaggle mirror `truthisneverlinear/dentex-challenge-2023`) | **Yes.** The shipped quadrant coordinator was trained on DENTEX `quadrant` data; the shipped detector's four classes are DENTEX's diagnosis classes. | `MLv2/notebook93943e382e.ipynb` cells 1 and 6 (DENTEX paths); coordinator hash identical, see §3; `dentex_week3/production/pipeline_config.json` `disease_map` (line 25) |
| Tufts Dental Database | **No** (used only for the earlier 5-class YOLOv8s, `ml/`, which is not shipped) | `ml/README.md` lines 27–30 |
| Loki Silvres (caries) | **No** (same earlier `ml/` model only) | `ml/README.md` class table and "Datasets" |
| Roboflow | **No** — appears only in Week-1 plans; no code or data uses it | `grep -ri roboflow` hits only `docs/Week1_Execution_Plan.md`, `docs/Project_Context.md`, `docs/WEEK1_STATUS.md`, `scripts/setup-week1-board.ps1` |

Provenance of the **shipped disease-detector weights** (`disease_detector_best.pt`, SHA-256 `cf92c8ca…`): it is **not** the
MLv2 detector (`b79c69a9…`), and no training notebook for it is in the repo → its exact training data/split is
**[UNVERIFIED]** (its class set and the pipeline name "DENTEX production candidate" indicate DENTEX).

## 2. Classes (shipped)

**4 pathology classes:** Impacted, Caries, Periapical Lesion, Deep Caries
(`pipeline_config.json` `disease_map`; `backend/app/domain/finding.py` `DISEASE_LABELS`). Teeth are reported in FDI
notation (quadrant 1–4 × tooth 1–8). The earlier `ml/` model had 5 different classes (not shipped).

## 3. Which model ships, and which one the app calls

**Shipped:** the `dentex_week3` 3-stage pipeline (also archived as `dentex_production_portable_run3/`, identical weights):
1. **Coordinator** — YOLOv8n, detects the 4 quadrants (`coordinator_best.pt`, SHA-256 `d53c8b4e…` — byte-identical to MLv2 `coordinator_quadrant/weights/best.pt`).
2. **Disease detector** — YOLOv8 (22.5 MB checkpoint; YOLOv8s-sized), 4 classes, run on the full panoramic image.
3. **Tooth association** — Random Forest, 300 trees, 15 spatial features, maps each lesion to a tooth.

The 4-stage MLv2 design (per-quadrant **enumerators** + IoU association) is **not** shipped:
`dentex_week3/production/README.txt` line 24 "The enumerator is NOT used in the final pipeline"; `pipeline_config.json`
line 49 `"enumerator_used": false`; Run-3 report §1 ("removed the YOLO enumerators").

**The app calls it:** backend `DentexClient` posts to `{ML_SERVICE_URL}/predict` (`backend/app/services/ml_client/dentex_client.py`
line 80); `ML_SERVICE_URL` defaults to the `dentex_week3` service on port 8001 (`backend/app/core/config.py`;
`CHANGELOG_MODEL_SWITCH.md`).

## 4. Metrics (exact; never mix without labels)

### 4a. Shipped pipeline — held-out benchmark (the only held-out evaluation of the shipped system)
`dentex_week3/production/final_evaluation.json`; `README.txt` lines 11–13. **23 held-out images, 122 detections.**

| Metric | Value |
| --- | --- |
| Disease label correct | 119/122 = **97.54%** |
| Tooth number correct | 93/122 = **76.23%** |
| Disease **and** tooth correct | 92/122 = **75.41%** |
| Full-match by quadrant | Q1 74.19% · Q2 85.71% · Q3 75.76% · Q4 66.67% |

Caveats: the denominator is detections that were matched, so "disease accuracy" is label correctness, **not**
sensitivity/recall; 23 images is a small set; RF confidences are uncalibrated model probabilities (Run-3 report line 23).
mAP50 / mAP50-95 / precision / recall of the **shipped detector** on a held-out split: **not in the repo [UNVERIFIED]**.

### 4b. MLv2 training runs (Kaggle, DENTEX) — fit on **training images**, not a held-out estimate
In every MLv2 data YAML the validation path is the training folder (`val: {output_dir}images/train`, notebook cells 2 and 7,
with the comment "Split this properly later"). The numbers below therefore measure **training-set fit**:

| Model | Images / instances | P | R | mAP50 | mAP50-95 | Shipped? |
| --- | --- | --- | --- | --- | --- | --- |
| Coordinator (YOLOv8n) | 693 / 2772 | 0.999 | 0.999 | **0.995** | 0.809 | **Yes (same weights)** |
| Enumerators Q1–Q4 (YOLOv8n) | e.g. 634 / 5039 | ≈0.97–0.98 | ≈0.97 | **0.986–0.987** | ≈0.66 | No |
| Disease detector (YOLOv8s) | 678 / 3528 | 0.884 | 0.854 | **0.922** | 0.726 | **No (different weights)** |

MLv2 per-class (training-set fit; class order = DENTEX disease ids): Impacted 0.988 / Caries 0.836 / Periapical Lesion
0.919 / Deep Caries 0.946 mAP50. The MLv2 report calls these "exceptional"; they are **not** generalization results and
must not be presented as test performance.

### 4c. Earlier model (`ml/`, 5-class YOLOv8s, Tufts + Loki, **validation split**, not shipped)
`ml/Evaluation_Report.md` §2: all P 0.544, R 0.463, mAP50 0.380; Caries P 0.555, R 0.667, mAP50 0.648. Shown only as
history ("DENTEX boxes were tooth-level; purging them lifted Caries mAP50 from 0.009 to 0.648").

## 5. Drug and dosage recommendations

**Built** (Phase 3): finding → treatment mapping **plus** candidate drugs with regimens (adult and weight-based
pediatric), 26-rule contraindication register (R-01…R-26), daily-dose limits, decision gates
(`backend/app/services/recommendation/`, `backend/app/services/contraindication/`, `docs/CLINICAL_GUIDELINES.md` §2, §4).
**Validation status: source-backed, NOT clinician-validated.** Every value cites ADA 2019 / AHA 2021 / AAPD / FDA /
AGS Beers 2023 or is marked PROJECT (`docs/PHASE3_STATUS.md` line 5, line 110; `docs/PHASE6_STATUS.md` line 51). Every
API response carries "Pending Dentist Validation" (`backend/app/domain/prescription.py` line 17). The QA tables in
`docs/qa/` are marked UNVALIDATED (no dentist meeting held).

## 6. Feedback loop

**Corrections are logged for future retraining.** Rejections, relabels, missed lesions, drug overrides, dose changes and
treatment cancellations are written to the append-only `clinical_feedback_logs` table; detection corrections are also
forwarded to the ML service's CSV queue (`docs/PHASE4_STATUS.md`). **No retraining job or retraining run exists**
(`docs/PHASE4_STATUS.md` line 53). Never claim "the model improves".

## 7. Test evidence

| Item | Evidence |
| --- | --- |
| Backend automated tests | **171 passed** (pytest; also from a clean install of `requirements.txt` on Python 3.12) — `docs/PHASE6_STATUS.md`; re-run 2026-10-21 |
| Frontend automated tests | **25 passed** (vitest) + typecheck + production build |
| HTTP/route tests | `backend/tests/test_api.py`, `test_auth.py` (401 without token, 404 across dentists). A test literally named "route-contract" **does not exist** |
| CI | `.github/workflows/ci.yml`: **guard** (no weights/.env/keys committed), **backend** (compile + pytest), **frontend** (typecheck + test + build) |
| Synthetic profiles | 6 (P-001…P-006) — `docs/qa/synthetic-patient-profiles.md`; 23 contraindication/negative cases in `docs/qa/contraindication-test-cases.md` (marked UNVALIDATED) |
| Three demo branches | `backend/tests/test_recommendation_engine.py` lines 29, 34, 41: (1) caries → restorative referral, **no drug**; (2) periapical lesion + infection → **amoxicillin 500 mg q8h, no conflict**; (3) same with penicillin allergy → **clindamycin with visible warning (R-18)** |
| Live end-to-end runs | throwaway patients/accounts on the dev Supabase, deleted afterwards (`docs/PHASE3–6_STATUS.md`) |

## 8. Clinic pilot

**No pilot is recorded in the repo** (no pilot notes/logs; `docs/qa/*` state the dentist meeting was not held;
`docs/PHASE3_STATUS.md` line 5 "no clinic partner yet"). → Pilot status **[UNVERIFIED]**; the drafts say "clinic pilot:
planned" unless the team confirms otherwise.

## 9. Team

| Item | Value | Source |
| --- | --- | --- |
| Affiliation | Alexandria University (CDS) | `ml/README.md` line 8 |
| ML engineering | Abdullah Tarek Habashy | `ml/README.md` line 8; git author `abdullahtarek4` |
| Repo owner / commits | Seif Ahmed (`sayfeldinn`) | `git log` authors |
| Five names and roles | Roles defined (ML Engineer, Backend Engineer, Frontend Engineer, Integration/QA Engineer, Team Lead/Clinical Liaison) but **names not in repo** → **[UNVERIFIED]** except the two above | `docs/Week1_Execution_Plan.md` §2 |
| Advisor | Ashraf Eshta | task brief (not in repo) |
| Partner dentist | Mohamed Fatah | task brief (not in repo); note §5/§8: no clinician review recorded |
| Repo | https://github.com/sayfeldinn/dental-xray-ai-assistant | `git remote -v` |
| Duration | 21 Sep – 18 Oct 2026 | task brief; git history spans 2026-09-26 → 2026-10-20 |

## 10. Known limitations

1. **Small held-out set** (23 images, 122 detections); no held-out mAP/recall for the shipped detector (§4a).
2. **MLv2 metrics are training-set fit** (validation split = training folder) (§4b).
3. **Tooth numbering:** the MLv2 enumerators shifted numbering when a tooth is missing (`MLv2/Evaluation_Report_v2.md`
   line 24); the shipped RF association was introduced to address it, but tooth accuracy is still 76.23% — tooth numbers
   remain the weakest output.
4. **Uncalibrated confidences** (RF model probabilities; Run-3 report line 23).
5. **Domain gap:** trained and evaluated on public DENTEX images only; no real-clinic images (our assessment — not
   written in the evaluation reports).
6. **Clinical rules not clinician-validated** (§5); **no retraining yet** (§6); **no pilot** (§8).
7. Not modelled: pregnancy, renal dose adjustment, penicillin-reaction severity (`docs/PHASE3_STATUS.md` §7).
