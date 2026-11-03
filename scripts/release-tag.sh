#!/usr/bin/env bash
# Tags every repo for a release whose manifest is already merged: each sibling
# at the commit releases/<name>.json records, the meta repo at the commit on
# origin/master that added that file (not whatever merged after it). Every
# check runs before anything is tagged; the meta repo is tagged last, so its
# tag only appears once every sibling's has; and a re-run with some or all of
# the tags in place finishes the job. (T-504)
# Usage: scripts/release-tag.sh M2
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/release-lib.sh"

name="${1:-}"
check_name "$name"
file="releases/$name.json"

git -C "$ROOT" fetch --quiet origin master || die "meta repo: fetch failed"
meta_commit="$(git -C "$ROOT" log -1 --format=%H --diff-filter=A origin/master -- "$file")"
[ -n "$meta_commit" ] || die "meta repo: origin/master has no $file (merge the manifest first)"
git -C "$ROOT" diff --quiet "$meta_commit" origin/master -- "$file" \
  || die "meta repo: $file changed after ${meta_commit:0:12} added it; a manifest is never edited"
pairs="$(git -C "$ROOT" show "$meta_commit:$file" | manifest_commits)" \
  || die "meta repo: $file is not a valid manifest"

# Pass 1: check everything.
targets=()
while read -r repo commit; do
  dir="$ROOT/$repo"
  [ -d "$dir/.git" ] || die "$repo: not cloned at $dir"
  git -C "$dir" fetch --quiet origin master || die "$repo: fetch failed"
  git -C "$dir" merge-base --is-ancestor "$commit" origin/master 2>/dev/null \
    || die "$repo: $commit is not on origin/master"
  targets+=("$dir" "$commit")
done <<<"$pairs"
targets+=("$ROOT" "$meta_commit")

for ((i = 0; i < ${#targets[@]}; i += 2)); do
  dir="${targets[i]}" want="${targets[i + 1]}" repo="$(basename "${targets[i]}")"
  [ "$dir" = "$ROOT" ] && repo="meta repo"
  have="$(local_tag_commit "$dir" "$name")"
  [ -z "$have" ] || [ "$have" = "$want" ] || die "$repo: local $name is on $have, not $want"
  have="$(remote_tag_commit "$dir" "$name")" || die "$repo: can't read origin"
  [ -z "$have" ] || [ "$have" = "$want" ] || die "$repo: origin's $name is on $have, not $want"
done

# Pass 2: tag and push, siblings first, the meta repo last.
for ((i = 0; i < ${#targets[@]}; i += 2)); do
  dir="${targets[i]}" want="${targets[i + 1]}"
  [ -n "$(local_tag_commit "$dir" "$name")" ] || git -C "$dir" tag -a "$name" "$want" -m "Release $name"
  remote="$(remote_tag_commit "$dir" "$name")" || die "$(basename "$dir"): can't read origin"
  [ -n "$remote" ] || git -C "$dir" push --quiet origin "refs/tags/$name"
  echo "$(basename "$dir"): $name -> ${want:0:12}"
done
