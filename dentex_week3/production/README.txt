DENTEX PRODUCTION PIPELINE
============================

Frozen production configuration.

FINAL UNTOUCHED BENCHMARK
-------------------------
Held-out images:       23
Held-out detections:   122

Disease accuracy:      97.54%
Tooth accuracy:        76.23%
Disease + tooth:       75.41%

ARCHITECTURE
------------
Panorama
  -> Coordinator
  -> Quadrants
  -> Disease detector
  -> RF tooth association
  -> Disease + tooth

The enumerator is NOT used in the final pipeline.

FILES
-----
tooth_association_rf_300.joblib
    Frozen Step 51 RF tooth-association model.

pipeline_config.json
    Model paths, mappings, feature contract and benchmark.

final_evaluation.json
    Final untouched evaluation record.

inference_pipeline.py
    Standalone inference wrapper.

USAGE
-----
from inference_pipeline import run_dentex_pipeline

result = run_dentex_pipeline(
    "/path/to/panorama.png"
)

The coordinator and disease detector paths in
pipeline_config.json point to the Kaggle model
artifacts used during validation.

IMPORTANT
---------
The reported 75.41% figure is the empirical
untouched held-out disease+tooth accuracy.
Confidence values produced by the RF are model
probabilities and are not calibrated clinical
probabilities.
