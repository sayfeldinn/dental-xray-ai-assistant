# Shipped DENTEX pipeline — held-out evaluation

Official DENTEX **validation** split (50 panoramas / 182 lesions), which the models never saw in training (all `model.train()` runs used `training_data/` only; see `MLv2/provenance/*/args.yaml`). Ground truth is the full quadrant + tooth + disease triple from `validation_triple.json`. Predictions are the frozen production pipeline (`production/inference_pipeline.py`, conf=0.20) served by the ML service.

- images scored: **50/50**
- ground-truth lesions: **182** · model predictions: **272**
- matching: greedy one-to-one by descending IoU at IoU ≥ 0.5

## 1. Detection quality (per disease class, IoU ≥ 0.5)

| class | GT | pred | precision (95% CI) | recall (95% CI) | F1 | AP@0.5 |
|---|---|---|---|---|---|---|
| Impacted | 40 | 43 | 76.7% [62.3%, 86.8%] | 82.5% [68.0%, 91.3%] | 79.5% | 76.7% |
| Caries | 101 | 186 | 33.3% [27.0%, 40.4%] | 61.4% [51.6%, 70.3%] | 43.2% | 33.3% |
| Periapical Lesion | 9 | 16 | 37.5% [18.5%, 61.4%] | 66.7% [35.4%, 87.9%] | 48.0% | 37.5% |
| Deep Caries | 32 | 27 | 59.3% [40.7%, 75.5%] | 50.0% [33.6%, 66.4%] | 54.2% | 59.3% |
| **micro avg** | 182 | 272 | 43.0% [37.3%, 49.0%] | 64.3% [57.1%, 70.9%] | 51.5% | 51.7% |

**mAP@0.5 = 51.7% · mAP@0.5:0.95 = 37.5%**

## 2. Label accuracy on matched lesions (IoU ≥ 0.5, any label)

This is the metric family of the original `final_evaluation.json` (disease / tooth / joint), now on a reproducible 182-lesion set with CIs.

| metric | rate (95% CI) | correct / total |
|---|---|---|
| disease label | **87.7%** [80.9%, 92.3%] | 114 / 130 |
| tooth number | **89.2%** [82.7%, 93.5%] | 116 / 130 |
| quadrant | **100.0%** [97.1%, 100.0%] | 130 / 130 |
| disease **and** tooth | **78.5%** [70.6%, 84.7%] | 102 / 130 |

### Disease confusion matrix (rows = ground truth, cols = prediction)

| GT \ pred | Impacted | Caries | Periapical Lesion | Deep Caries |
|---|---|---|---|---|
| **Impacted** | 33 | 0 | 0 | 1 |
| **Caries** | 0 | 60 | 1 | 4 |
| **Periapical Lesion** | 0 | 1 | 6 | 0 |
| **Deep Caries** | 0 | 9 | 0 | 15 |

## 3. Tooth accuracy per quadrant

| quadrant | tooth acc (95% CI) | joint (95% CI) | n |
|---|---|---|---|
| Q1 | 76.7% [59.1%, 88.2%] | 66.7% [48.8%, 80.8%] | 30 |
| Q2 | 91.7% [74.2%, 97.7%] | 87.5% [69.0%, 95.7%] | 24 |
| Q3 | 97.7% [87.9%, 99.6%] | 81.4% [67.4%, 90.3%] | 43 |
| Q4 | 87.9% [72.7%, 95.2%] | 78.8% [62.2%, 89.3%] | 33 |

## 4. Confidence-threshold sweep (disease detector)

The pipeline bakes in conf=0.20; higher thresholds can be applied by filtering returned detections (identical to raising the threshold). Values below 0.20 are unreachable without re-running the model.

| threshold | precision | recall | F1 | disease acc on matches (95% CI) | n |
|---|---|---|---|---|---|
| 0.20 | 43.0% | 64.3% | 51.5% | 87.7% [80.9%, 92.3%] | 130 |
| 0.25 | 45.3% | 61.5% | 52.2% | 86.5% [79.5%, 91.4%] | 126 |
| 0.30 | 46.7% | 57.7% | 51.6% | 86.4% [79.1%, 91.5%] | 118 |
| 0.40 | 52.2% | 52.2% | 52.2% | 85.3% [77.5%, 90.8%] | 109 |
| 0.50 | 55.0% | 45.6% | 49.8% | 87.2% [79.0%, 92.5%] | 94 |

---

Regenerate with `python dentex_week3/evaluate.py` (see its docstring). Confidence intervals are 95% Wilson score intervals.
