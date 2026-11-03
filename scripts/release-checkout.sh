#!/usr/bin/env bash
# Puts every sibling at its <name> tag (detached HEAD), after checking all of
# them first: a sibling with uncommitted changes or untracked files, a missing
# tag, a local tag that differs from origin's, or a tag on a commit other than
# the manifest's stops the run before any repo moves. Never touches a branch.
# Check the meta repo out yourself first. (T-504)
# Usage: git checkout M2 && scripts/release-checkout.sh M2
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/release-lib.sh"

name="${1:-}"
check_name "$name"

# The tag in <dir> as origin has it, fetching it if missing locally. Prints the
# commit; on failure prints why and returns 1.
synced_tag() {
  local dir="$1" remote have
  remote="$(remote_tag_commit "$dir" "$name")" || { echo "can't read origin"; return 1; }
  [ -n "$remote" ] || { echo "no tag $name on origin"; return 1; }
  if [ -z "$(local_tag_commit "$dir" "$name")" ]; then
    git -C "$dir" fetch --quiet origin tag "$name" 2>/dev/null || { echo "fetching tag $name failed"; return 1; }
  fi
  have="$(local_tag_commit "$dir" "$name")"
  [ "$have" = "$remote" ] || { echo "local tag $name is ${have:0:12}, origin's is ${remote:0:12}"; return 1; }
  echo "$have"
}

# The manifest comes from the meta repo's tag, so this works from any branch.
meta_commit="$(synced_tag "$ROOT")" || die "meta repo: $meta_commit"
pairs="$(git -C "$ROOT" show "$meta_commit:releases/$name.json" 2>/dev/null | manifest_commits)" \
  || die "meta repo: tag $name has no valid releases/$name.json manifest"

problems=()
plan=()
while read -r repo commit; do
  dir="$ROOT/$repo"
  if [ ! -d "$dir/.git" ]; then problems+=("$repo: not cloned at $dir"); continue; fi
  is_clean "$dir" || { problems+=("$repo: uncommitted changes or untracked files"); continue; }
  have="$(synced_tag "$dir")" || { problems+=("$repo: $have"); continue; }
  [ "$have" = "$commit" ] || { problems+=("$repo: tag $name is ${have:0:12}, manifest says ${commit:0:12}"); continue; }
  plan+=("$dir")
done <<<"$pairs"

if [ "${#problems[@]}" -gt 0 ]; then
  printf 'error: %s\n' "${problems[@]}" >&2
  echo "nothing was checked out" >&2
  exit 1
fi

for dir in "${plan[@]}"; do
  git -C "$dir" checkout --quiet --detach "refs/tags/$name"
  echo "$(basename "$dir"): at $name"
done
