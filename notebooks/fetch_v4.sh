#!/usr/bin/env bash
# Download the v4 pathology run WITHOUT touching production weights.
# Promotion only happens after v4 beats v3 on the locked benchmark.
# Usage: ./fetch_v4.sh [staging-dir]
set -euo pipefail

KAGGLE_BIN="${KAGGLE_BIN:-kaggle}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="${1:-/tmp/opencode/kaggle_out}"

mkdir -p "$STAGE/pathology_v4"
echo "==> downloading pathology v4 run"
"$KAGGLE_BIN" kernels output sayfeldin/dentalai-pathology-v4 -p "$STAGE/pathology_v4"

# The run output may also contain the Zenodo fallback romania.zip (~1.4 GB).
# It is not needed for evaluation.
rm -f "$STAGE/pathology_v4/romania.zip" "$STAGE/pathology_v4"/*.kaggle-partial

echo "==> artifacts"
ls -lh "$STAGE/pathology_v4"

if [ -f "$STAGE/pathology_v4/pathology_v4_metrics.json" ]; then
  echo "==> validation metrics"
  cat "$STAGE/pathology_v4/pathology_v4_metrics.json"
fi

echo
echo "next: run notebooks/11_evaluate_v4.ipynb against"
echo "      $STAGE/pathology_v4/pathology_v4_best.pt"
echo "      (weights are NOT installed into $REPO/dentex_week3/production)"
