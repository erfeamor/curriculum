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

# The meta repo has no product code, but scripts/ carries the QA-stack generator
# whose failure mode is silent (T-028) — so its tests run here too.
echo "=== Test: cv-project (meta tooling) ==="
(cd "$ROOT_DIR" && python3 -m unittest discover -s scripts -p 'test_*.py' -q) \
  || FAILED+=("cv-project meta tooling")

if [ "${#FAILED[@]}" -gt 0 ]; then
  echo "Tests failed in: ${FAILED[*]}"
  exit 1
fi
echo "All test suites passed."
