# Model card — DentalAI v3

## Model details

| Field | Value |
| --- | --- |
| Pipeline version | **v3** (frozen; `pipeline_version` stored in `raw_ml_output.model`) |
| Task | Panoramic dental X-ray: tooth enumeration, lesion detection, lesion-to-tooth association |
| Tooth detector | Ultralytics **YOLOv8s**, 32 FDI classes, 1024 px |
| Disease detector | Ultralytics **YOLOv8s**, 4 classes (`Caries`, `Deep Caries`, `Periapical Lesion`, `Impacted`), 1024 px |
| Association | IoU → containment → nearest centre |
| Missing teeth (advisory) | **ResNet18** classifier + rule fallback; interior FDI gaps only |
| Findings (advisory) | **YOLOv8s**, 11 DentalOPG classes, 640 px; never enters the report |
| Input | JPEG / PNG / WebP panoramic radiograph |
| Output | Tooth boxes + FDI numbers; disease boxes + labels; associated findings; advisory layers; report text |
| Weights | Public `weights-v3` release; tensor-identical to the validated local weights |
| License | Code MIT; weights and DENTEX-derived data research/non-commercial (see NOTICE) |

## Intended use

DentalAI is an **assistive second-opinion** prototype for research and education. It
surfaces candidate findings on a panoramic radiograph, proposes an FDI tooth for each
lesion, and supports a dentist's review. Confirmed findings flow into a deterministic
treatment and drug-safety workflow with explicit safety gates.

It is intended for:

- research demonstrations and model evaluation;
- clinician-in-the-loop review experiments;
- teaching and conference presentations.

## Out of scope

Do **not** use DentalAI for:

- autonomous diagnosis, prescribing, or treatment planning;
- patient care outside a supervised research setting;
- screening without a licensed dentist's review;
- bitewing/periapical images (the model was trained on panoramas);
- DICOM/PACS ingestion (only JPEG/PNG/WebP are supported);
- paediatric or edentulous cases outside the training distribution;
- any commercial use of the DENTEX-derived weights.

## Training data

| Dataset | Use | Notes |
| --- | --- | --- |
| **DENTEX 2023** | Tooth detector (540 train / 94 val); disease detector mix | 32 FDI tooth classes, 4 disease classes; CC BY-NC-SA 4.0 |
| **OralXrays-9** | Disease detector mix (10,120 train / 9,848 unique / 107 val) | See upstream dataset terms |
| **DentalOPG** | Advisory 11-class findings detector | See upstream dataset terms |
| **Romanian hospital set** | External validation only (175 images) | Never used for training or selection |

The **locked-50** official DENTEX validation split (50 images, 182 lesions) was never
used for training or model selection. It is the judge for every candidate.

## Evaluation

Locked-50, confidence threshold 0.20, 303 predictions:

| Metric | v3 |
| --- | ---: |
| mAP@0.5 | **54.2** |
| mAP@0.5:0.95 | **38.2** |
| Precision | **44.6** (95% CI 39.1–50.2) |
| Recall | **74.2** (95% CI 67.4–80.0) |

Per-class AP@0.5: **Impacted 75.0**, **Caries 35.3**, **Periapical Lesion 55.6**,
**Deep Caries 51.1**.

On the 145 matched lesions: tooth **91.7%**, disease **89.0%**, quadrant **100%**,
joint **82.8%**. End-to-end (including missed lesions): tooth **73.1%**, joint
**65.9%**.

External Romanian hospital set (175 images): mAP@0.5 **43.3**, Caries AP **17.7**,
precision **48.8**, recall **50.3**. This domain-shift drop is a known limitation, not
a hidden result.

v2 → v3: recall **+9.9 pp**, end-to-end tooth **+7.7 pp**, joint **+8.8 pp** (all
significant); mAP **+2.5 pp** (not significant). A v4 candidate was rejected after
losing **5.5 pp** of end-to-end joint accuracy (p = 0.029).

Advisory layers:

- Missing teeth: F1 **0.796**, precision **0.896**, recall **0.717**, validation AUC
  **0.931**; rule baseline F1 0.733 (best derivation threshold).
- 11-class findings: in-hospital mAP@0.5 **0.594**; cross-hospital **0.118**. Advisory
  only; excluded from the report.

## Limitations and risks

- **Caries is the weakest class.** AP 35.3 in-hospital and 17.7 externally. Low
  precision at the default threshold means false positives are expected.
- **Domain shift is real.** Performance drops on the external Romanian set.
- **Confidence is not calibrated.** The threshold is an operating-point choice, not a
  probability that a finding is true.
- **Label accuracy is conditional on detection.** End-to-end accuracy is lower because
  missed lesions count as errors.
- **No clinician reader study, no prospective pilot, no regulatory clearance.**
- **No DICOM/PACS.** Real hospital workflows are not yet supported.
- **Advisory layers can be wrong.** Missing-teeth and 11-class findings are deliberately
  excluded from the clinical report and treatment engine.
- **No retraining from feedback.** Corrections are logged but the model is frozen.
- **Dataset bias.** DENTEX/OralXrays/DentalOPG do not represent every population,
  scanner, or technique; the external drop is evidence of this.
- **Privacy.** The public demo uses synthetic/local data; do not upload identifiable
  patient images.

## Ethical and regulatory notes

DentalAI is a research prototype and **not a medical device**. It has no CE/FDA/EDA
clearance. Any clinical deployment would require regulatory review, a prospective
reader study, calibration, monitoring, and a data-protection assessment. The UI keeps
the dentist in control, labels all AI output as pending, and blocks autonomous writes.
The rule engine is deterministic and cited; no LLM is used for drug selection or dosing.

## Citation and license

- Citation: `CITATION.cff`.
- Code: MIT (`LICENSE`).
- Weights and DENTEX-derived data: research/non-commercial; DENTEX is CC BY-NC-SA 4.0
  (`NOTICE`).
- Full evaluation: `dentex_week3/eval/evaluation_report_v3.md`.
