# Claim → source check — v3 conference materials

**Updated:** 2026-11-18. This table verifies the **v3 rewrite** (`FACTS.md`,
`DECK_V3_REWRITE.md`, `QA_Prep.md`). The binary deck/summary in this folder are the
**old v2 versions** until the team applies the rewrite; do not submit them as-is.

Status: ✅ verified in the repo · ⬜ must be applied/captured before submission · ⚠️ known
limitation that must stay visible.

## 1. Content claims

| # | Claim in the v3 deck / summary | Source | Status |
| ---: | --- | --- | --- |
| 1 | v3 = YOLOv8s tooth (32 FDI) + YOLOv8s disease (4 classes) + IoU/centre association | `pipeline_config.json`; `docs/ARCHITECTURE.md` §4.2 | ✅ |
| 2 | Missing teeth = ResNet18 + rule fallback, advisory only | `pipeline_config.json`; `missing_teeth_model_results.json` | ✅ |
| 3 | 11-class findings = advisory only, excluded from the report | `pipeline_config.json`; `findings_*.json`; `ScanPage.tsx` | ✅ |
| 4 | Data: DENTEX 2023 (540/94 tooth; 10,120/9,848/107 disease mix) + OralXrays; DentalOPG advisory; Romanian external | `pipeline_config.json` `training`; `FACTS.md` §2 | ✅ |
| 5 | Locked-50: 50 images, 182 lesions, 303 predictions, conf 0.20 | `evaluation_report_v3.md` | ✅ |
| 6 | mAP@0.5 54.2; mAP@0.5:0.95 38.2; P 44.6 [39.1–50.2]; R 74.2 [67.4–80.0] | `evaluation_report_v3.md` | ✅ |
| 7 | Per-class AP: Impacted 75.0, Caries 35.3, Periapical 55.6, Deep Caries 51.1 | `evaluation_report_v3.md` | ✅ |
| 8 | Matched-label accuracy: disease 89.0, tooth 91.7, quadrant 100, joint 82.8 (n=145) | `evaluation_report_v3.md` | ✅ |
| 9 | End-to-end: tooth 73.1, joint 65.9 (n=182) | `paired_significance_v2_v3.md` | ✅ |
| 10 | Threshold sweep 0.20/0.30/0.50 = P44.6/R74.2, P51.4/R69.2, P68.0/R57.1 | `evaluation_report_v3.md` §4 | ✅ |
| 11 | v2→v3: recall +9.9 pp, tooth +7.7 pp, joint +8.8 pp significant; mAP +2.5 ns | `paired_significance_v2_v3.md` | ✅ |
| 12 | v4 rejected: joint −5.5 pp, p=0.029; mAP +0.8 ns | `paired_significance_v3_v4.md` | ✅ |
| 13 | External Romanian: 175 images, mAP 43.3, Caries AP 17.7, P 48.8, R 50.3 | `disease_cross_hospital.json` | ✅ |
| 14 | Missing teeth: F1 0.796, P 0.896, R 0.717, AUC 0.931; rule baseline 0.733 | `missing_teeth_model_results.json` | ✅ |
| 15 | Findings: in-hospital mAP 59.4 / P 57.6 / R 62.7; cross-hospital mAP 11.8 | `findings_test_metrics.json`; `findings_cross_hospital.json` | ✅ |
| 16 | 26 contraindication rules, source-backed, not clinician-validated | `docs/CLINICAL_GUIDELINES.md`; `FACTS.md` §10 | ✅ / ⚠️ |
| 17 | Feedback logged; **no retraining run** | `docs/PHASE4_STATUS.md`; `FACTS.md` §11 | ✅ |
| 18 | Tests: **176 backend + 29 frontend**, typecheck clean (2026-11-18) | `pytest -q`; `npm test`; `npm run typecheck` | ✅ |
| 19 | Local e2e loop passed 2026-11-05; 172/16 counts in that record are historical | `docs/qa/e2e-clinician-flow.md` | ✅ |
| 20 | No clinic pilot, no reader study, no regulatory clearance | repo search; `FACTS.md` §10/§14 | ✅ / ⚠️ |
| 21 | Code MIT; DENTEX CC BY-NC-SA; weights research/non-commercial | `LICENSE`, `NOTICE`, `MODEL_CARD.md` | ✅ |
| 22 | Repo public; `weights-v3` public release; tensor-identical weights | release page; verification notes | ✅ |
| 23 | Team: Alexandria University (CDS); Seif Ahmed; Abdullah Tarek Habashy; advisor Ashraf Eshta; partner dentist Mohamed Fatah | `FACTS.md` §14 | ✅ |
| 24 | Remaining three names/roles | team roster, **not in repo** | ⬜ fill before submission |
| 25 | UI screenshots show v3 advisory panel, dashed missing boxes, threshold, provenance | current `ScanPage.tsx` / `XrayViewer.tsx` | ⬜ recapture (old assets are v2) |
| 26 | Architecture diagram shows tooth + disease + association + advisory layers | `DECK_V3_REWRITE.md` | ⬜ replace old diagram |
| 27 | Live cloud site | Cloudflare Pages returned 522/523 at writing | ⚠️ do not claim; use local/video |

## 2. Removed from the old deck

| Old claim | Why removed |
| --- | --- |
| Coordinator + Random Forest, 300 trees, 15 features | v1 architecture; replaced by tooth + disease detectors |
| 97.54% disease / 76.23% tooth / 75.41% joint on 23 images | v1 benchmark; superseded by locked-50 |
| "No held-out mAP/recall" | false; v3 has mAP 54.2 / R 74.2 |
| 171 backend / 25 frontend / 14 frontend / 196 total | inconsistent and stale; current is 176/29 |
| "UNVERIFIED" names and competitor "verify" cells | not submission-ready; replace with confirmed roles/names |
| "Model improves with feedback" | no retraining |
| "Clinically validated" | no reader study/pilot |
| Live site URL / "available" | site was down; local demo + video |

## 3. Constraint checks (apply to the updated deck/summary)

| Check | Target | Current |
| --- | --- | --- |
| Summary is one A4 page (PDF) | 1 page | ⬜ regenerate from v3 text |
| Abstract ≤ 250 words | ≤ 250 | ⬜ new abstract in `DECK_V3_REWRITE.md` |
| Keywords 1–5 from the tracks | 5 | ⬜ keep T5.2, T5.4, T5.1, T5.12, T7.11 |
| Main deck ≤ 7 slides + "Backup — Q&A" divider | 7 + divider + backup | ⬜ apply rewrite |
| Speaker notes/timing on every main slide | yes | ⬜ apply rewrite |
| Main script ≈ 3:00 | ~350 words (~2:55) | ⬜ rehearse |
| Forbidden overclaims ("diagnoses", "prescribes", "autonomous", "improves itself", "FDA", "replaces the dentist") | 0 hits | ⬜ check after edit |
| Every number traceable to `FACTS.md` | 100% | ✅ for the rewrite; ⬜ for the binary deck |
| No "UNVERIFIED" or competitor "verify" cells | 0 | ⬜ remove from binary deck |
| Figures/screenshots current | v3 UI + v3 metrics | ⬜ recapture/replace |

## 4. Sign-off

| Role | Name | Date |
| --- | --- | --- |
| ML / numbers | Abdullah Tarek Habashy | |
| Integration / demo | Seif Ahmed | |
| Team Lead | | |
| Advisor | Ashraf Eshta | |

The deck is submission-ready only when every ⬜ above is closed and the binary PDF/PPTX
matches this table.
