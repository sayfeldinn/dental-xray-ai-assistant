#!/usr/bin/env bash
# Download the v3 pathology run WITHOUT touching production weights.
# Promotion only happens after v3 beats v2 on the locked benchmark.
# Usage: ./fetch_v3.sh [staging-dir]
set -euo pipefail

KAGGLE_BIN="${KAGGLE_BIN:-kaggle}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="${1:-/tmp/opencode/kaggle_out}"

mkdir -p "$STAGE/pathology"
echo "==> downloading pathology v3 run"
"$KAGGLE_BIN" kernels output sayfeldin/dentalai-pathology-v3 -p "$STAGE/pathology"

echo "==> artifacts"
ls -lh "$STAGE/pathology"

if [ -f "$STAGE/pathology/pathology_v3_metrics.json" ]; then
  echo "==> validation metrics"
  cat "$STAGE/pathology/pathology_v3_metrics.json"
fi

echo
echo "next: run notebooks/05_assemble_and_evaluate.ipynb against"
echo "      $STAGE/pathology/pathology_v3_best.pt"
echo "      (weights are NOT installed into $REPO/dentex_week3/production)"
