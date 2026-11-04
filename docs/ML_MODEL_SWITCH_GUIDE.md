# ML Model Guide: dentex_week3 (v3)

> **Current models as of 2026-11-03.** The disease detector is v3, trained on
> 9,848 unique panoramas (DENTEX + OralXrays). v2 is archived in
> `archive/ml-v2/`, and the v1 coordinator + random-forest pipeline in
> `archive/ml-v1/` (tag `ml-v1-baseline`). A Romanian-augmented v4 was trained
> and rejected on 2026-11-04 (it lost Caries, tooth and joint accuracy on the
> locked 50); see "Candidate v4" below. `notebooks/README.md` covers training
> and `dentex_week3/eval/evaluation_report_v3.md` has the full benchmark.

## Overview

The shipped pipeline is two clinical YOLO detectors joined by geometric
association, plus an advisory findings model:

```
panorama
  ├─ tooth detector   (32 classes, one per FDI tooth)   -> tooth boxes + numbers
  ├─ disease detector (4 classes)                        -> lesion boxes + labels
  │           └─ association: IoU -> containment -> nearest centre
  └─ findings detector (11 classes, advisory)            -> /predict + /findings
```

Both models are `yolov8s`, trained at 1024 px. The tooth detector labels every
tooth directly, which is what removed the old coordinator + random forest: v1
detected four quadrant boxes and then *guessed* the tooth number from lesion
geometry.

The tooth detector is unchanged from v2 (540 training panoramas). The disease
detector is v3: the same `yolov8s` / 1024 px recipe as v2, retrained on 9,848
unique images with 4 classes (caries, deep caries, periapical, impacted).

## What changed from v1

| | v1 | v2 |
|---|---|---|
| Tooth identification | quadrant coordinator + random forest | 32-class detector |
| Disease detector input | cropped quadrants | full panorama |
| Inference resolution | 416 px | 1024 px |
| Class imbalance | unhandled (13.9:1) | image oversampling (7.0:1) |
| Models in `production/` | 3 (`.pt` + `.joblib`) | 2 (`.pt`) |
| Training notebooks | ad hoc, validated on training data | reproducible 00-05 with a locked split |

## Model files

| File | Size | Purpose |
|---|---|---|
| `production/tooth_best.pt` | ~22 MB | 32 FDI classes, `imgsz=1024`, `conf=0.25` |
| `production/disease_best.pt` | ~22 MB | 4 disease classes, `imgsz=1024`, `conf=0.20` |
| `production/findings_best.pt` | ~22 MB | 11 advisory findings classes, `imgsz=640`, `conf=0.40` |
| `production/pipeline_config.json` | small | class maps, thresholds, training provenance |

Weights are **not committed** (gitignored). Fetch them with:

```bash
KAGGLE_BIN=~/.local/bin/kaggle ./notebooks/fetch_weights.sh
KAGGLE_BIN=~/.local/bin/kaggle ./notebooks/fetch_findings.sh   # advisory model
```

`inference_pipeline.py` loads each model lazily on first use, so the API starts
even if one weight file is missing; the error then surfaces on `/predict`.

## Configuration

### Backend environment variables (`backend/.env`)

```env
ML_API_URL=http://localhost:8001
ML_TIMEOUT_SECONDS=60
ML_ALLOW_MOCK_FALLBACK=true
ML_DEFAULT_CONFIDENCE=0.2
```

### Port

The ML service runs on **8001** so it does not collide with the backend:

