# DENTEX Multi-Stage Detection Pipeline

> **⚠️ SUPERSEDED — not the shipped model.** This is the **MLv2** generation, kept only as design
> history. The model that actually ships and runs in production is **`dentex_week3/`** (a 3-stage
> pipeline: quadrant coordinator → disease detector → Random Forest tooth association). The
> per-quadrant **enumerators** described below were dropped from the shipped pipeline because
> sequential counting misnumbers teeth when one is missing.
>
> The `mAP@50` figures quoted in this README (0.995 / >0.98 / 0.922) were measured with
> `val = train` (the validation folder pointed at the training split), so they are **training-set
> fit, not generalization**. See `MLv2/Evaluation_Report_v2.md` and `submission/FACTS.md` §4b.
> Training logs are preserved in `MLv2/provenance/`.

This repository contains an advanced, multi-stage Machine Learning pipeline built to solve the DENTEX challenge. By decoupling spatial anatomical reasoning from disease classification, we effectively eliminate the spatial ambiguity common in panoramic X-ray datasets.

## 🧠 Model Weights
Due to file size limits, the trained YOLOv8 model weights (Coordinator, Enumerators, and Global Disease Detector) are hosted externally.

📥 **[Download the Pre-trained Models (.zip) Here](https://drive.google.com/file/d/1vdrmEWC3WfykzR9TsUIAh1NS5ChhizUP/view?usp=sharing)**

*Instructions: Download the zip file and extract it into a `models/` directory next to the API folder to run the inference pipeline.*

---

## 🏗️ Pipeline Architecture

This pipeline consists of **6 separate YOLOv8 models** working together in a mathematically stitched 4-Phase system:

### Phase 1: The Spatial Coordinator (Quadrant Detection)
* **Model:** YOLOv8 Nano
* **Function:** Detects and isolates the four anatomical quadrants (Top-Right, Top-Left, Bottom-Left, Bottom-Right) on the full, raw X-ray.
* **Performance:** `mAP@50 = 0.995`

### Phase 2: Local Enumerators (Tooth Counting)
* **Models:** 4 Independent YOLOv8 Nano Models (one per quadrant)
* **Function:** Dynamically crops the X-ray based on the Coordinator's output. Counts and classifies teeth (1 through 8) strictly within their local anatomical bounds. This prevents the model from confusing identical-looking left and right molars.
* **Performance:** `mAP@50 > 0.98` across all four models.

### Phase 3: Global Disease Detector
* **Model:** YOLOv8 Small
* **Function:** Analyzes the full, uncropped X-ray to detect abnormal pathology, including: Caries, Deep Caries, Periapical Lesions, and Impacted Teeth. The slightly larger YOLOv8s architecture allows for better feature extraction on subtle lesions.
* **Performance:** `mAP@50 = 0.922`

### Phase 4: Integration and Spatial Association
* **Script:** Custom Python Inference Pipeline (`api/app.py`)
* **Function:** Runs the global disease detector and the localized enumerators in parallel. It utilizes an **Intersection over Union (IoU) > 10% threshold algorithm** to map a globally detected disease bounding box to a specific localized tooth bounding box mathematically. 
* **Final Output:** Returns the exact DENTEX requirement: `[Quadrant] + [Tooth Number] + [Diagnosis]`.

---

## 🚀 Running the API

The inference logic is wrapped in a production-ready FastAPI application.

1. Ensure you have downloaded the model weights (link above) and placed them in a `models/` directory.
2. Install dependencies:
   ```bash
   cd api
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Test the pipeline via the interactive swagger UI at `http://localhost:8000/docs` by uploading a panoramic X-ray image.
