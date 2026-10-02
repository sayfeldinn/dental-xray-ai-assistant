
import os
import json
import joblib
import numpy as np
import pandas as pd

from PIL import Image
from ultralytics import YOLO


# ================================================================
# CONFIGURATION
# ================================================================

PACKAGE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

with open(
    os.path.join(
        PACKAGE_DIR,
        "pipeline_config.json"
    ),
    "r"
) as f:
    CONFIG = json.load(f)


PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

COORDINATOR_PATH = CONFIG["coordinator_model"]
DISEASE_PATH = CONFIG["disease_model"]

TOOTH_RF_PATH = os.path.join(
    PACKAGE_DIR,
    "tooth_association_rf_300.joblib"
)


DISEASE_MAP = {
    int(k): v
    for k, v in CONFIG["disease_map"].items()
}

TOOTH_MAP = {
    int(k): v
    for k, v in CONFIG["tooth_map"].items()
}

RAW_TO_ACTUAL_Q = {
    int(k): v
    for k, v in
    CONFIG["coordinator_raw_to_actual_quadrant"].items()
}


# ================================================================
# LOAD MODELS
# ================================================================

COORDINATOR_MODEL = YOLO(
    COORDINATOR_PATH
)

DISEASE_MODEL = YOLO(
    DISEASE_PATH
)

TOOTH_RF = joblib.load(
    TOOTH_RF_PATH
)


# ================================================================
# EXACT STEP 51 FEATURES
# ================================================================

def production_features(df):

    out = pd.DataFrame(index=df.index)

    q = df["quadrant"].astype(float)
    x = df["cx"].astype(float)
    y = df["cy"].astype(float)
    w = df["w"].astype(float)
    h = df["h"].astype(float)
    disease = df["disease"].astype(float)

    out["quadrant"] = q
    out["cx"] = x
    out["cy"] = y
    out["w"] = w
    out["h"] = h
    out["disease"] = disease

    out["area"] = w * h
    out["aspect"] = w / (h + 1e-6)

    anatomical_x = np.where(
        (q == 1) | (q == 4),
        1.0 - x,
        x
    )

    out["anatomical_x"] = anatomical_x
    out["anatomical_y"] = y

    out["q_x"] = q * x
    out["q_y"] = q * y

    out["disease_x"] = disease * x
    out["disease_y"] = disease * y

    out["disease_anatomical_x"] = (
        disease * anatomical_x
    )

    return out


# ================================================================
# IMAGE LOADING
# ================================================================

def load_image_array(image):

    if isinstance(image, str):

        return np.array(
            Image.open(image).convert("RGB")
        )

    if isinstance(image, Image.Image):

        return np.array(
            image.convert("RGB")
        )

    if isinstance(image, np.ndarray):

        if image.ndim == 2:
            image = np.stack(
                [image] * 3,
                axis=-1
            )

        if image.shape[-1] == 4:
            image = image[..., :3]

        return image

    raise TypeError(
        "image must be a filepath, PIL Image, "
        "or numpy array"
    )


# ================================================================
# COORDINATOR
# ================================================================

def detect_quadrants(image):

    H, W = image.shape[:2]

    results = COORDINATOR_MODEL.predict(
        source=image,
        imgsz=640,
        conf=0.25,
        verbose=False
    )

    result = results[0]

    if result.boxes is None:
        return []

    best_by_q = {}

    for box in result.boxes:

        raw_class = int(
            box.cls[0].item()
        )

        confidence = float(
            box.conf[0].item()
        )

        x1, y1, x2, y2 = (
            box.xyxy[0]
            .cpu()
            .numpy()
        )

        actual_q = RAW_TO_ACTUAL_Q.get(
            raw_class
        )

        if actual_q is None:
            continue

        record = {
            "quadrant": actual_q,
            "confidence": confidence,
            "box": [
                float(x1),
                float(y1),
                float(x2),
                float(y2),
            ],
        }

        if (
            actual_q not in best_by_q
            or confidence >
               best_by_q[actual_q]["confidence"]
        ):
            best_by_q[actual_q] = record

    return [
        best_by_q[q]
        for q in sorted(best_by_q)
    ]


# ================================================================
# DISEASE DETECTOR
# ================================================================

