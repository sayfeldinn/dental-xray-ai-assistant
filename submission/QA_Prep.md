# DentalAI — judge Q&A prep (IC-FTAI 2026, v3)

Answers are grounded in `FACTS.md`. Keep each answer to ~20 seconds; point to the
backup slide. Never quote the old v1 numbers (97.54 / 76.23 / 75.41 on 23 images) or the
old test counts (171/25/14).

| # | Likely question | Answer (2–3 sentences) | Backup |
| ---: | --- | --- | --- |
| 1 | How is this different from commercial dental AI? | Commercial systems focus on detecting findings, and some do it well. Our contribution is the **loop around detection**: the dentist confirms every finding, confirmed findings drive a cited treatment and drug-safety check, the decision is recorded with model provenance, and corrections are logged. We claim the workflow and the auditability, not a better detector. | B1 |
| 2 | What is your test performance, and on what data? | On the official DENTEX validation split — 50 images, 182 lesions, never used for training or selection — v3 gets **mAP@0.5 54.2**, precision 44.6 and recall 74.2 at threshold 0.20. On the 145 lesions it matches, tooth number is 91.7% and disease label 89.0%; counting missed lesions, end-to-end tooth is 73.1% and joint 65.9%. This is retrospective public-data performance, not clinical performance. | B1, B2 |
| 3 | Your notebook shows mAP50 0.922. Why isn't that on the slide? | Those runs validated on their own training folder, so they measure fit, not generalization, and that detector is not the shipped one. We only report the locked-50 judge and the external set. | B3 |
| 4 | Who is liable for a wrong dose? | The treating dentist, exactly as today: the system never finalises a prescription. Every drug is a proposal; a warning needs explicit acknowledgement, a contraindicated drug needs a written reason, and both are stored with the dentist's id for audit. | B7 |
| 5 | Does the model learn from corrections? | Not yet. Every rejection, relabel, missed lesion and override is logged in an append-only ledger and queued for the ML service, but **no retraining run has been done**. Feedback capture is real; model improvement is future work. | B9 |
| 6 | What happens when a tooth is missing? | v3 labels each tooth directly with 32 FDI classes instead of counting teeth in sequence, so a gap does not shift the numbering. The missing-teeth classifier is advisory (F1 0.796) and drawn as dashed boxes; the dentist confirms every tooth number. | B2, B6 |
| 7 | How do you handle patient privacy? | The public demo uses synthetic patients and public DENTEX images. Every request needs a signed-in dentist who sees only their own patients; RLS denies all direct client access, images sit in a private bucket behind short-lived signed links, and cross-dentist access returns 404. A PDPL 151/2020 assessment is planned before any pilot. | B8 |
| 8 | Are the drug rules clinically validated? | They are **source-backed, not clinician-validated**: every dose and rule cites ADA 2019, AHA 2021, AAPD, FDA or AGS Beers 2023, or is marked PROJECT. No clinician review session is recorded yet, and the UI says "pending validation" everywhere. Clinician review is the first pilot step. | B7 |
| 9 | Have you tested it in a real clinic? | No. There is no pilot and no reader study. We have run the full loop end-to-end on a local Supabase stack with synthetic patients and public X-rays; the next step is a supervised pilot with our partner dentist. | B10 |
| 10 | How do you know the software works? | **176 backend and 29 frontend automated tests**, typecheck, and three CI jobs run on every push; the three clinical branches are tested: no drug, drug without conflict, drug with conflict. Security tests check that sign-in is required and one dentist cannot reach another's patients. | B8 |
| 11 | Will it work on our clinic's X-ray machine? | We expect a domain gap: on 175 Romanian hospital images mAP drops from 54.2 to **43.3**, and Caries AP from 35.3 to **17.7**. That is exactly why the dentist reviews everything and why a local-image validation is part of any pilot. | B4 |
| 12 | Why does the AI propose antibiotics at all? | Only when the dentist reports an active infection; plain caries never gets antibiotics, which follows ADA antibiotic-stewardship guidance. A penicillin allergy automatically switches the proposal to clindamycin with a visible warning. | B7 |
| 13 | Caries AP is only 35.3. Why is caries so weak? | Caries is visually subtle, highly imbalanced, and the detector trades precision for recall at the 0.20 operating point: 35.3% precision, 70.3% recall in-hospital, and only 17.7 AP externally. We show it rather than hide it; the next work is hard-negative mining, per-class thresholds, higher resolution/segmentation, and a caries-specific verifier. | B5 |
| 14 | Why did you reject v4 if its mAP was higher? | v4 gained +0.8 pp mAP but that was not significant, and it lost **5.5 pp of end-to-end joint accuracy** (p = 0.029). Our promotion rule requires gains on mAP, Caries AP, tooth and joint; v4 failed, so v3 stayed. | B3 |
| 15 | What is genuinely novel here? | The novelty is the **closed, auditable loop**: detection → dentist decision → cited treatment/drug safety → record → feedback, with advisory layers kept out of the report and model provenance stored per run. It is a systems contribution, not a new detector architecture. | B1 |
| 16 | Do you support DICOM / PACS? | Not yet. The current input is JPEG/PNG/WebP; DICOM/PACS is a stated next step and a requirement for real hospital deployment. | B10 |
| 17 | Are your confidence scores calibrated? | No. The threshold is an operating point, not a probability that a finding is true. We expose 0.20/0.30/0.50 and report the precision–recall trade-off; calibration is future work. | B5 |
| 18 | Why are missing teeth and the 11-class findings not in the report? | Because their evidence is weaker: missing teeth is F1 0.796 but still advisory, and the 11-class findings model drops to **mAP 11.8** on the external set. They are shown in a separate advisory panel, flagged `*_advisory: true`, and never enter the report or treatment engine. | B6 |
| 19 | Can we use this commercially? | The code is MIT, but the weights are trained on DENTEX, which is **CC BY-NC-SA 4.0**, so the weights are research/non-commercial. A commercial deployment would need relicensing/re-training on appropriately licensed data and regulatory work. | B10 |
| 20 | What would you do with six more months? | A supervised clinician reader study, caries-specific improvement, DICOM/PACS, calibration, retraining from the feedback ledger, and a prospective pilot with our partner dentist. The current system is a research prototype, not a product. | B10 |
| 21 | Why 0.20 as the default threshold? | It is recall-oriented: 74.2% recall vs 57.1% at 0.50, which suits a second-opinion screen where the dentist reviews everything. The UI lets the dentist choose 0.20/0.30/0.50 and shows the trade-off. | B5 |
| 22 | How do you know the AI report is not hallucinated? | The report is a deterministic template filled from detected facts; no LLM is used for findings, drugs or doses. The dentist can edit it, and the original AI output is kept for audit. | B1 |
| 23 | Periapical has only 9 ground-truth lesions. Can you trust 55.6 AP? | No — the 95% CI is wide (26.7–81.1), so we present it as an estimate, not a stable class result. The locked-50 set is small; that is a limitation we state. | B2 |
| 24 | Who is on the team? | Alexandria University (CDS): Seif Ahmed (integration/repo), Abdullah Tarek Habashy (ML), plus backend, frontend and team-lead roles; advisor Ashraf Eshta; partner dentist Mohamed Fatah. The full name/role roster is on the title slide. | B10 |

| 25 | How do you audit an AI run? | Every run stores the weights, thresholds and `pipeline_version` in `raw_ml_output.model`; the scan page shows a **Model provenance** card with the pipeline version, tooth/disease/findings weights and missing-teeth gate. Re-analysis is blocked after the first review, so the audit trail refers to what the dentist saw. | B9 |

## Delivery notes

- If a judge pushes on a number, open the backup slide and give the **CI**, not a new
  number.
- If asked something not in `FACTS.md`, say "we have not measured that" — do not improvise.
- Never say "the model improves", "clinically validated", "diagnoses", "FDA/CE", or
  "state-of-the-art".
- The live cloud site was unreachable at writing (522/523); demo locally or play the
  recorded video. Do not promise the URL.
