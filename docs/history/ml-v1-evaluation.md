# YOLO Dental Abnormality Model Evaluation

## 1. Week 1 Training Run Evaluation
**Dataset:** Tufts + DENTEX
**Run:** `dental_yolov8s_run`

**Metrics (Validation):**
- **all:** Precision: 0.488 | Recall: 0.266 | mAP50: 0.271
- **Non-Odontogenic:** Precision: 0.484 | Recall: 0.600 | mAP50: 0.519
- **Periapical:** Precision: 0.663 | Recall: 0.381 | mAP50: 0.425
- **Pericoronal:** Precision: 0.784 | Recall: 0.612 | mAP50: 0.641
- **Caries:** Precision: 0.000 | Recall: 0.000 | mAP50: 0.009
- **Deep Caries:** Precision: 0.000 | Recall: 0.000 | mAP50: 0.031
- **Impacted:** Precision: 1.000 | Recall: 0.000 | mAP50: 0.004

**Weakest Classes:** 
The DENTEX classes (`Caries`, `Deep Caries`, `Impacted`) failed completely, exhibiting 0 recall. This is likely due to extreme class imbalance, conflicting annotation styles between Tufts and DENTEX, or objects being too small to be picked up by the standard augmentation pipeline.

**Concrete Adjustment Executed:**
To address the failing caries detection, we dropped the unharmonized DENTEX dataset and merged in the **Loki Silvres dataset**, focusing specifically on extracting tight Caries bounding boxes (Unified Class 4). We also modified the training schedule to disable `mosaic` augmentation in the final fine-tuning stage to prevent small caries from being distorted or shrunk further.

---

## 2. Final Training Run Evaluation (Base-Model Candidate)
**Dataset:** Tufts + Loki Silvres (Cleaned)
**Run:** `dental_clean_tufts_loki_p2`

**Metrics (Validation):**
- **all:** Precision: 0.544 | Recall: 0.463 | mAP50: 0.380
- **Inter-Radicular:** Precision: 1.000 | Recall: 0.000 | mAP50: 0.100 (1 instance)
- **Non-Odontogenic:** Precision: 0.497 | Recall: 0.450 | mAP50: 0.392
- **Periapical:** Precision: 0.367 | Recall: 0.864 | mAP50: 0.553
- **Pericoronal:** Precision: 0.302 | Recall: 0.333 | mAP50: 0.210
- **Caries:** Precision: 0.555 | Recall: 0.667 | mAP50: 0.648

**Conclusion:** 
Metrics are now reasonable, especially for the critical **Caries** class (mAP50 jumped from 0.009 to 0.648). We will **freeze this checkpoint** (`best.pt`) as our base-model candidate and resist further infinite tuning.

---

## 3. Known Weak Points (Honest Documentation for Pitch)
To maintain credibility, we acknowledge the following limitations of the current frozen checkpoint:

1. **Extreme Data Sparsity in Rare Classes:** 
   - `Inter-Radicular` had only 1 instance in the validation set (and 0% recall). 
   - `Pericoronal` had only 6 instances. The model simply hasn't seen enough examples of these abnormalities to generalize reliably.
2. **Over-prediction of Periapical Lesions:** 
   While `Periapical` recall is excellent (86.4%), its precision is low (36.7%). This means the model is highly sensitive and catches most periapical lesions, but it generates a significant number of false positives. This will require a human-in-the-loop (dentist) to review the highlighted regions.
3. **Loss of "Impacted" / "Deep Caries":** 
   We successfully salvaged the general `Caries` class, but we had to drop the granular distinction between standard and "Deep Caries," as well as "Impacted" teeth, because the DENTEX annotations were incompatible. We currently only output a unified `Caries` label.
