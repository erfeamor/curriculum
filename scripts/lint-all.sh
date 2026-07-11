#!/usr/bin/env bash
# Runs the appropriate linter in every cv-* repo, detected by project type.
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAILED=()

lint_repo() {
  local dir="$1"
  local name
  name="$(basename "$dir")"
  echo "=== Lint: $name ==="

  if [ -f "$dir/pom.xml" ]; then
    (cd "$dir" && mvn -q -B checkstyle:check) || FAILED+=("$name")
  elif [ -f "$dir/package.json" ]; then
    (cd "$dir" && npm run lint --silent) || FAILED+=("$name")
  elif [ -f "$dir/main.tf" ] || compgen -G "$dir/*.tf" > /dev/null 2>&1; then
    (cd "$dir" && terraform fmt -check -recursive) || FAILED+=("$name")
  else
    echo "no linter configured, skipping"
  fi
}

for dir in "$ROOT_DIR"/cv-*; do
  [ -d "$dir" ] || continue
  lint_repo "$dir"
done

if [ "${#FAILED[@]}" -gt 0 ]; then
  echo "Lint failed in: ${FAILED[*]}"
  exit 1
fi
echo "All lint checks passed."
