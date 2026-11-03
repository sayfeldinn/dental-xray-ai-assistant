#!/usr/bin/env python3
"""Push the Kaggle training notebooks with the correct dataset attachments.

Kaggle has no internet unless the account is phone-verified, so the notebooks
install ultralytics from the private `dentalai-ml-wheels` dataset (which also
carries the pretrained yolov8s.pt). GPU access also requires phone
verification: https://www.kaggle.com/settings -> Phone Verification.

Usage:
    KAGGLE_BIN=~/.local/bin/kaggle python notebooks/push_kaggle.py [--dry-run]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KAGGLE = os.environ.get("KAGGLE_BIN", "kaggle")
STAGE = Path(os.environ.get("KAGGLE_STAGE", "/tmp/opencode/kaggle_push"))

NOTEBOOKS = {
    "tooth": {
        "file": "03_train_tooth_detector.ipynb",
        "id": "sayfeldin/dentalai-tooth-detector",
        "title": "DentalAI Tooth Detector",
    },
    "disease": {
        "file": "04_train_disease_detector.ipynb",
        "id": "sayfeldin/dentalai-disease-detector",
        "title": "DentalAI Disease Detector",
    },
    "pathology": {
        "file": "06_train_pathology_v3.ipynb",
        "id": "sayfeldin/dentalai-pathology-v3",
        "title": "DentalAI Pathology v3",
        # needs internet to pull OralXrays-9 from HuggingFace
        "internet": True,
    },
    "findings": {
        "file": "08_train_findings_detector.ipynb",
        "id": "sayfeldin/dentalai-findings-detector",
        "title": "DentalAI Findings Detector",
        "datasets": ["sayfeldin/dentalopg-1550-yolo", "sayfeldin/dentalai-ml-wheels"],
    },
}

DATASETS = [
    "truthisneverlinear/dentex-challenge-2023",  # raw DENTEX data
    "sayfeldin/dentalai-ml-wheels",              # ultralytics wheels + yolov8s.pt
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", choices=sorted(NOTEBOOKS), help="push a single kernel")
    args = ap.parse_args()

    for key, spec in NOTEBOOKS.items():
        if args.only and key != args.only:
            continue
        stage = STAGE / key
        stage.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / "notebooks" / spec["file"], stage / spec["file"])
        (stage / "kernel-metadata.json").write_text(json.dumps({
            "id": spec["id"],
            "title": spec["title"],
            "code_file": spec["file"],
            "language": "python",
            "kernel_type": "notebook",
            "is_private": True,
            "enable_gpu": True,
            "enable_internet": spec.get("internet", False),
            "dataset_sources": spec.get("datasets", DATASETS),
            "competition_sources": [],
            "kernel_sources": [],
            "model_sources": [],
        }, indent=2))

        cmd = [KAGGLE, "kernels", "push", "-p", str(stage)]
        print("+", " ".join(cmd))
        if not args.dry_run:
            subprocess.run(cmd, check=True)

    print("\nRun status:  kaggle kernels status <id>")
    print("Logs:        kaggle kernels output <id> -p <dir>")
    print("Weights:     ./fetch_weights.sh")


if __name__ == "__main__":
    sys.exit(main())
