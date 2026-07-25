#!/usr/bin/env bash
# Manage every cv-* repo plus this meta repo.
# Usage: ./update-all.sh [-s|--status] [-r|--reset] [-h|--help]
set -euo pipefail

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

usage() {
  cat <<EOF
Usage: ./update-all.sh [OPTION]

Runs the selected action on every cv-* repo and the meta repo.

Options:
  (no option)    Fast-forward pull every repo (current branch).
  -s, --status   Show each repo's status: branch and working-tree state.
  -r, --reset    Return every repo to a clean master: stash uncommitted
                 changes if any, checkout master, pull.
  -h, --help     Show this help.
EOF
}

status_repo() {
  local name="$1" target="$2"
  local branch dirty
  branch="$(git -C "$target" rev-parse --abbrev-ref HEAD)"
  if [ -n "$(git -C "$target" status --porcelain)" ]; then
    dirty="uncommitted changes"
  else
    dirty="clean"
  fi
  printf '── %s ──\n' "$name"
  printf '   branch: %s, working tree: %s\n' "$branch" "$dirty"
  git -C "$target" status --short | sed 's/^/   /'
}

reset_repo() {
  local name="$1" target="$2"
  local branch
  branch="$(git -C "$target" rev-parse --abbrev-ref HEAD)"
  echo "→ Resetting $name (on $branch)"
  if [ -n "$(git -C "$target" status --porcelain)" ]; then
    echo "   stashing uncommitted changes"
    git -C "$target" stash push -u -m "update-all.sh reset from $branch"
  fi
  if [ "$branch" != "master" ]; then
    git -C "$target" checkout master
  fi
  git -C "$target" pull --ff-only
}

update_repo() {
  local name="$1" target="$2"
  echo "→ Updating $name"
  git -C "$target" pull --ff-only
}

MODE="update"
case "${1:-}" in
  "")           MODE="update" ;;
  -s|--status)  MODE="status" ;;
  -r|--reset)   MODE="reset" ;;
  -h|--help)    usage; exit 0 ;;
  *)            echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
esac

for repo in "${REPOS[@]}"; do
  target="$ROOT_DIR/$repo"

  if [ ! -d "$target/.git" ]; then
    echo "⚠ $repo not cloned yet, run clone-all.sh first"
    continue
  fi

  "${MODE}_repo" "$repo" "$target"
done

"${MODE}_repo" "cv-project (meta repo)" "$ROOT_DIR"
