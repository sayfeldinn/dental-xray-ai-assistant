# Shipped DENTEX pipeline — held-out evaluation

Official DENTEX **validation** split (50 panoramas / 182 lesions), which the models never saw in training (all `model.train()` runs used `training_data/` only; see `MLv2/provenance/*/args.yaml`). Ground truth is the full quadrant + tooth + disease triple from `validation_triple.json`. Predictions are the frozen production pipeline (`production/inference_pipeline.py`, conf=0.20) served by the ML service.

- images scored: **50/50**
- ground-truth lesions: **182** · model predictions: **303**
- matching: greedy one-to-one by descending IoU at IoU ≥ 0.5

## 1. Detection quality (per disease class, IoU ≥ 0.5)

| class | GT | pred | precision (95% CI) | recall (95% CI) | F1 | AP@0.5 |
|---|---|---|---|---|---|---|
| Impacted | 40 | 48 | 75.0% [61.2%, 85.1%] | 90.0% [76.9%, 96.0%] | 81.8% | 75.0% |
| Caries | 101 | 201 | 35.3% [29.0%, 42.2%] | 70.3% [60.8%, 78.3%] | 47.0% | 35.3% |
| Periapical Lesion | 9 | 9 | 55.6% [26.7%, 81.1%] | 55.6% [26.7%, 81.1%] | 55.6% | 55.6% |
| Deep Caries | 32 | 45 | 51.1% [37.0%, 65.0%] | 71.9% [54.6%, 84.4%] | 59.7% | 51.1% |
| **micro avg** | 182 | 303 | 44.6% [39.1%, 50.2%] | 74.2% [67.4%, 80.0%] | 55.7% | 54.2% |

**mAP@0.5 = 54.2% · mAP@0.5:0.95 = 38.2%**

## 2. Label accuracy on matched lesions (IoU ≥ 0.5, any label)

This is the metric family of the original `final_evaluation.json` (disease / tooth / joint), now on a reproducible 182-lesion set with CIs.

| metric | rate (95% CI) | correct / total |
|---|---|---|
| disease label | **89.0%** [82.8%, 93.1%] | 129 / 145 |
| tooth number | **91.7%** [86.1%, 95.2%] | 133 / 145 |
| quadrant | **100.0%** [97.4%, 100.0%] | 145 / 145 |
| disease **and** tooth | **82.8%** [75.8%, 88.0%] | 120 / 145 |

### Disease confusion matrix (rows = ground truth, cols = prediction)

| GT \ pred | Impacted | Caries | Periapical Lesion | Deep Caries |
|---|---|---|---|---|
| **Impacted** | 36 | 0 | 0 | 2 |
| **Caries** | 0 | 68 | 0 | 5 |
| **Periapical Lesion** | 0 | 2 | 5 | 0 |
| **Deep Caries** | 0 | 6 | 1 | 20 |

## 3. Tooth accuracy per quadrant

| quadrant | tooth acc (95% CI) | joint (95% CI) | n |
|---|---|---|---|
| Q1 | 82.4% [66.5%, 91.7%] | 73.5% [56.9%, 85.4%] | 34 |
| Q2 | 89.7% [73.6%, 96.4%] | 82.8% [65.5%, 92.4%] | 29 |
| Q3 | 100.0% [92.3%, 100.0%] | 93.5% [82.5%, 97.8%] | 46 |
| Q4 | 91.7% [78.2%, 97.1%] | 77.8% [61.9%, 88.3%] | 36 |

## 4. Confidence-threshold sweep (disease detector)

The pipeline bakes in conf=0.20; higher thresholds can be applied by filtering returned detections (identical to raising the threshold). Values below 0.20 are unreachable without re-running the model.

| threshold | precision | recall | F1 | disease acc on matches (95% CI) | n |
|---|---|---|---|---|---|
| 0.20 | 44.6% | 74.2% | 55.7% | 89.0% [82.8%, 93.1%] | 145 |
| 0.25 | 48.2% | 73.6% | 58.3% | 88.9% [82.7%, 93.0%] | 144 |
| 0.30 | 51.4% | 69.2% | 59.0% | 88.9% [82.5%, 93.2%] | 135 |
| 0.40 | 61.5% | 64.8% | 63.1% | 91.3% [85.0%, 95.1%] | 126 |
| 0.50 | 68.0% | 57.1% | 62.1% | 92.7% [86.3%, 96.3%] | 110 |

---

Regenerate with `python dentex_week3/evaluate.py` (see its docstring). Confidence intervals are 95% Wilson score intervals.
