# Claim → Source check (Phase 5)

Every number or factual claim that appears in the summary (S) or the deck (D, slide no.) mapped to `FACTS.md`.

| Claim | Where | Source (FACTS.md §) |
| --- | --- | --- |
| 3-stage pipeline: YOLOv8n coordinator → YOLOv8 detector → Random Forest (300 trees, 15 features) | S, D4, D10 | §3; `pipeline_config.json` |
| Enumerators replaced because of missing-tooth numbering shift | S, D11 | §3, §10.3 |
| 4 findings: caries, deep caries, periapical lesion, impacted; FDI numbering | S, D4, D10 | §2 |
| Data: DENTEX 2023 (CC BY-NC-SA); Tufts + Loki set aside; Roboflow never used | S, D10 | §1; DENTEX HF README licence |
| 97.54% / 76.23% / 75.41% on 23 held-out images, 122 detections | S, D5 | §4a (`final_evaluation.json`) |
| Per-quadrant full match 74.19 / 85.71 / 75.76 / 66.67% | D5 chart | §4a |
| Coordinator mAP50 0.995 labelled "training-set fit" | S | §4b (same weights as shipped) |
| MLv2 per-class chart labelled "not shipped · training images" | D10 | §4b |
| 26 contraindication rules; ADA 2019 / AHA 2021 / AAPD / Beers 2023 | S, D4, D14 | §5 |
| Rules source-backed, pending clinician validation | S, D11, D14 | §5 |
| Corrections logged for future retraining; no retraining run | S, D3, D7, D11 | §6 |
| 171 backend + 14 frontend tests (185 total); 3 CI jobs; 6 synthetic profiles; 3 demo branches | S, D7, D13 | §7 |
| No clinic pilot recorded | S (placeholder), D11 | §8 |
| Team names (2 verified), advisor, partner dentist, duration, repo | S, D1 | §9 (advisor/dentist/duration from task brief) |
| Limitations: small set, tooth numbering, uncalibrated confidence, domain gap | S, D11 | §10 |
| Screens are the real app with a synthetic patient (P-003) and public DENTEX images | S Fig. 2, D6 | captured 2026-10-21 via `build/capture_screens.py` |
| Detection examples are the shipped model on DENTEX validation images, conf ≥ 0.35 | D1, D5 | `build/annotate_detections.py` (live `/predict`) |

## Constraint checks

| Check | Result |
| --- | --- |
| Summary is one A4 page (PDF) | ✅ 1 page |
| Abstract ≤ 250 words | ✅ 233 words |
| Keywords 1–5 from the tracks | ✅ 5 (T5.2, T5.4, T5.1, T5.12, T7.11) |
| Main deck ≤ 7 slides, then "Backup — Q&A" divider | ✅ 7 + divider + 6 backup |
| Speaker notes with timing on every main slide | ✅ |
| Main-slide script ≈ 3:00 | ✅ 420 words |
| Forbidden overclaims ("diagnoses", "prescribes", "autonomous", "improves itself", "FDA", "replaces the dentist") | ✅ 0 hits (the official title's word "Diagnostic" is kept) |
