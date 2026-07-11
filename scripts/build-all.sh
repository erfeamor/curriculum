#!/usr/bin/env bash
# Builds every cv-* repo, detected by project type.
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAILED=()

build_repo() {
  local dir="$1"
  local name
  name="$(basename "$dir")"
  echo "=== Build: $name ==="

  if [ -f "$dir/pom.xml" ]; then
    (cd "$dir" && mvn -q -B package -DskipTests) || FAILED+=("$name")
  elif [ -f "$dir/package.json" ]; then
    if grep -q '"build"' "$dir/package.json"; then
      (cd "$dir" && npm run build --silent) || FAILED+=("$name")
    else
      echo "no build script defined, skipping"
    fi
  elif [ -f "$dir/main.tf" ] || compgen -G "$dir/*.tf" > /dev/null 2>&1; then
    (cd "$dir" && terraform validate) || FAILED+=("$name")
  else
    echo "nothing to build, skipping"
  fi
}

for dir in "$ROOT_DIR"/cv-*; do
  [ -d "$dir" ] || continue
  build_repo "$dir"
done

if [ "${#FAILED[@]}" -gt 0 ]; then
  echo "Build failed in: ${FAILED[*]}"
  exit 1
fi
echo "All repos built successfully."