```bash
cd dentex_week3/api
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | health check (`models_loaded`) |
| `POST` | `/predict` | multipart image -> detections + quadrant boxes + report |
| `POST` | `/findings` | advisory findings: missing teeth, BDR, fillings, crowns, ... |
| `POST` | `/feedback/finding` | dentist correction for a single finding |
| `POST` | `/feedback/report` | accept / edit a generated report |

`/predict` returns the v1-compatible contract, so the backend needs no changes:

```json
{
  "image_width": 2872,
  "image_height": 1504,
  "quadrants": [{"quadrant": 1, "confidence": 0.93, "box": [x1, y1, x2, y2]}],
  "detections": [{
    "quadrant": 4, "tooth_id": 7, "tooth": "Tooth_7", "tooth_fdi": "47",
    "tooth_confidence": 0.88,
    "disease": "Caries", "disease_id": 1, "disease_confidence": 0.94,
    "association_confidence": 0.83,
    "box": [x1, y1, x2, y2]
  }],
  "num_detections": 8,
  "model": {"tooth": "tooth_best.pt", "disease": "disease_best.pt",
            "architecture": "tooth_detector+disease_detector",
            "findings": "findings_best.pt"},
  "findings": [{
    "finding_id": 6, "finding": "Missing Teeth", "confidence": 0.72,
    "box": [x1, y1, x2, y2]
  }],
  "findings_advisory": true,
  "ai_generated_report": "..."
}
```

`quadrants` is now **derived** from the tooth boxes (union per FDI quadrant)
rather than produced by a coordinator model.

`findings` is the advisory DentalOPG layer (see below); it never feeds the
clinical report. Set `"findings_in_predict": false` in `pipeline_config.json`
to omit it from `/predict`.

## Setup and testing

```bash
# 1. weights
ls -lh dentex_week3/production/*.pt      # tooth, disease, findings

# 2. dependencies
cd dentex_week3/api
pip install -r requirements.txt

# 3. verify everything
cd ..
python verify_setup.py

# 4. start
cd api && uvicorn app:app --host 0.0.0.0 --port 8001 --reload

# 5. smoke test
curl -X POST http://localhost:8001/predict -F "file=@/path/to/panorama.png"
```

## Disease mapping

| id | name |
|---|---|
| 0 | Impacted |
| 1 | Caries |
| 2 | Periapical Lesion |
| 3 | Deep Caries |

This is identical to the DENTEX `category_id_3` order and to
`pipeline_config.json`, so no remapping is needed anywhere in the stack.

## Findings layer (advisory)

`production/findings_best.pt` is a separate 11-class detector for what the
DENTEX taxonomy does not cover: missing teeth, BDR, fillings, crowns, root
canals, bridges, impacted/unerupted teeth, periapical abscess and
periodontitis. It is appended to `/predict` as an advisory `findings` list
(and is also available on its own `POST /findings` endpoint), but it never
feeds the clinical report.

| Split | Images | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|---|
| DentalOPG val | 303 | 61.9% | 25.1% |
| DentalOPG test (held out) | 154 | 59.4% | 24.9% |

Per-class test AP@0.5: Bridge 99.5%, Cap 94.7%, Unerupted Wisdom 78.3%,
Horizontal Impaction 67.6%, Missing Teeth 65.4%, Periodontitis 55.5%,
BDR 53.8%, Filling 50.9%, Apical Abscess 31.3%, Root Canal 28.1%,
Distoangular Impaction 28.0%.

The model is trained in `notebooks/08_train_findings_detector.ipynb` on
DentalOPG 1550 (1,068 train / 303 val / 154 test, 640 px). Caries is excluded
because the DENTEX detector already owns it, and "Normal Teeth" is excluded
because its 5,076 boxes would teach the model to box every tooth.

**Domain caveat.** DentalOPG is a different hospital population at 640×640.
On the locked DENTEX 50 the model produces tooth-sized, anatomically plausible
boxes, but there is no DENTEX ground truth for these findings, so accuracy
there is unknown. A cross-hospital check on the Romanian external split
(Zenodo 15487430, 176 images), mapping each Romanian class to its nearest
DentalOPG equivalent, scored mAP@0.5 11.8% (horizontal impaction 31.7%, root
canal 23.1%, filling 9.9%, cap 6.0%, periodontitis and apical abscess 0). The Romanian restoration and
endodontic boxes are lesion-level while DentalOPG's are tooth-level, so this
is a lower bound rather than a like-for-like score; it nonetheless shows the
model does not transfer to a new hospital without re-annotation. That is why
the response carries `"advisory": true`, why it is not merged into the
diagnosis path, and why it must not be presented as a diagnosis until it is
validated on an external labelled set with matching box definitions.

## Tooth numbering

The tooth detector's class index maps to FDI as:

```python
quadrant = index // 8 + 1     # 1-4
tooth    = index % 8 + 1      # 1-8
fdi      = f"{quadrant}{tooth}"
```

Class 0 = FDI 11 (upper-right central incisor) ... class 31 = FDI 48
(lower-right third molar).

**Do not flip images** when training or augmenting the tooth detector: FDI
labels are position-dependent, so a mirrored panorama would swap quadrants
while the label stays the same. The training notebook disables `fliplr`,
`flipud` and `mosaic` for exactly this reason.

## Performance

Locked official DENTEX validation set (50 panoramas / 182 lesions), scored with
`dentex_week3/evaluate.py`:

| Metric | v1 | v2 | v3 |
|---|---|---|---|
| mAP@0.5 | 49.8% | 51.7% | **54.2%** |
| mAP@0.5:0.95 | 33.6% | 37.5% | **38.2%** |
| Precision | 40.9% | 43.0% | **44.6%** |
| Recall | 56.6% | 64.3% | **74.2%** |
| Disease accuracy | 83.6% | 87.7% | **89.0%** |
| Tooth accuracy | 75.9% | 91.5% | **91.7%** |
| Quadrant accuracy | 99.1% | 100.0% | **100.0%** |
| Joint accuracy | 66.4% | 80.0% | **82.8%** |

Both v2 and v3 are scored with class-agnostic tooth-box dedup at IoU 0.6
(`tooth_nms_iou`). Without it, YOLO's per-class NMS keeps two class hypotheses
for the same tooth and v2 scores 89.2% tooth / 78.5% joint.

Per-class AP@0.5 (v3): Impacted 75.0%, Caries 35.3%, Periapical Lesion 55.6%,
Deep Caries 51.1%. The 36× increase in periapical boxes moved that class
37.5% -> 55.6% (+18.1 pp), which is the main win of v3. Deep Caries fell
59.3% -> 51.1% because OralXrays labels deep lesions simply as caries, so the
model now prefers the broader label; the lesion box is still found. Caries
remains the weakest clinically important class.

### How much of this is noise?

`dentex_week3/paired_significance.py` re-analyses the same two prediction files
with paired statistics (McNemar exact test per lesion, plus a bootstrap that
resamples the 50 panoramas). Results in
`dentex_week3/eval/paired_significance.md`. Summary:

| metric | delta | 95% CI | verdict |
|---|---|---|---|
| tooth (end-to-end) | +17.0 pp | [+7.0, +28.3] | **significant** (McNemar p=0.0002) |
| joint (end-to-end) | +14.8 pp | [+5.4, +24.7] | **significant** (p=0.0009) |
| recall | +7.7 pp | [+0.0, +15.4] | borderline |
| mAP@0.5 | +2.0 pp | [-11.4, +11.1] | **not significant** |
| Caries AP@0.5 | +5.1 pp | [-2.0, +12.1] | suggestive, not significant |
| Periapical AP@0.5 | -5.4 pp | [-60.0, +20.5] | indistinguishable from noise |

#### v2 vs v3

`dentex_week3/eval/paired_significance_v2_v3.md`:

| metric | delta | 95% CI | verdict |
|---|---|---|---|
| recall | +9.9 pp | [+4.5, +15.8] | **significant** (McNemar p=0.003) |
| tooth (end-to-end) | +7.7 pp | [+2.7, +13.0] | **significant** (p=0.009) |
| joint (end-to-end) | +8.8 pp | [+2.8, +14.9] | **significant** (p=0.007) |
| mAP@0.5 | +2.5 pp | [-6.9, +12.4] | not significant |
| Caries AP@0.5 | +2.0 pp | [-3.3, +7.3] | not significant |
| Periapical AP@0.5 | +18.1 pp | [-15.7, +51.9] | large but underpowered (n=9) |
| Deep Caries AP@0.5 | -8.1 pp | [-23.8, +7.5] | not significant |

The defensible claim for v2 was: **v2 identifies teeth substantially better and
is not worse at lesion detection.** v3 adds a significant recall gain on top
(+9.9 pp, McNemar p=0.003) and finds more of the lesions that matter, at the
cost of a non-significant Deep Caries regression. Conditioned on detected
lesions, tooth accuracy is essentially tied (91.7% vs 91.5%); v3's end-to-end
tooth gain (+7.7 pp) comes from detecting more lesions, not from better tooth
assignment. The end-to-end rates over all 182 ground-truth lesions are
73.1% / 65.9%, which is the more clinically meaningful number.

### Candidate v4 (rejected, 2026-11-04)

v4 added the Romanian 14-class dataset (Zenodo 15487430) to v3's training mix.
Romanian caries/apical labels are tight lesion boxes, so each was converted to
its smallest containing tooth box with the production tooth detector (99%
containment; converted median area 1.18% vs 1.21% in DENTEX). 1,304 images /
3,738 converted boxes were added, and the DENTEX val split was unchanged.

Validation (107 DENTEX images) improved: mAP@0.5 62.5% -> 65.7%,
mAP@0.5:0.95 41.9% -> 43.4%, Periapical 41.6% -> 51.8%, Caries 52.0% -> 51.7%.
The locked 50 did not:

| Metric | v3 | v4 | Δ |
|---|---|---|---|
| mAP@0.5 | 54.2% | 55.1% | +0.9 |
| mAP@0.5:0.95 | 38.2% | 41.6% | +3.4 |
| Precision | 44.6% | 45.0% | +0.4 |
| Recall | 74.2% | 71.4% | -2.8 |
| Disease accuracy | 89.0% | 86.4% | -2.6 |
| Tooth accuracy | 91.7% | 91.4% | -0.3 |
| Joint accuracy | 82.8% | 78.6% | -4.2 |
| Caries AP@0.5 | 35.3% | 34.2% | -1.1 |
| Periapical AP@0.5 | 55.6% | 50.0% | -5.6 |
| Deep Caries AP@0.5 | 51.1% | 63.6% | +12.5 |

Paired bootstrap: joint -5.5 pp [-11.3, +0.6], P(v4 > v3) = 0.029; Caries
-1.1 pp [-5.9, +3.2], not significant; per-lesion McNemar joint p = 0.076.
v4 improved localisation (mAP@0.5:0.95) and Deep Caries, but became more
conservative (recall -2.8 pp), which costs clinically meaningful joint
accuracy. It fails the promotion rule on Caries, tooth and joint, so v3 stays.

The weights are kept out of `production/`; the run is reproducible with
`notebooks/10_train_pathology_v4.ipynb` and `11_evaluate_v4.ipynb`. This is a
real domain trade-off, not a bug: the same conversion that makes Romanian
boxes DENTEX-shaped also teaches the model a slightly different box scale and
a more conservative confidence profile.

`notebooks/12_cross_hospital.ipynb` adds the external check. On the Romanian
external split (a hospital neither model trained on), the shipped v3 disease
detector scores mAP@0.5 43.3% with tooth-converted GT (Impacted 77.7%,
Periapical 34.6%, Caries 17.7%), and the findings model 11.8% with
class-mapped GT. Neither model transfers to a new hospital without local
re-annotation, which is why the findings layer remains advisory.

### Caries verifier (optional, not promoted, 2026-11-04)

Caries is localised well by v3 (96% of the locked-50 caries are hit at IoU 0.5)
but ranked poorly (35% precision). A binary ResNet18 was trained on
**tooth crops** to score each caries detection: positives are teeth containing
caries/deep caries; negatives are healthy teeth plus Romanian restoration teeth
(`OBT`/`END`/`PRR`) as hard negatives. Held-out DENTEX val AUC 0.843
(`notebooks/13_train_caries_verifier.ipynb`).

It is used as a **gate**: Caries / Deep Caries detections whose crop score is
below a threshold are dropped. The threshold (0.9) was chosen on the held-out
107-image DENTEX split, never on the locked 50.

| Metric | v3 | gate 0.7 | gate 0.9 |
|---|---|---|---|
| mAP@0.5 | 54.2% | 56.8% | **59.6%** |
| mAP@0.5:0.95 | 38.2% | 40.1% | **42.8%** |
| Precision | 44.6% | – | **54.7%** |
| Recall | 74.2% | 72.5% | 70.3% |
| Caries AP@0.5 | 35.3% | 39.1% | **46.2%** |
| Caries precision | 35.3% | 39.1% | **46.2%** |
| Caries recall | 70.3% | 67.3% | 65.3% |
| Deep Caries AP@0.5 | 51.1% | 57.5% | **61.8%** |
| Disease accuracy | 89.0% | 90.6% | **91.1%** |
| Tooth accuracy | **91.7%** | 91.4% | 91.1% |
| Joint accuracy | 82.8% | 84.2% | **84.4%** |

Paired over the 50 images, mAP (+5.4 pp [+3.1, +8.4]) and Caries AP
(+10.8 pp [+6.7, +15.3]) improve **significantly**, but recall (−3.8 pp) and
end-to-end tooth (−5.5 pp) and joint (−3.3 pp) drop **significantly**. The gate
trades recall for precision; it raises AP, which rewards a clean top of the
ranking, but removes real detections.

Per the promotion rule it does not ship: it does not beat v3 on tooth accuracy
(91.1% vs 91.7%, conditioned on matched lesions) and the more clinically
meaningful end-to-end joint falls. The code is wired but **off by default**
(`caries_verifier.enabled = false` in `pipeline_config.json`). To try it::

    ./notebooks/fetch_caries_verifier.sh
    DENTEX_CARIES_VERIFIER=/tmp/opencode/kaggle_out_verifier/caries_verifier.pt:gate:0.7 \
      python dentex_week3/evaluate.py --local --images-dir ... --gt ...

`mode: "scale"` (confidence `*= p^alpha`) is also supported but does not change
AP, because it preserves the confidence ordering.

### Inference time

Measured on CPU (16-core) with `imgsz=1024`: ~0.25 s per image per model,
~0.5 s for the full pipeline. On a T4 the detectors run at ~15 ms each.

## Troubleshooting

### "Models not loaded"

`models_loaded` is set at import time. If it is `False`, the module itself
failed to import — usually a missing `ultralytics`. Check:

```bash
python -c "import ultralytics; print(ultralytics.__version__)"
```

Missing weights do **not** set `models_loaded=False` (loading is lazy); they
raise on the first `/predict` instead.

### "No module named 'ultralytics'"

```bash
pip install -r dentex_week3/api/requirements.txt
```

### Port already in use

```bash
lsof -i :8001
```

### Slow inference

Check the device actually used:

```python
import torch; print(torch.cuda.is_available())
```

CPU inference is ~0.5 s per panorama, which is fine for the review UI but not
for batch processing.

### Path errors

All model paths in `pipeline_config.json` must stay **relative**
(`tooth_best.pt`, not `D:/.../tooth_best.pt`); `inference_pipeline.py` joins
them with its own directory.

## Retraining

See `notebooks/README.md`. Short version:

1. `02_prepare_dataset.ipynb` rebuilds the DENTEX split locally (seed 42).
2. `03` / `04` train the tooth and DENTEX-only disease detectors on Kaggle.
3. `06_train_pathology_v3.ipynb` adds OralXrays and trains the v3 disease
   detector; `./notebooks/fetch_v3.sh` pulls the run without touching
   `production/`.
4. `07_evaluate_v3.ipynb` scores a candidate on the locked 50, writes
   `evaluation_report_v3.md`, and runs the paired significance test.

Promotion rule: a new model ships only if it beats the incumbent on mAP@0.5,
Caries AP@0.5, tooth accuracy and joint accuracy on the locked set.
