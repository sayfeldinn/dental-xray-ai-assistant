"""Stage the mirrored OralXrays-9 for upload as a private Kaggle dataset.

Reads a raw HuggingFace mirror (3 classes) and writes a 4-class copy:

  images/train/*.jpg   hardlinked (no extra disk)
  labels/train/*.txt   remapped to the pipeline index

HF:   0=caries, 1=periapical, 2=impacted
ours: 0=Impacted, 1=Caries, 2=Periapical Lesion, 3=Deep Caries

Usage:
    python notebooks/stage_oralxrays.py [--src /var/tmp/dental-mirror]
                                        [--dst /var/tmp/dental-mirror-v3]
"""

import argparse
import os
import shutil
from collections import Counter
from pathlib import Path

MAP = {0: 1, 1: 2, 2: 0}
NAMES = ["Impacted", "Caries", "Periapical Lesion", "Deep Caries"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="/var/tmp/dental-mirror")
    ap.add_argument("--dst", default="/var/tmp/dental-mirror-v3")
    args = ap.parse_args()

    src, dst = Path(args.src), Path(args.dst)
    if dst.exists():
        shutil.rmtree(dst)
    (dst / "images" / "train").mkdir(parents=True)
    (dst / "labels" / "train").mkdir(parents=True)

    imgs = sorted((src / "images" / "train").glob("*.jpg"))
    counts = Counter()
    linked = missing = 0

    for img in imgs:
        lab = src / "labels" / "train" / (img.stem + ".txt")
        if not lab.exists():
            missing += 1
            continue
        dst_img = dst / "images" / "train" / img.name
        if not dst_img.exists():
            os.link(img, dst_img)
        out = []
        for line in lab.read_text().splitlines():
            if not line.strip():
                continue
            parts = line.split()
            parts[0] = str(MAP[int(parts[0])])
            counts[NAMES[int(parts[0])]] += 1
            out.append(" ".join(parts))
        (dst / "labels" / "train" / (img.stem + ".txt")).write_text(
            "\n".join(out) + ("\n" if out else ""))
        linked += 1

    (dst / "README.md").write_text(
        "# OralXrays-9 mirror (4-class YOLO)\n\n"
        "Source: https://huggingface.co/datasets/liodon-ai/dental-panoramic-xray-yolo\n"
        "which combines DENTEX (CC BY 4.0) and OralXrays-9 (Chen et al., CVPR 2025,\n"
        "research use). License of the combined set: CC BY-NC 4.0.\n\n"
        "Labels remapped from the source 3-class index to the pipeline 4-class index:\n"
        "0=Impacted, 1=Caries, 2=Periapical Lesion, 3=Deep Caries (absent here).\n"
        "The DENTEX validation split (the locked 50-image benchmark) is deliberately\n"
        "excluded: it must never appear in training.\n")

    print(f"staged {linked} images ({missing} without labels)")
    for k, v in counts.most_common():
        print(f"  {k:22s} {v:6d}")
    print("total boxes:", sum(counts.values()))
    size = sum(f.stat().st_size for f in dst.rglob("*") if f.is_file())
    print(f"dst size: {size / 1e9:.2f} GB")


if __name__ == "__main__":
    main()
