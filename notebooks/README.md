# ML rebuild — notebooks

Rebuild of the DENTEX models from scratch. v1 is frozen in `archive/ml-v1/`
(tag `ml-v1-baseline`) and v2 in `archive/ml-v2/`. The shipped disease
detector is v3.

## Pipeline

```
panorama
  ├─ tooth detector (32 FDI classes)  -> tooth boxes + numbers
  ├─ disease detector (4 classes)     -> lesion boxes + labels
  │           └─ association by IoU / centre containment / nearest centre
  └─ findings detector (11 classes)   -> advisory, /predict + /findings
```

This replaces v1's quadrant coordinator + random-forest tooth assignment.

## Notebooks

| # | Notebook | Where | Purpose |
|---|---|---|---|
| 00 | `00_setup.ipynb` | local | verify source data and environment |
| 01 | `01_data_audit.ipynb` | local | class balance, lesion sizes, leakage check |
| 02 | `02_prepare_dataset.ipynb` | local | COCO -> YOLO, stratified 85/15 split (seed 42) |
| 03 | `03_train_tooth_detector.ipynb` | Kaggle GPU | 32-class FDI detector |
| 04 | `04_train_disease_detector.ipynb` | Kaggle GPU | 4-class detector + rare-class oversampling |
| 05 | `05_assemble_and_evaluate.ipynb` | local | v2 pipeline on the locked 50, v1-vs-v2 table |
| 06 | `06_train_pathology_v3.ipynb` | Kaggle GPU | paced OralXrays download, merge, v3 training |
| 07 | `07_evaluate_v3.ipynb` | local | v3 on the locked 50, v1/v2/v3 table, significance |
| 08 | `08_train_findings_detector.ipynb` | Kaggle GPU | 11-class findings detector (missing, BDR, filling, crown, RCT, ...) |
| 09 | `09_evaluate_findings.ipynb` | local | findings held-out test (154) + locked-50 domain-shift sanity |
| 10 | `10_train_pathology_v4.ipynb` | Kaggle GPU | v4 (rejected): DENTEX + OralXrays + converted Romanian |
| 11 | `11_evaluate_v4.ipynb` | local | v4 on the locked 50, v1-v4 table, significance |
| 12 | `12_cross_hospital.ipynb` | local | Romanian external split: disease + findings transfer |
| 13 | `13_train_caries_verifier.ipynb` | Kaggle GPU | caries tooth-crop verifier (optional, not promoted) |
| 14 | `14_train_missing_teeth.ipynb` | Kaggle GPU | missing-teeth gap-vs-tooth classifier |

`dentex_data.py` is dependency-free, so notebooks 02 and 03/04 produce
**identical splits** from the same seed. The notebooks assert the expected
counts (540/94 and 598/107, 18,095 and 3,529 boxes) to catch drift.

## Data

Source data lives outside the repo (read-only), default
`/home/sayfeldin/Projects/dental-model-research`; override with `DENTEX_DATA`.

| Task | Source | Images | Boxes |
|---|---|---|---|
| Tooth detector | `quadrant_enumeration` | 634 | 18,095 |
| Disease detector (v2) | `quadrant-enumeration-disease` | 705 | 3,529 |
| Disease detector (v3) | DENTEX + OralXrays | 9,848 unique (10,120 with oversampling) | 40,985 |
| Disease detector (v4) | + Romanian 14-class (Zenodo 15487430) | +1,375 train (≈1,100 usable) | +4,527 raw, ≈3,300 converted |
| Findings detector | DentalOPG 1550 (Roboflow) | 1,068 train / 303 val | 3,861 train / 1,110 val (11 classes) |
| Locked final judge | official `validation_data` | 50 | 182 |

The 50-image validation set is never trained on and never used for model
selection — only for the final report. The OralXrays validation split is
identical to the locked 50, so only its `train` split is used.

## Kaggle workflow

```bash
# 1. train (already pushed; re-push after edits)
python push_kaggle.py --only pathology

# 2. wait, then pull the weights without touching production/
KAGGLE_BIN=~/.local/bin/kaggle ./fetch_v3.sh

# 3. evaluate locally
python 07_evaluate_v3.ipynb   # or run its cells

# findings detector (separate model, same pattern)
python push_kaggle.py --only findings
KAGGLE_BIN=~/.local/bin/kaggle ./fetch_findings.sh
python 09_evaluate_findings.ipynb

# v4 (rejected 2026-11-04; it lost Caries/tooth/joint on the locked 50)
# adds the Romanian hospital; lesion boxes are converted to DENTEX-style
# tooth boxes with the production tooth detector
python push_kaggle.py --only pathology_v4
KAGGLE_BIN=~/.local/bin/kaggle ./fetch_v4.sh
python 11_evaluate_v4.ipynb

# cross-hospital check on the Romanian external split
python 12_cross_hospital.ipynb

# caries tooth-crop verifier (optional precision knob; not promoted)
python push_kaggle.py --only caries_verifier
KAGGLE_BIN=~/.local/bin/kaggle ./fetch_caries_verifier.sh
python 13_train_caries_verifier.ipynb

# missing-teeth classifier (derived gaps + gap-vs-tooth validation)
python push_kaggle.py --only missing_teeth
KAGGLE_BIN=~/.local/bin/kaggle ./fetch_missing_teeth.sh
python 14_train_missing_teeth.ipynb
```

Training notebooks disable flips and mosaic for the tooth detector: FDI labels
are position-dependent, so mirroring would silently swap quadrants.

## Baseline to beat (locked 50 images / 182 lesions)

| Metric | v1 | v2 | v3 (current) |
|---|---|---|---|
| mAP@0.5 | 49.8% | 51.7% | **54.2%** |
| Precision / Recall | 40.9% / 56.6% | 43.0% / 64.3% | **44.6% / 74.2%** |
| Disease accuracy | 83.6% | 87.7% | **89.0%** |
| Tooth accuracy | 75.9% | 91.5% | **91.7%** |
| Joint accuracy | 66.4% | 80.0% | **82.8%** |
| Caries AP@0.5 | 28.2% | 33.3% | **35.3%** |
| Periapical AP@0.5 | 42.9% | 37.5% | **55.6%** |

## Findings detector (advisory, not part of the locked-50 judge)

DentalOPG 1550, 640 px, 40 epochs. Exposed as `POST /findings` with
`"advisory": true`; it does not change `/predict` or the table above.

| Split | Images | mAP@0.5 | mAP@0.5:0.95 | Missing Teeth AP | BDR AP |
|---|---|---|---|---|---|
| DentalOPG val | 303 | 61.9% | 25.1% | 72.0% | 64.3% |
| DentalOPG test | 154 | 59.4% | 24.9% | 65.4% | 53.8% |

DentalOPG is a different hospital population, and there is no DENTEX ground
truth for these classes. Locked-50 boxes are tooth-sized and plausible, but
accuracy there is unverified — hence advisory-only.
