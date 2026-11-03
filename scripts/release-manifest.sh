#!/usr/bin/env bash
# Writes releases/<name>.json: each sibling's origin/master commit, fetched
# fresh. Commit it to the meta repo through a PR; once merged,
# release-tag.sh <name> tags every repo from it. (T-504)
# Usage: scripts/release-manifest.sh M2
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/release-lib.sh"

name="${1:-}"
check_name "$name"
out="$ROOT/releases/$name.json"
[ ! -e "$out" ] || die "$out already exists; a release manifest is never regenerated"

entries=()
for repo in "${SIBLINGS[@]}"; do
  dir="$ROOT/$repo"
  [ -d "$dir/.git" ] || die "$repo: not cloned at $dir (run ./clone-all.sh)"
  git -C "$dir" fetch --quiet origin master || die "$repo: fetch failed"
  entries+=("$repo" "$(git -C "$dir" rev-parse origin/master)")
done

mkdir -p "$ROOT/releases"
python3 - "$name" "$GITHUB_ORG" "${entries[@]}" > "$out" <<'PY'
import json, sys
name, org, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
repos = {rest[i]: {"github": f"{org}/{rest[i]}", "commit": rest[i + 1]} for i in range(0, len(rest), 2)}
json.dump({"release": name, "repos": repos}, sys.stdout, indent=2)
print()
PY
echo "wrote $out"
