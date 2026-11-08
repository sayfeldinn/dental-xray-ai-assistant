# Shipped DENTEX pipeline — held-out evaluation

Official DENTEX **validation** split (50 panoramas / 182 lesions), which the models never saw in training (all `model.train()` runs used `training_data/` only; see `MLv2/provenance/*/args.yaml`). Ground truth is the full quadrant + tooth + disease triple from `validation_triple.json`. Predictions are the frozen production pipeline (`production/inference_pipeline.py`, conf=0.20) served by the ML service.

- images scored: **50/50**
- ground-truth lesions: **182** · model predictions: **289**
- matching: greedy one-to-one by descending IoU at IoU ≥ 0.5

## 1. Detection quality (per disease class, IoU ≥ 0.5)

| class | GT | pred | precision (95% CI) | recall (95% CI) | F1 | AP@0.5 |
|---|---|---|---|---|---|---|
| Impacted | 40 | 51 | 72.5% [59.1%, 82.9%] | 92.5% [80.1%, 97.4%] | 81.3% | 72.5% |
| Caries | 101 | 193 | 34.2% [27.9%, 41.1%] | 65.3% [55.7%, 73.9%] | 44.9% | 34.2% |
| Periapical Lesion | 9 | 12 | 50.0% [25.4%, 74.6%] | 66.7% [35.4%, 87.9%] | 57.1% | 50.0% |
| Deep Caries | 32 | 33 | 63.6% [46.6%, 77.8%] | 65.6% [48.3%, 79.6%] | 64.6% | 63.6% |
| **micro avg** | 182 | 289 | 45.0% [39.4%, 50.7%] | 71.4% [64.5%, 77.5%] | 55.2% | 55.1% |

**mAP@0.5 = 55.1% · mAP@0.5:0.95 = 41.6%**

## 2. Label accuracy on matched lesions (IoU ≥ 0.5, any label)

This is the metric family of the original `final_evaluation.json` (disease / tooth / joint), now on a reproducible 182-lesion set with CIs.

| metric | rate (95% CI) | correct / total |
|---|---|---|
| disease label | **86.4%** [79.8%, 91.1%] | 121 / 140 |
| tooth number | **91.4%** [85.6%, 95.0%] | 128 / 140 |
| quadrant | **100.0%** [97.3%, 100.0%] | 140 / 140 |
| disease **and** tooth | **78.6%** [71.1%, 84.6%] | 110 / 140 |

### Disease confusion matrix (rows = ground truth, cols = prediction)

| GT \ pred | Impacted | Caries | Periapical Lesion | Deep Caries |
|---|---|---|---|---|
| **Impacted** | 37 | 1 | 0 | 0 |
| **Caries** | 0 | 63 | 0 | 4 |
| **Periapical Lesion** | 0 | 2 | 4 | 1 |
| **Deep Caries** | 0 | 9 | 2 | 17 |

## 3. Tooth accuracy per quadrant

| quadrant | tooth acc (95% CI) | joint (95% CI) | n |
|---|---|---|---|
| Q1 | 81.8% [65.6%, 91.4%] | 69.7% [52.7%, 82.6%] | 33 |
| Q2 | 88.9% [71.9%, 96.1%] | 77.8% [59.2%, 89.4%] | 27 |
| Q3 | 100.0% [92.3%, 100.0%] | 82.6% [69.3%, 90.9%] | 46 |
| Q4 | 91.2% [77.0%, 97.0%] | 82.4% [66.5%, 91.7%] | 34 |

## 4. Confidence-threshold sweep (disease detector)

The pipeline bakes in conf=0.20; higher thresholds can be applied by filtering returned detections (identical to raising the threshold). Values below 0.20 are unreachable without re-running the model.

| threshold | precision | recall | F1 | disease acc on matches (95% CI) | n |
|---|---|---|---|---|---|
| 0.20 | 45.0% | 71.4% | 55.2% | 86.4% [79.8%, 91.1%] | 140 |
| 0.25 | 49.0% | 67.6% | 56.8% | 87.0% [80.2%, 91.7%] | 131 |
| 0.30 | 53.6% | 62.1% | 57.5% | 87.5% [80.4%, 92.3%] | 120 |
| 0.40 | 61.9% | 57.1% | 59.4% | 88.3% [81.0%, 93.0%] | 111 |
| 0.50 | 70.2% | 47.8% | 56.9% | 89.2% [81.3%, 94.1%] | 93 |

---

Regenerate with `python dentex_week3/evaluate.py` (see its docstring). Confidence intervals are 95% Wilson score intervals.
