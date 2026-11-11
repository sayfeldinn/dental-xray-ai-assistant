#!/usr/bin/env bash
# Deploy the ML service (private) and the backend API (public) to Google Cloud Run.
#
#   deploy/deploy_cloud_run.sh <gcp-project-id> <frontend-origin>
#   deploy/deploy_cloud_run.sh my-project https://dentalai-49y.pages.dev
#
# Needs `gcloud auth login` and a project with billing enabled. Reads SUPABASE_URL and
# SUPABASE_SERVICE_ROLE_KEY from the repo-root .env; the service-role key goes to Secret
# Manager, never into an image or an env var. Safe to re-run: every step is idempotent.
set -euo pipefail

PROJECT="${1:?usage: deploy_cloud_run.sh <gcp-project-id> <frontend-origin>}"
FRONTEND_ORIGIN="${2:?usage: deploy_cloud_run.sh <gcp-project-id> <frontend-origin>}"
REGION="${REGION:-europe-west1}"          # close to Supabase eu-west-1
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

env_value() { grep -E "^$1=" .env | head -1 | cut -d= -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//'; }
SUPABASE_URL="$(env_value SUPABASE_URL)"
SERVICE_KEY="$(env_value SUPABASE_SERVICE_ROLE_KEY)"
[ -n "$SUPABASE_URL" ] && [ -n "$SERVICE_KEY" ] || { echo "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY missing in .env" >&2; exit 1; }

TAG="$(git rev-parse --short HEAD)"
AR="$REGION-docker.pkg.dev/$PROJECT/dentalai"
ML_SA="dentalai-ml@$PROJECT.iam.gserviceaccount.com"
BACKEND_SA="dentalai-backend@$PROJECT.iam.gserviceaccount.com"
SECRET=supabase-service-role-key
G=(--project "$PROJECT" --quiet)

echo "==> enabling APIs"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  cloudbuild.googleapis.com secretmanager.googleapis.com "${G[@]}"

echo "==> image repository"
gcloud artifacts repositories describe dentalai --location "$REGION" "${G[@]}" >/dev/null 2>&1 ||
  gcloud artifacts repositories create dentalai --repository-format docker --location "$REGION" "${G[@]}"

echo "==> service accounts"
for sa in dentalai-ml dentalai-backend; do
  gcloud iam service-accounts describe "$sa@$PROJECT.iam.gserviceaccount.com" "${G[@]}" >/dev/null 2>&1 ||
    gcloud iam service-accounts create "$sa" --display-name "DentalAI $sa" "${G[@]}"
done

echo "==> Supabase service-role key -> Secret Manager"
if ! gcloud secrets describe "$SECRET" "${G[@]}" >/dev/null 2>&1; then
  gcloud secrets create "$SECRET" --replication-policy automatic "${G[@]}"
fi
if [ "$(gcloud secrets versions access latest --secret "$SECRET" "${G[@]}" 2>/dev/null || true)" != "$SERVICE_KEY" ]; then
  printf '%s' "$SERVICE_KEY" | gcloud secrets versions add "$SECRET" --data-file - "${G[@]}"
fi
gcloud secrets add-iam-policy-binding "$SECRET" --member "serviceAccount:$BACKEND_SA" \
  --role roles/secretmanager.secretAccessor "${G[@]}" >/dev/null

echo "==> building images in Cloud Build ($TAG)"
gcloud builds submit --config deploy/cloudbuild.yaml \
  --substitutions "_IMAGE_BASE=$AR,_TAG=$TAG" "${G[@]}" .

echo "==> ML service (private: only the backend may call it)"
gcloud run deploy dentalai-ml --image "$AR/ml:$TAG" --region "$REGION" \
  --service-account "$ML_SA" --no-allow-unauthenticated --port 8001 \
  --memory 2Gi --cpu 2 --cpu-boost --concurrency 4 \
  --min-instances 0 --max-instances 2 --timeout 120 "${G[@]}"
ML_URL="$(gcloud run services describe dentalai-ml --region "$REGION" --format 'value(status.url)' "${G[@]}")"
gcloud run services add-iam-policy-binding dentalai-ml --region "$REGION" \
  --member "serviceAccount:$BACKEND_SA" --role roles/run.invoker "${G[@]}" >/dev/null

echo "==> backend API (public; every route checks the Supabase login itself)"
ENV_FILE="$(mktemp)"
trap 'rm -f "$ENV_FILE"' EXIT
cat > "$ENV_FILE" <<EOF
ENVIRONMENT: production
DEBUG: "false"
SUPABASE_URL: "$SUPABASE_URL"
ML_SERVICE_URL: "$ML_URL"
ML_SERVICE_AUTH: "true"
ML_TIMEOUT_SECONDS: "120"
CORS_ORIGINS: '["$FRONTEND_ORIGIN"]'
EOF
gcloud run deploy dentalai-backend --image "$AR/backend:$TAG" --region "$REGION" \
  --service-account "$BACKEND_SA" --allow-unauthenticated --port 8000 \
  --memory 512Mi --cpu 1 --min-instances 0 --max-instances 3 --timeout 300 \
  --env-vars-file "$ENV_FILE" --set-secrets "SUPABASE_SERVICE_ROLE_KEY=$SECRET:latest" "${G[@]}"
BACKEND_URL="$(gcloud run services describe dentalai-backend --region "$REGION" --format 'value(status.url)' "${G[@]}")"

echo "==> smoke test"
curl -fsS "$BACKEND_URL/health"; echo
code="$(curl -s -o /dev/null -w '%{http_code}' "$ML_URL/")"
echo "ML service from the internet without a token: HTTP $code (403 expected)"

echo
echo "ML service : $ML_URL (private)"
echo "Backend API: $BACKEND_URL"
echo "Next: deploy/deploy_frontend.sh $BACKEND_URL"
