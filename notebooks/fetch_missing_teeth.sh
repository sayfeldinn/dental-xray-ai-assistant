#!/usr/bin/env bash
# Download the missing-teeth gap-vs-tooth classifier.
# Usage: ./fetch_missing_teeth.sh [staging-dir]
set -euo pipefail
KAGGLE_BIN="${KAGGLE_BIN:-kaggle}"
STAGE="${1:-/tmp/opencode/kaggle_out_mt}"
mkdir -p "$STAGE"
"$KAGGLE_BIN" kernels output sayfeldin/dentalai-missing-teeth -p "$STAGE"
rm -f "$STAGE"/detect_cache.json "$STAGE"/*.kaggle-partial
ls -lh "$STAGE"
echo
echo "install: cp $STAGE/missing_teeth.pt dentex_week3/production/"
echo "config : missing_teeth_model=missing_teeth.pt, missing_teeth_gap_threshold=0.40"
