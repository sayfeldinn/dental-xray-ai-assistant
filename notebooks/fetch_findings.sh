#!/usr/bin/env bash
# Download the findings run WITHOUT touching production weights.
# Usage: ./fetch_findings.sh [staging-dir]
set -euo pipefail

KAGGLE_BIN="${KAGGLE_BIN:-kaggle}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="${1:-/tmp/opencode/kaggle_out}"

mkdir -p "$STAGE/findings"
echo "==> downloading findings run"
"$KAGGLE_BIN" kernels output sayfeldin/dentalai-findings-detector -p "$STAGE/findings"

echo "==> artifacts"
ls -lh "$STAGE/findings"

if [ -f "$STAGE/findings/findings_metrics.json" ]; then
  echo "==> validation metrics"
  cat "$STAGE/findings/findings_metrics.json"
fi

echo
echo "next: run notebooks/09_evaluate_findings.ipynb"
echo "      weights stay in $STAGE/findings until the test split is scored"
