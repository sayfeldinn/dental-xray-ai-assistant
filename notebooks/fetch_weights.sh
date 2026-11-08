#!/usr/bin/env bash
# Download the Kaggle training outputs and install the weights where the ML
# service expects them. Usage: ./fetch_weights.sh [staging-dir]
set -euo pipefail

KAGGLE_BIN="${KAGGLE_BIN:-kaggle}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="${1:-/tmp/opencode/kaggle_out}"

mkdir -p "$STAGE/tooth" "$STAGE/disease"

echo "==> downloading tooth run"
"$KAGGLE_BIN" kernels output sayfeldin/dentalai-tooth-detector -p "$STAGE/tooth"
echo "==> downloading disease run"
"$KAGGLE_BIN" kernels output sayfeldin/dentalai-disease-detector -p "$STAGE/disease"

install -m 644 "$STAGE/tooth/tooth_best.pt" "$REPO/dentex_week3/production/tooth_best.pt"
install -m 644 "$STAGE/disease/disease_best.pt" "$REPO/dentex_week3/production/disease_best.pt"
cp "$STAGE/tooth/tooth_metrics.json" "$REPO/dentex_week3/eval/tooth_metrics.json" 2>/dev/null || true
cp "$STAGE/disease/disease_metrics.json" "$REPO/dentex_week3/eval/disease_metrics.json" 2>/dev/null || true

echo "==> installed:"
ls -lh "$REPO/dentex_week3/production"/*.pt
