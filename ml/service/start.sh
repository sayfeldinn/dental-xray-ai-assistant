#!/usr/bin/env bash
# Start the DENTEX v3 inference API (port 8001 by default).
#
# The production pipeline needs two weights: the 32-class FDI tooth detector and
# the 4-class disease detector. The advisory findings and missing-teeth weights
# are optional: if absent, the API still starts, but those advisory layers are
# unavailable (the missing-teeth rule fallback remains).
set -euo pipefail

cd "$(dirname "$0")"

WEIGHTS_DIR="../weights"
PIPELINE_DIR="../pipeline"
REQUIRED_WEIGHTS=(
  "$WEIGHTS_DIR/tooth_best.pt"
  "$WEIGHTS_DIR/disease_best.pt"
)
OPTIONAL_WEIGHTS=(
  "$WEIGHTS_DIR/findings_best.pt"
  "$WEIGHTS_DIR/missing_teeth.pt"
)
REQUIRED_FILES=(
  "$PIPELINE_DIR/pipeline_config.json"
  "$PIPELINE_DIR/inference.py"
  "app.py"
)

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Install Python 3.11 or 3.12 first." >&2
  exit 1
fi

if [ ! -d venv ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# shellcheck disable=SC1091
source venv/bin/activate

if ! python -c "import fastapi, uvicorn, ultralytics, torch" >/dev/null 2>&1; then
  echo "Installing API dependencies..."
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
fi

missing=0
for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: missing required file: $f" >&2
    missing=1
  fi
done
for w in "${REQUIRED_WEIGHTS[@]}"; do
  if [ ! -f "$w" ]; then
    echo "ERROR: missing required weights: $w" >&2
    missing=1
  fi
done

if [ "$missing" -ne 0 ]; then
  cat >&2 <<'EOF'

Download the v3 weights from the public release, then re-run this script:

  # from the repository root
  ./notebooks/fetch_release_weights.sh

Release: https://github.com/sayfeldinn/dental-xray-ai-assistant/releases/tag/weights-v3
EOF
  exit 1
fi

for w in "${OPTIONAL_WEIGHTS[@]}"; do
  if [ ! -f "$w" ]; then
    echo "WARNING: optional weights not found: $w"
    echo "         The API will start, but that advisory layer will be unavailable."
  fi
done

PORT="${PORT:-8001}"
HOST="${HOST:-0.0.0.0}"

echo
echo "DENTEX v3 inference API"
echo "  tooth detector:   $WEIGHTS_DIR/tooth_best.pt"
echo "  disease detector: $WEIGHTS_DIR/disease_best.pt"
echo "  findings:         $WEIGHTS_DIR/findings_best.pt (advisory, optional)"
echo "  missing teeth:    $WEIGHTS_DIR/missing_teeth.pt (advisory, optional)"
echo "  listening on:     http://${HOST}:${PORT}"
echo "  docs:             http://127.0.0.1:${PORT}/docs"
echo

if [ "${RELOAD:-0}" = "1" ]; then
  exec python -m uvicorn app:app --host "$HOST" --port "$PORT" --reload
else
  exec python -m uvicorn app:app --host "$HOST" --port "$PORT"
fi
