# DentalAI — YOLOv8s Dental Lesion Detector (Phase 1)

Phase 1 detection model: **YOLOv8s** trained on panoramic dental radiographs. This
directory holds the training notebook and the model card. **Weights are not in git** —
they are published as a [GitHub Release](https://github.com/sayfeldinn/dental-xray-ai-assistant/releases)
asset because they are 22.6 MB (see `CONTRIBUTING.md`).

> Engineering by Abdullah Tarek Habashy (Alexandria University, CDS).

## Status

| Item | Value |
| --- | --- |
| Weights | [`v0.1-dental-yolov8s`](https://github.com/sayfeldinn/dental-xray-ai-assistant/releases/tag/v0.1-dental-yolov8s) → `best.pt` (22,601,514 bytes) |
| SHA-256 | `df4455861a67fd683a0ab44b0f461b889624b513738b7cbb6c0ea3adc033a2ed` |
| Notebook | [`train_dental_yolov8s.ipynb`](train_dental_yolov8s.ipynb) (outputs stripped) |
| Inference path | **Not yet wired** — tracked in issue #12 / Friday checkpoint |
| Metrics | Reported below; notebook outputs were stripped, so re-run to reproduce |

## Class taxonomy (authoritative)

The final checkpoint is a **5-class** model. The 7-class mapping at the top of the
notebook was the earlier DENTEX attempt and does **not** describe this checkpoint.

| ID | Class | Source dataset |
| --- | --- | --- |
| 0 | `Inter-Radicular` | Tufts Dental Database |
| 1 | `Non-Odontogenic` | Tufts Dental Database |
| 2 | `Periapical` | Tufts Dental Database |
| 3 | `Pericoronal` | Tufts Dental Database |
| 4 | `Caries` | Loki Silvres (lesion-level boxes) |

**DENTEX was purged from training entirely.** Its boxes were tooth-level rather than
lesion-level, so YOLO treated actual decay as background — Cavities sat at 0% recall
until DENTEX was removed.

This list is the reference for the model↔backend taxonomy reconciliation in issue #28.

## Datasets

- **Tufts Dental Database** — `expert.json` polygon annotations, mapped to classes 0–3
- **Loki Silvres** — YOLO-format labels; only class `0` (Caries) kept and remapped to unified class `4`
- **DENTEX Challenge 2023** — used in early attempts, **removed**; do not reintroduce without re-checking box granularity

Split is 80/10/10 (train/val/test) with `random.seed(42)`.

## Training pipeline

Two-phase strategy against a unified clean dataset (`unified_clean_dataset`):

1. **Phase 1** — `yolov8s.pt` base, 60 epochs, `imgsz=1024`, `batch=16`, `mosaic=0.5`,
   `mixup=0.0`, `patience=20`. Broke the 0% recall plateau → **Caries recall 60.0%**.
2. **Phase 2** — fine-tune from Phase 1 checkpoint, 35 epochs, `patience=0`,
   `lr0=0.002`, `lrf=0.01`, `mosaic=0.0` (train at native tooth scale).

Final run directory: `dental_clean_tufts_loki_p2`.

## Reported results (Phase 2 checkpoint)

| Metric | Value |
| --- | --- |
| Caries Recall | 66.7% |
| Caries mAP@0.5 | 64.8% |
| Caries Precision | 0.555 |
| Overall mAP@0.5 (5-class) | 38.0% |

These come from the original training logs. Notebook outputs were stripped to shrink the
file, so re-running the notebook reproduces them from scratch.

## Inference (once wired)

```python
from ultralytics import YOLO

model = YOLO("best.pt")          # download from the Release
results = model.predict("panoramic.png", imgsz=1024, conf=0.25)
for r in results:
    for box in r.boxes:
        cls = int(box.cls[0])
        print(model.names[cls], float(box.conf[0]))
```

There is currently **no `predict.py`, ONNX export, or FastAPI inference endpoint** —
the API still runs the placeholder `FindingTypeEnum`. See issue #12 and #15/#17.

## Reproducing

The notebook targets **Kaggle** (`/kaggle/input`, `/kaggle/working`) and expects the
Tufts + Loki + DENTEX datasets mounted as inputs. To run it locally you would need to
repoint `BASE_DIR` and the dataset discovery paths. Output cell counts: 14 cells,
all outputs cleared.
