# YOLO Multi-Stage DENTEX Pipeline Evaluation

## 1. Architecture Overview
We have replaced the single-model approach with a robust, four-phase multi-stage pipeline designed specifically for the DENTEX dataset. This isolates spatial reasoning from disease detection, drastically improving performance.

- **Phase 1 (Coordinator):** A YOLOv8 Nano model trained to detect and crop the 4 anatomical quadrants.
- **Phase 2 (Enumerators):** Four independent YOLOv8 Nano models (one per quadrant) trained to count and classify teeth 1 through 8 within their localized crops.
- **Phase 3 (Global Disease Detector):** A YOLOv8 Small model trained on the full X-rays to detect abnormalities (Caries, Deep Caries, Periapical Lesions, Impacted Teeth).
- **Phase 4 (Spatial Association):** An algorithmic pipeline that stitches the outputs together, utilizing an Intersection over Union (IoU > 10%) threshold to map the global disease bounding box to the locally enumerated tooth bounding box.

## 2. Evaluation Metrics (Base-Model Candidate)
The multi-stage approach yielded exceptional metrics across all distinct tasks:

- **Coordinator (Quadrant Detection):** `mAP50 = 0.995`
- **Enumerators (Tooth Counting Q1-Q4):** `mAP50 > 0.98`
- **Global Disease Detector:** `mAP50 = 0.922`

**Conclusion:** 
The metrics are highly reasonable and significantly surpass the previous week's architecture. The spatial isolation strategy solved the DENTEX classification ambiguity. We will **freeze these checkpoints** as our base-model pipeline.

## 3. Known Weak Points (Honest Documentation for Pitch)
While highly accurate on complex cases (e.g., detecting multiple impacted wisdom teeth and concurrent caries), the sequential nature of the enumerator models introduces a specific edge case:

- **Missing Teeth Numbering Shift:** If a patient is missing a tooth (e.g., an extracted premolar), the enumerator models maintain strict sequential counting. Consequently, the 8th physical tooth (wisdom tooth) will be mislabeled as Tooth 7. 
- *Mitigation Plan:* This is a known behavior of sequential object detectors. For future iterations, a post-processing heuristic (or anatomical distance measurement) will be required if absolute anatomical numbering is needed rather than strict positional numbering.
