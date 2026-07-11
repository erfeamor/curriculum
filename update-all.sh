#!/usr/bin/env bash
# Fast-forward pulls every cv-* repo plus this meta repo.
# Usage: ./update-all.sh
set -euo pipefail

REPOS=(
  cv-database
  cv-domain-service
  cv-bff-node
  cv-admin-react
  cv-public-vanilla
  cv-observability
  cv-infra
)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for repo in "${REPOS[@]}"; do
  target="$ROOT_DIR/$repo"

  if [ ! -d "$target/.git" ]; then
    echo "⚠ $repo not cloned yet, run clone-all.sh first"
    continue
  fi

  echo "→ Updating $repo"
  git -C "$target" pull --ff-only
done

echo "→ Updating cv-project (meta repo)"
git -C "$ROOT_DIR" pull --ff-only
