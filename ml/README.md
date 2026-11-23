# ML service — DENTEX v3 pipeline

Inference, evaluation and evidence for the shipped DentalAI detector.

## Layout

| Path | Contents |
| --- | --- |
| `pipeline/inference.py` | Frozen v3 pipeline: `run_dentex_pipeline(image, confidence_threshold=None)` |
| `pipeline/pipeline_config.json` | Class maps, thresholds, training provenance |
| `weights/` | `*.pt` checkpoints + `weights.sha256` (gitignored, fetched from the release) |
| `service/` | FastAPI wrapper on `:8001` (`app.py`, `start.sh`, `requirements.txt`) |
| `eval/evaluate.py` | **The judge.** Locked-50 benchmark, mAP/AR, Wilson CIs |
| `eval/significance.py` | Paired bootstrap significance between two cached prediction sets |
| `eval/*.json`, `eval/*.md` | Generated evidence — cited by `submission/VERIFICATION.md` |
| `research/` | One-off studies (caries rerank/threshold, missing teeth, gap rules) |
| `tools/verify_setup.py` | Environment and weights sanity check |
| `tests/` | Unit tests (torch stubbed, CI-safe) |

## Architecture

```
Panorama
  -> tooth detector   (yolov8s, 32 FDI classes, 1024 px)  -> tooth boxes + numbers
  -> disease detector (yolov8s, 4 classes, 1024 px)       -> lesion boxes + labels
  -> association: IoU -> centre containment -> nearest centre
  -> disease + FDI tooth

Advisory only (never in the clinical report):
  -> missing teeth: interior FDI gaps, checked by a ResNet18 gap classifier
  -> findings detector (yolov8s, 11 classes: fillings, crowns, RCT, ...)
```

## Weights

The `.pt` files are **not** in git. Install and verify them with:

```bash
./notebooks/fetch_release_weights.sh   # downloads into ml/weights/ and checks sha256
```

## Locked benchmark

Official DENTEX validation set: 50 panoramas, 182 lesions, never used for
training or model selection. Scored with `ml/eval/evaluate.py`.

| Metric | Value |
| --- | --- |
| Tooth number (on matched lesions) | 91.7% |
| Disease label (on matched lesions) | 89.0% |
| Tooth + disease (joint) | 82.8% |
| Lesion recall (conf 0.20) | 74.2% |
| Precision (conf 0.20) | 44.6% |
| mAP@0.5 | 54.2% |
| Caries AP@0.5 (weakest class) | 35.3% |

Re-running with the same weights reproduces these numbers; the full report,
per-class AP and confidence intervals are in `eval/evaluation_report_v3.md`.
