# Datasets

Large datasets are **never** stored in this repository. They live outside the
working tree and are referenced by path.

## Local layout (this machine)

| Dataset | Path | Used by |
| --- | --- | --- |
| DENTEX YOLO export (4.9 GB) | `~/Projects/dental-model-research/data/dentex_yolo` | `notebooks/03`, `04`, `06` |
| DENTEX raw + validation triple | `~/Projects/dental-model-research/data/raw/dentex` | `dentex_week3/evaluate.py` |
| Romanian external set | `~/Projects/dental-model-research/data/raw/romania` | `notebooks/12` |

The YOLO export was moved out of the repository during the 2026-11 cleanup
(it used to sit at `datasets/dentex_yolo`). It is reproducible from the raw
DENTEX archives with `notebooks/01_data_audit.ipynb` and
`notebooks/02_prepare_dataset.ipynb`.

## Rules

1. Do not commit datasets, weights, or training runs. `.gitignore` already
   covers `datasets/`, `*.pt`, `runs/`, and `archive/`.
2. Every evaluation must name the exact dataset path it used; see
   `submission/VERIFICATION.md` for the claim-to-source map.
3. The locked-50 split (official DENTEX validation) is the only promotion
   judge. It is never used for training or model selection.

## Recreating the data

```bash
# 1. Download the official archives (DENTEX on Hugging Face)
#    training_data.zip, validation_data.zip, validation_triple.json

# 2. Audit and convert to the YOLO layout
jupyter lab notebooks/01_data_audit.ipynb
jupyter lab notebooks/02_prepare_dataset.ipynb

# 3. Point the notebooks at the export
export DENTEX_YOLO_DIR=~/Projects/dental-model-research/data/dentex_yolo
```
