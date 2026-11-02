#!/usr/bin/env bash
# Fallback: publish the image from a local Mac/Linux Docker installation when GitHub Actions are unavailable.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE='ghcr.io/vbrekher/torrserver-bunny:main'
command -v gh >/dev/null || { echo 'GitHub CLI (gh) is required' >&2; exit 1; }
command -v docker >/dev/null || { echo 'Docker Desktop or Docker Engine with buildx is required' >&2; exit 1; }
gh auth status >/dev/null
docker buildx version >/dev/null
OWNER="$(gh api user --jq .login)"
printf 'Build and publish %s from this local folder, as GitHub account %s\n' "$IMAGE" "$OWNER"
printf 'Requires GHCR write:packages permission on your token and a running Docker daemon.\n'
read -r -p 'Type BUILD to publish the container image: ' ACK
[ "$ACK" = BUILD ] || { echo 'Canceled'; exit 1; }
gh auth token | docker login ghcr.io --username "$OWNER" --password-stdin
cd "$ROOT"
docker buildx build --platform linux/amd64 --provenance=false --sbom=false --file Dockerfile.bunny --tag "$IMAGE" --push .
printf '\nImage pushed: %s\n' "$IMAGE"
printf 'In GitHub package settings, set package visibility to PUBLIC if necessary.\n'
