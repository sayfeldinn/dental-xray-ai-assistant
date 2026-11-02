# ML rebuild — notebooks

Rebuild of the DENTEX models from scratch. v1 is frozen in `archive/ml-v1/`
and tagged `ml-v1-baseline`; it stays recoverable until v2 beats it on the
locked benchmark.

## Pipeline

```
panorama
  ├─ tooth detector (32 FDI classes)  -> tooth boxes + numbers
  └─ disease detector (4 classes)     -> lesion boxes + labels
              └─ association by IoU / centre containment / nearest centre
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

`dentex_data.py` is dependency-free, so notebooks 02 and 03/04 produce
**identical splits** from the same seed. The notebooks assert the expected
counts (540/94 and 598/107, 18,095 and 3,529 boxes) to catch drift.

## Data

Source data lives outside the repo (read-only), default
`/home/sayfeldin/Projects/dental-model-research`; override with `DENTEX_DATA`.

| Task | Source | Images | Boxes |
|---|---|---|---|
| Tooth detector | `quadrant_enumeration` | 634 | 18,095 |
| Disease detector | `quadrant-enumeration-disease` | 705 | 3,529 |
| Locked final judge | official `validation_data` | 50 | 182 |

The 50-image validation set is never trained on and never used for model
selection — only for the final report.

## Kaggle workflow

```bash
# 1. train (already pushed; re-push after edits)
kaggle kernels push -p <staging-dir>

# 2. wait, then pull the weights into dentex_week3/production/
KAGGLE_BIN=~/.local/bin/kaggle ./fetch_weights.sh

# 3. evaluate locally
python 05_assemble_and_evaluate.ipynb   # or run its cells
```

Training notebooks disable flips and mosaic for the tooth detector: FDI labels
are position-dependent, so mirroring would silently swap quadrants.

## Baseline to beat (locked 50 images / 182 lesions)

| Metric | v1 |
|---|---|
| mAP@0.5 | 49.8% |
| Precision / Recall | 40.9% / 56.6% |
| Disease accuracy | 83.6% |
| Tooth accuracy | 75.9% |
| Joint accuracy | 66.4% |
| Caries AP@0.5 | 28.2% |
