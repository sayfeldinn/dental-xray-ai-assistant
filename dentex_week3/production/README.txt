DENTEX PRODUCTION PIPELINE (v3)
===============================

ARCHITECTURE
------------
Panorama
  -> tooth detector   (yolov8s, 32 FDI classes, 1024 px)  -> tooth boxes + numbers
  -> disease detector (yolov8s, 4 classes, 1024 px)       -> lesion boxes + labels
  -> association: IoU -> centre containment -> nearest centre
  -> disease + FDI tooth

Advisory only (never in the clinical report):
  -> missing teeth: interior FDI gaps, checked by a ResNet18 gap classifier
  -> findings detector (yolov8s, 11 classes: fillings, crowns, RCT, ...)

FILES
-----
tooth_best.pt          32-class tooth detector
disease_best.pt        4-class disease detector (DENTEX + OralXrays-9)
findings_best.pt       11-class advisory findings detector (DentalOPG)
missing_teeth.pt       ResNet18 gap-vs-tooth classifier
weights.sha256         checksums of the exact files scored below
pipeline_config.json   class maps, thresholds, training provenance
final_evaluation.json  locked-set benchmark summary
inference_pipeline.py  run_dentex_pipeline(image, confidence_threshold=None)

The .pt files are not in git. Install them with
    ./notebooks/fetch_release_weights.sh
then check them with
    cd dentex_week3/production && shasum -a 256 -c weights.sha256

LOCKED BENCHMARK
----------------
Official DENTEX validation set: 50 panoramas, 182 lesions, never used for
training or model selection. Scored with dentex_week3/evaluate.py.

Tooth number (on found lesions):     91.7%
Disease label (on found lesions):    89.0%
Tooth + disease:                     82.8%
Lesions found (recall, conf 0.20):   74.2%
Precision (conf 0.20):               44.6%
mAP@0.5:                             54.2%
Caries AP@0.5 (weakest class):       35.3%

Re-run on a different machine, the same weights reproduce the label
accuracies exactly; mAP moves by under 1 pp from GPU/CPU float differences.

IMPORTANT
---------
Confidence values are detector scores, not calibrated clinical
probabilities. Roughly half the boxes at the default threshold are false
positives, which is why every finding requires dentist confirmation.
