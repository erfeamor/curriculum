#!/usr/bin/env bash
# Tags every repo for a release whose manifest is already merged: each sibling
# at the commit releases/<name>.json records, the meta repo at its master HEAD
# (which contains that manifest). Every check runs before anything is tagged,
# and a re-run with the tags already in place is a no-op. (T-504)
# Usage: scripts/release-tag.sh M2
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/release-lib.sh"

name="${1:-}"
check_name "$name"

git -C "$ROOT" fetch --quiet origin master || die "meta repo: fetch failed"
is_clean "$ROOT" || die "meta repo: uncommitted changes"
meta_commit="$(git -C "$ROOT" rev-parse HEAD)"
[ "$meta_commit" = "$(git -C "$ROOT" rev-parse origin/master)" ] \
  || die "meta repo: HEAD is not origin/master; tag the merged manifest, not a branch"
manifest="$(git -C "$ROOT" show "HEAD:releases/$name.json" 2>/dev/null)" \
  || die "meta repo: HEAD has no releases/$name.json (merge the manifest first)"

# Pass 1: check everything.
targets=("$ROOT" "$meta_commit")
while read -r repo commit; do
  dir="$ROOT/$repo"
  [ -d "$dir/.git" ] || die "$repo: not cloned at $dir"
  git -C "$dir" fetch --quiet origin master || die "$repo: fetch failed"
  git -C "$dir" merge-base --is-ancestor "$commit" origin/master 2>/dev/null \
    || die "$repo: $commit is not on origin/master"
  targets+=("$dir" "$commit")
done < <(manifest_commits <<<"$manifest")

for ((i = 0; i < ${#targets[@]}; i += 2)); do
  dir="${targets[i]}" want="${targets[i + 1]}" repo="$(basename "${targets[i]}")"
  [ "$dir" = "$ROOT" ] && repo="meta repo"
  for have in "$(local_tag_commit "$dir" "$name")" "$(remote_tag_commit "$dir" "$name")"; do
    [ -z "$have" ] || [ "$have" = "$want" ] || die "$repo: $name already exists on $have, not $want"
  done
done

# Pass 2: tag and push. The meta repo goes last, so its tag only appears
# once every sibling's does.
order=("${targets[@]:2}" "${targets[@]:0:2}")
for ((i = 0; i < ${#order[@]}; i += 2)); do
  dir="${order[i]}" want="${order[i + 1]}"
  [ -n "$(local_tag_commit "$dir" "$name")" ] || git -C "$dir" tag -a "$name" "$want" -m "Release $name"
  [ -n "$(remote_tag_commit "$dir" "$name")" ] || git -C "$dir" push --quiet origin "refs/tags/$name"
  echo "$(basename "$dir"): $name -> ${want:0:12}"
done
