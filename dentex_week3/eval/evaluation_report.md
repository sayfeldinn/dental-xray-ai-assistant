# Shipped DENTEX pipeline — held-out evaluation

Official DENTEX **validation** split (50 panoramas / 182 lesions), which the models never saw in training (all `model.train()` runs used `training_data/` only; see `MLv2/provenance/*/args.yaml`). Ground truth is the full quadrant + tooth + disease triple from `validation_triple.json`. Predictions are the frozen production pipeline (`production/inference_pipeline.py`, conf=0.20) served by the ML service.

- images scored: **50/50**
- ground-truth lesions: **182** · model predictions: **252**
- matching: greedy one-to-one by descending IoU at IoU ≥ 0.5

## 1. Detection quality (per disease class, IoU ≥ 0.5)

| class | GT | pred | precision (95% CI) | recall (95% CI) | F1 | AP@0.5 |
|---|---|---|---|---|---|---|
| Impacted | 40 | 48 | 75.0% [61.2%, 85.1%] | 90.0% [76.9%, 96.0%] | 81.8% | 75.0% |
| Caries | 101 | 163 | 28.2% [21.9%, 35.6%] | 45.5% [36.2%, 55.2%] | 34.8% | 28.2% |
| Periapical Lesion | 9 | 7 | 42.9% [15.8%, 75.0%] | 33.3% [12.1%, 64.6%] | 37.5% | 42.9% |
| Deep Caries | 32 | 34 | 52.9% [36.7%, 68.5%] | 56.2% [39.3%, 71.8%] | 54.5% | 52.9% |
| **micro avg** | 182 | 252 | 40.9% [35.0%, 47.0%] | 56.6% [49.3%, 63.6%] | 47.5% | 49.8% |

**mAP@0.5 = 49.8% · mAP@0.5:0.95 = 33.6%**

## 2. Label accuracy on matched lesions (IoU ≥ 0.5, any label)

This is the metric family of the original `final_evaluation.json` (disease / tooth / joint), now on a reproducible 182-lesion set with CIs.

| metric | rate (95% CI) | correct / total |
|---|---|---|
| disease label | **83.6%** [75.8%, 89.3%] | 97 / 116 |
| tooth number | **75.9%** [67.3%, 82.7%] | 88 / 116 |
| quadrant | **99.1%** [95.3%, 99.8%] | 115 / 116 |
| disease **and** tooth | **66.4%** [57.4%, 74.3%] | 77 / 116 |

### Disease confusion matrix (rows = ground truth, cols = prediction)

| GT \ pred | Impacted | Caries | Periapical Lesion | Deep Caries |
|---|---|---|---|---|
| **Impacted** | 36 | 0 | 0 | 0 |
| **Caries** | 1 | 43 | 0 | 6 |
| **Periapical Lesion** | 0 | 4 | 2 | 1 |
| **Deep Caries** | 0 | 7 | 0 | 16 |

## 3. Tooth accuracy per quadrant

| quadrant | tooth acc (95% CI) | joint (95% CI) | n |
|---|---|---|---|
| Q1 | 70.4% [51.5%, 84.1%] | 63.0% [44.2%, 78.5%] | 27 |
| Q2 | 76.2% [54.9%, 89.4%] | 71.4% [50.0%, 86.2%] | 21 |
| Q3 | 78.4% [62.8%, 88.6%] | 64.9% [48.8%, 78.2%] | 37 |
| Q4 | 77.4% [60.2%, 88.6%] | 67.7% [50.1%, 81.4%] | 31 |

## 4. Confidence-threshold sweep (disease detector)

The pipeline bakes in conf=0.20; higher thresholds can be applied by filtering returned detections (identical to raising the threshold). Values below 0.20 are unreachable without re-running the model.

| threshold | precision | recall | F1 | disease acc on matches (95% CI) | n |
|---|---|---|---|---|---|
| 0.20 | 40.9% | 56.6% | 47.5% | 83.6% [75.8%, 89.3%] | 116 |
| 0.25 | 44.1% | 53.8% | 48.5% | 84.5% [76.6%, 90.1%] | 110 |
| 0.30 | 47.5% | 51.6% | 49.5% | 84.8% [76.7%, 90.4%] | 105 |
| 0.40 | 57.1% | 48.9% | 52.7% | 86.7% [78.6%, 92.1%] | 98 |
| 0.50 | 59.8% | 43.4% | 50.3% | 85.2% [76.3%, 91.2%] | 88 |

---

Regenerate with `python dentex_week3/evaluate.py` (see its docstring). Confidence intervals are 95% Wilson score intervals.
