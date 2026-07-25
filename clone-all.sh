#!/usr/bin/env bash
# Clones every cv-* repo as a sibling of this meta repo (cv-project).
# Usage: ./clone-all.sh [https|ssh]
set -euo pipefail

GITHUB_ORG="erfeamor"
PROTOCOL="${1:-https}"

REPOS=(
  cv-database
  cv-domain-service
  cv-bff-node
  cv-admin-react
  cv-public-vanilla
  cv-public-react
  cv-observability
  cv-infra
)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for repo in "${REPOS[@]}"; do
  target="$ROOT_DIR/$repo"

  if [ -d "$target/.git" ]; then
    echo "✔ $repo already cloned, skipping"
    continue
  fi

  if [ "$PROTOCOL" = "ssh" ]; then
    url="git@github.com:${GITHUB_ORG}/${repo}.git"
  else
    url="https://github.com/${GITHUB_ORG}/${repo}.git"
  fi

  echo "→ Cloning $repo from $url"
  git clone "$url" "$target"
done

echo "Done. Repos live as siblings of cv-project under: $ROOT_DIR"
