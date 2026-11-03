#!/usr/bin/env bash
# Puts every sibling at its <name> tag (detached HEAD), after checking all of
# them first: a sibling with uncommitted changes, a missing tag, or a tag on a
# commit other than the manifest's stops the run before any repo moves. Never
# touches a branch. Check the meta repo out yourself first. (T-504)
# Usage: git checkout M2 && scripts/release-checkout.sh M2
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/release-lib.sh"

name="${1:-}"
check_name "$name"

# The manifest comes from the meta repo's tag, so this works from any branch.
# A plain (non-forced) fetch fails if the local tag differs from origin's.
if [ -z "$(local_tag_commit "$ROOT" "$name")" ]; then
  git -C "$ROOT" fetch --quiet origin tag "$name" 2>/dev/null || die "meta repo: no tag $name"
fi
manifest="$(git -C "$ROOT" show "refs/tags/$name:releases/$name.json" 2>/dev/null)" \
  || die "meta repo: tag $name has no releases/$name.json"

problems=()
plan=()
while read -r repo commit; do
  dir="$ROOT/$repo"
  if [ ! -d "$dir/.git" ]; then problems+=("$repo: not cloned at $dir"); continue; fi
  is_clean "$dir" || { problems+=("$repo: uncommitted changes"); continue; }
  if [ -z "$(local_tag_commit "$dir" "$name")" ]; then
    git -C "$dir" fetch --quiet origin tag "$name" 2>/dev/null || { problems+=("$repo: no tag $name"); continue; }
  fi
  have="$(local_tag_commit "$dir" "$name")"
  [ "$have" = "$commit" ] || { problems+=("$repo: tag $name is $have, manifest says $commit"); continue; }
  plan+=("$dir")
done < <(manifest_commits <<<"$manifest")

if [ "${#problems[@]}" -gt 0 ]; then
  printf 'error: %s\n' "${problems[@]}" >&2
  echo "nothing was checked out" >&2
  exit 1
fi

for dir in "${plan[@]}"; do
  git -C "$dir" checkout --quiet --detach "refs/tags/$name"
  echo "$(basename "$dir"): at $name"
done
