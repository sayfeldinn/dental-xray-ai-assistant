#!/usr/bin/env bash
# Upload the OralXrays-9 mirror as a private Kaggle dataset so training kernels
# never download from HuggingFace (whose resolver allows 3000 req / 5 min / IP
# and rate-limits the 18,500-file dataset into an endless retry loop).
#
# One-time cost. After this, `dentalai-oralxrays-v3` is attached to the training
# kernel like any other dataset.
#
# Usage: ./upload_oralxrays.sh [src-dir] [dst-dir]
set -euo pipefail

KAGGLE_BIN="${KAGGLE_BIN:-kaggle}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${1:-/var/tmp/dental-mirror}"
DST="${2:-/var/tmp/dental-mirror-v3}"

echo "==> staging 4-class mirror from $SRC"
python3 "$REPO/notebooks/stage_oralxrays.py" --src "$SRC" --dst "$DST"

cat > "$DST/dataset-metadata.json" <<'JSON'
{
  "title": "DentalAI OralXrays-9 mirror (4-class YOLO)",
  "id": "sayfeldin/dentalai-oralxrays-v3",
  "licenses": [{"name": "CC-BY-NC-4.0"}]
}
JSON

echo "==> uploading $DST (zip mode)"
"$KAGGLE_BIN" datasets create -p "$DST" -r zip

echo "==> done: sayfeldin/dentalai-oralxrays-v3"