def detect_diseases(
    image,
    quadrants
):

    # IMPORTANT:
    # The frozen benchmark used the disease detector
    # on the FULL panorama at imgsz=416, conf=0.20.

    results = DISEASE_MODEL.predict(
        source=image,
        imgsz=416,
        conf=0.20,
        verbose=False
    )

    result = results[0]

    if result.boxes is None:
        return []

    detections = []

    for box in result.boxes:

        disease_id = int(
            box.cls[0].item()
        )

        disease_confidence = float(
            box.conf[0].item()
        )

        bx1, by1, bx2, by2 = (
            box.xyxy[0]
            .cpu()
            .numpy()
        )

        bx1 = float(bx1)
        by1 = float(by1)
        bx2 = float(bx2)
        by2 = float(by2)

        # Disease-box center in panorama coordinates.
        cx = (bx1 + bx2) / 2.0
        cy = (by1 + by2) / 2.0

        # First try to find a quadrant containing
        # the disease-box center.
        containing = []

        for q in quadrants:

            qx1, qy1, qx2, qy2 = q["box"]

            if (
                qx1 <= cx <= qx2
                and
                qy1 <= cy <= qy2
            ):
                containing.append(q)

        if containing:

            # If overlapping quadrant boxes contain the
            # center, choose the smallest containing box.
            quadrant_record = min(
                containing,
                key=lambda q: (
                    (q["box"][2] - q["box"][0])
                    *
                    (q["box"][3] - q["box"][1])
                )
            )

        else:

            # Fallback: nearest quadrant center.
            quadrant_record = min(
                quadrants,
                key=lambda q: (
                    (
                        (
                            q["box"][0]
                            +
                            q["box"][2]
                        ) / 2.0
                        -
                        cx
                    ) ** 2
                    +
                    (
                        (
                            q["box"][1]
                            +
                            q["box"][3]
                        ) / 2.0
                        -
                        cy
                    ) ** 2
                )
            )

        detections.append({
            "quadrant":
                quadrant_record["quadrant"],

            "disease_id":
                disease_id,

            "disease":
                DISEASE_MAP.get(
                    disease_id,
                    f"Unknown_{disease_id}"
                ),

            "disease_confidence":
                disease_confidence,

            "box": [
                bx1,
                by1,
                bx2,
                by2,
            ],
        })

    return detections


# ================================================================
# TOOTH ASSOCIATION
# ================================================================

def associate_teeth(
    detections,
    image_shape
):

    if not detections:
        return []

    H, W = image_shape[:2]

    rows = []

    for d in detections:

        x1, y1, x2, y2 = d["box"]

        rows.append({
            "quadrant":
                d["quadrant"],

            "cx":
                ((x1 + x2) / 2.0) / W,

            "cy":
                ((y1 + y2) / 2.0) / H,

            "w":
                (x2 - x1) / W,

            "h":
                (y2 - y1) / H,

            "disease":
                d["disease_id"],
        })

    df = pd.DataFrame(rows)

    X = production_features(df)

    predictions = TOOTH_RF.predict(X)

    probabilities = TOOTH_RF.predict_proba(X)

    output = []

    for i, d in enumerate(detections):

        tooth_id = int(
            predictions[i]
        )

        tooth_confidence = float(
            np.max(probabilities[i])
        )

        item = dict(d)

        item["tooth_id"] = tooth_id

        item["tooth"] = (
            TOOTH_MAP[tooth_id]
        )

        item["tooth_confidence"] = (
            tooth_confidence
        )

        item["association_confidence"] = (
            d["disease_confidence"]
            * tooth_confidence
        )

        output.append(item)

    return output


# ================================================================
# COMPLETE PIPELINE
# ================================================================

def run_dentex_pipeline(
    image,
    save_json=None
):

    image = load_image_array(image)

    H, W = image.shape[:2]

    quadrants = detect_quadrants(
        image
    )

    # Run disease detector once on the full panorama.
    disease_detections = detect_diseases(
        image,
        quadrants
    )

    final_detections = associate_teeth(
        disease_detections,
        image.shape
    )

    output = {
        "image_width": int(W),
        "image_height": int(H),

        "quadrants": quadrants,

        "detections":
            final_detections,

        "num_detections":
            len(final_detections),

        "model": {
            "coordinator":
                "best.pt",

            "disease":
                "best.pt",

            "tooth":
                "Step_51_RF_300",

            "enumerator":
                False,
        },
    }

    if save_json is not None:

        with open(
            save_json,
            "w"
        ) as f:

            json.dump(
                output,
                f,
                indent=2
            )

    return output
