#!/usr/bin/env bash
# Install the production weights from the GitHub Release and verify them against
# dentex_week3/production/weights.sha256 (the exact files scored on the locked 50).
# The repo is private, so this uses the GitHub CLI (`gh auth login` once).
# Usage: ./notebooks/fetch_release_weights.sh [tag]
set -euo pipefail

TAG="${1:-weights-v3}"
REPO_SLUG="${REPO_SLUG:-sayfeldinn/dental-xray-ai-assistant}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/dentex_week3/production"

echo "==> downloading $TAG from $REPO_SLUG"
gh release download "$TAG" --repo "$REPO_SLUG" --pattern "*.pt" --dir "$DEST" --clobber

echo "==> verifying checksums"
(cd "$DEST" && shasum -a 256 -c weights.sha256)

ls -lh "$DEST"/*.pt
