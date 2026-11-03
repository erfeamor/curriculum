#!/usr/bin/env bash
# Read-only. For the meta repo and every sibling, checks that <name> exists
# locally and on GitHub, points at the manifest's commit (the meta repo's at
# the commit that holds the manifest), and that the working copy is on it.
# Exits non-zero naming every repo that isn't. Changes nothing, not even
# refs: it reads origin with ls-remote instead of fetching. (T-504)
# Usage: scripts/release-verify.sh M2
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/release-lib.sh"

name="${1:-}"
check_name "$name"

meta_commit="$(local_tag_commit "$ROOT" "$name")"
[ -n "$meta_commit" ] || die "meta repo: no local tag $name (git fetch --tags)"
manifest="$(git -C "$ROOT" show "refs/tags/$name:releases/$name.json" 2>/dev/null)" \
  || die "meta repo: tag $name has no releases/$name.json"

failed=()
check() {
  local label="$1" dir="$2" want="$3" have remote head
  if [ ! -d "$dir/.git" ]; then
    echo "FAIL $label: not cloned at $dir"; failed+=("$label"); return
  fi
  have="$(local_tag_commit "$dir" "$name")"
  remote="$(remote_tag_commit "$dir" "$name")"
  head="$(git -C "$dir" rev-parse HEAD)"
  local why=()
  [ -n "$have" ] || why+=("no local tag")
  [ -z "$have" ] || [ "$have" = "$want" ] || why+=("local tag is ${have:0:12}")
  [ -n "$remote" ] || why+=("no tag on origin")
  [ -z "$remote" ] || [ "$remote" = "$want" ] || why+=("origin's tag is ${remote:0:12}")
  [ "$head" = "$want" ] || why+=("working copy at ${head:0:12}, not on $name")
  if [ "${#why[@]}" -eq 0 ]; then
    echo "ok   $label: $name ${want:0:12}"
  else
    local IFS=';'
    echo "FAIL $label: ${why[*]} (expected ${want:0:12})"; failed+=("$label")
  fi
}

check "curriculum" "$ROOT" "$meta_commit"
while read -r repo commit; do
  check "$repo" "$ROOT/$repo" "$commit"
done < <(manifest_commits <<<"$manifest")

if [ "${#failed[@]}" -gt 0 ]; then
  echo "error: not at $name: ${failed[*]}" >&2
  exit 1
fi
echo "all 9 repos at $name"
