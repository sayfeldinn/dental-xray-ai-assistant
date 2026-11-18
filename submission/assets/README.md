# Submission assets — what is current and what to replace

The binary deck/summary are still the v2 versions. Use this list with
`../DECK_V3_REWRITE.md` §6 and `../../docs/qa/conference-demo-script.md` §5.

## Keep (v3 model outputs)

| File | Use |
| --- | --- |
| `gt_vs_pred_val_2.png`, `gt_vs_pred_val_28.png`, `gt_vs_pred_val_31.png` | GT vs prediction panels; good for results/backup |
| `detection_val_13.png`, `detection_val_14.png`, `detection_val_28.png`, `detection_crop_val_28.png`, `detection_val_14_crop.png` | v3 detection examples; check the class labels/colours |
| `repo_qr.png` | Verify it resolves to the public repo; regenerate if stale |

## Replace (old v1/v2 content)

| File | Why |
| --- | --- |
| `model_arch.png`, `pipeline_strip.png`, `system_arch.png` | Old coordinator/random-forest diagrams |
| `loop_large.png` | Update to the v3 loop + advisory separation |
| `heldout_chart.png` | v1 23-image chart; replaced by locked-50 per-class AP |
| `training_fit_chart.png` | Training-set fit, not a generalization result |
| `hero_faded.png`, `hero_faded_crop.png` | Title image may show the v2 UI |
| `screen_landing.png`, `screen_login.png`, `screen_patient_record.png`, `screen_review.png`, `screen_review_full.png`, `screen_review_crop.png`, `screen_finding_review.png`, `screen_plan.png`, `screen_contraindication.png` | Old UI; recapture current v3 UI (advisory panel, dashed missing boxes, threshold, provenance, zoom) |

## Create (v3 charts)

| File | Content |
| --- | --- |
| `locked50_per_class.png` | AP@0.5 bars: Impacted 75.0, Caries 35.3, Periapical 55.6, Deep Caries 51.1 |
| `v2_v3_delta.png` | Recall +9.9, tooth +7.7, joint +8.8; mAP +2.5 (ns) |
| `external_validation.png` | Locked-50 vs Romanian: mAP 54.2 vs 43.3; Caries AP 35.3 vs 17.7 |
| `safety_branches.png` | Three branches + gate icons |
| `screen_v3_*.png` | Current UI screenshots (see shot list below) |

## Screenshot shot list

Capture at 1920×1080, browser zoom 100%, no devtools, no local URL/token visible.

1. `screen_v3_scan.png` — 0.20 scan, boxes + legend + findings list.
2. `screen_v3_advisory.png` — advisory panel expanded (6 missing + 19 findings).
3. `screen_v3_provenance.png` — provenance card expanded (pipeline v3, weights, gate).
4. `screen_v3_threshold.png` — threshold select + re-run control before review.
5. `screen_v3_plan.png` — treatment plan with the clindamycin warning.
6. `screen_v3_feedback.png` — feedback log with one correction.
7. `screen_v3_landing.png` — landing page (optional, title).

Use the QA scan `e6b213ba-f1ca-4b60-87de-a127e7c14507` (0.20) and the 0.50 scan
`5f25a5ba-542e-4910-bf5b-7c88b7c824b2`. Do not show the QA password or the local
Supabase keys.

## Rules

- Every figure must be generated from the current v3 code/data; no v1/v2 charts.
- Do not use DENTEX images outside the CC BY-NC-SA terms; see `../../NOTICE`.
- Keep the original files; name new ones `*_v3` or replace in place only after review.
- The deck must not show "UNVERIFIED", competitor "verify" cells, or the old 97.54 /
  76.23 / 75.41 numbers.
