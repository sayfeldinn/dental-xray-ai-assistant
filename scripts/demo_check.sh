#!/usr/bin/env bash
# Pre-demo health check for the local DentalAI stack.
# Usage: ./scripts/demo_check.sh
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ML_URL="${ML_URL:-http://127.0.0.1:8001}"
API_URL="${API_URL:-http://127.0.0.1:8000}"
UI_URL="${UI_URL:-http://127.0.0.1:8080}"
SUPABASE_URL="${SUPABASE_URL:-http://127.0.0.1:54321}"

pass=0
fail=0

ok() { echo "  ✅ $1"; pass=$((pass + 1)); }
bad() { echo "  ❌ $1"; fail=$((fail + 1)); }
info() { echo "  •  $1"; }

echo "DentalAI demo pre-flight"
echo "========================"

echo
echo "Weights"
for f in tooth_best.pt disease_best.pt; do
  if [ -f "ml/weights/$f" ]; then ok "ml/weights/$f"; else bad "missing ml/weights/$f"; fi
done
for f in findings_best.pt missing_teeth.pt; do
  if [ -f "ml/weights/$f" ]; then ok "ml/weights/$f (advisory)"; else info "optional advisory weight missing: ml/weights/$f"; fi
done

echo
echo "Services"
if ! command -v curl >/dev/null 2>&1; then
  bad "curl not found; cannot check services"
else
  ml_body="$(curl -fsS --max-time 3 "$ML_URL/" 2>/dev/null || true)"
  if echo "$ml_body" | grep -q '"models_loaded": *true'; then
    ok "ML $ML_URL (models loaded)"
  elif [ -n "$ml_body" ]; then
    bad "ML $ML_URL responded but models are not loaded"
  else
    bad "ML $ML_URL unreachable"
  fi

  if curl -fsS --max-time 3 "$API_URL/health" >/dev/null 2>&1; then
    ok "Backend $API_URL/health"
  else
    bad "Backend $API_URL/health unreachable"
  fi

  ui_code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$UI_URL/" 2>/dev/null || true)"
  ui_code="${ui_code:-000}"
  if [ "$ui_code" = "200" ] || [ "$ui_code" = "304" ]; then
    ok "Frontend $UI_URL ($ui_code)"
  else
    bad "Frontend $UI_URL returned $ui_code"
  fi

  # Supabase REST without an API key is expected to be 401; 200 is also fine.
  sb_code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$SUPABASE_URL/rest/v1/" 2>/dev/null || true)"
  sb_code="${sb_code:-000}"
  if [ "$sb_code" = "401" ] || [ "$sb_code" = "200" ]; then
    ok "Supabase $SUPABASE_URL (HTTP $sb_code, expected 401/200)"
  else
    bad "Supabase $SUPABASE_URL returned $sb_code"
  fi
fi

echo
echo "Demo entry points"
info "Login:  $UI_URL/login"
info "Patient: $UI_URL/patients/715a685f-8ed6-48dd-a54d-9c735eef6875"
info "Scan:    $UI_URL/scans/e6b213ba-f1ca-4b60-87de-a127e7c14507"
info "0.50 scan: $UI_URL/scans/5f25a5ba-542e-4910-bf5b-7c88b7c824b2"
info "Runbook: docs/qa/conference-demo-script.md"

echo
if [ "$fail" -eq 0 ]; then
  echo "READY: $pass checks passed."
  exit 0
fi
echo "NOT READY: $fail check(s) failed, $pass passed."
echo "Fix the red items or switch to the recorded video."
exit 1
