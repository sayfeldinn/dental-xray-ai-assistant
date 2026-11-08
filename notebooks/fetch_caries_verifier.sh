#!/usr/bin/env bash
# Download the optional caries-verifier weights (NOT part of production yet).
# Usage: ./fetch_caries_verifier.sh [staging-dir]
set -euo pipefail
KAGGLE_BIN="${KAGGLE_BIN:-kaggle}"
STAGE="${1:-/tmp/opencode/kaggle_out_verifier}"
mkdir -p "$STAGE"
"$KAGGLE_BIN" kernels output sayfeldin/dentalai-caries-verifier -p "$STAGE"
rm -f "$STAGE/romania.zip" "$STAGE"/*.kaggle-partial
ls -lh "$STAGE"
echo
echo "the verifier is not promoted; enable it with, e.g.:"
echo "  DENTEX_CARIES_VERIFIER=$STAGE/caries_verifier.pt:gate:0.7 python dentex_week3/evaluate.py --local ..."
