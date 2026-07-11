#!/usr/bin/env bash
# Runs the test suite in every cv-* repo, detected by project type.
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAILED=()

test_repo() {
  local dir="$1"
  local name
  name="$(basename "$dir")"
  echo "=== Test: $name ==="

  if [ -f "$dir/pom.xml" ]; then
    (cd "$dir" && mvn -q -B test) || FAILED+=("$name")
  elif [ -f "$dir/package.json" ]; then
    (cd "$dir" && npm test --silent) || FAILED+=("$name")
  elif [ -d "$dir/sql" ]; then
    echo "no automated tests for migrations yet, skipping"
  else
    echo "no test runner configured, skipping"
  fi
}

for dir in "$ROOT_DIR"/cv-*; do
  [ -d "$dir" ] || continue
  test_repo "$dir"
done

if [ "${#FAILED[@]}" -gt 0 ]; then
  echo "Tests failed in: ${FAILED[*]}"
  exit 1
fi
echo "All test suites passed."
