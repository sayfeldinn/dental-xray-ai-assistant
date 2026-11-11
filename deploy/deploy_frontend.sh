#!/usr/bin/env bash
# Build the clinician UI against the deployed backend and publish it to Cloudflare Pages.
#
#   deploy/deploy_frontend.sh <backend-url>
#   deploy/deploy_frontend.sh https://dentalai-backend-xxxx.europe-west1.run.app
#
# Needs `npx wrangler login` once. Only touches the Pages project named below. VITE_* values
# are public by design (they ship to every browser); the anon key cannot read patient data.
set -euo pipefail

BACKEND_URL="${1:?usage: deploy_frontend.sh <backend-url>}"
PROJECT_NAME="${PAGES_PROJECT:-dentalai}"
WRANGLER="wrangler@4.20.0"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

env_value() { grep -E "^$1=" "$ROOT/.env" | head -1 | cut -d= -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//'; }
export VITE_API_URL="${BACKEND_URL%/}"
export VITE_SUPABASE_URL="$(env_value VITE_SUPABASE_URL)"
export VITE_SUPABASE_ANON_KEY="$(env_value VITE_SUPABASE_ANON_KEY)"
[ -n "$VITE_SUPABASE_URL" ] && [ -n "$VITE_SUPABASE_ANON_KEY" ] || { echo "VITE_SUPABASE_* missing in .env" >&2; exit 1; }

cd "$ROOT/frontend"
echo "==> building against $VITE_API_URL"
npm ci --silent
npm run build              # shell env wins over the .env file, so VITE_API_URL is the cloud one

echo "==> publishing to Cloudflare Pages project '$PROJECT_NAME'"
npx -y "$WRANGLER" pages deploy dist --project-name "$PROJECT_NAME" --branch main --commit-dirty=true
