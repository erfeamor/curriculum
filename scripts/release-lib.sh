# Shared by the release-*.sh scripts (T-504). Sourced, not run.
#
# A release is a tag of the same name in all nine repos. The meta repo's tag
# is the commit that adds releases/<name>.json, which records the commit each
# sibling's tag points at, so the meta repo at <name> defines the release.

GITHUB_ORG="erfeamor"
META_GITHUB_REPO="curriculum"
# Same list, same order as clone-all.sh.
SIBLINGS=(
  cv-database
  cv-domain-service
  cv-bff-node
  cv-admin-react
  cv-public-vanilla
  cv-public-react
  cv-observability
  cv-infra
)

# CV_RELEASE_ROOT exists for the tests (scripts/test_release.py); in normal use
# the workspace is the meta repo this script lives in.
ROOT="${CV_RELEASE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

die() { echo "error: $*" >&2; exit 1; }

# Release names must match the tag ruleset's pattern (refs/tags/M*), or the
# tags would be created unprotected.
check_name() {
  [[ "${1:-}" =~ ^M[0-9]+$ ]] || die "release name must look like M2 (got '${1:-}')"
}

# Clean means no changes and no untracked files: an untracked file at a path
# the release tracks would make `git checkout` fail halfway through a run.
is_clean() { [ -z "$(git -C "$1" status --porcelain)" ]; }

# The commit a local tag points at, or nothing.
local_tag_commit() { git -C "$1" rev-parse -q --verify "refs/tags/$2^{commit}" 2>/dev/null || true; }

# The commit a tag points at on origin (peeled for annotated tags), or nothing.
# Fails if origin can't be read, so call it as `x="$(remote_tag_commit …)" ||`;
# never inside a `for` word list, where a failure reads as "no tag".
remote_tag_commit() {
  git -C "$1" ls-remote origin "refs/tags/$2" "refs/tags/$2^{}" \
    | awk -v ref="refs/tags/$2" '{ c[$2] = $1 } END { p = ref "^{}"; print (p in c) ? c[p] : c[ref] }'
}

# Prints "<sibling> <commit>" per line, in SIBLINGS order, from a manifest on
# stdin. Fails unless the manifest names exactly the eight siblings, each with
# a full commit id. Capture it with `x="$(manifest_commits …)" || die` rather
# than reading it through `< <(…)`, which would hide that failure.
manifest_commits() {
  python3 -c 'import json, re, sys
want = sys.argv[1:]
try:
    repos = json.load(sys.stdin)["repos"]
    commits = {name: repos[name]["commit"] for name in repos}
except Exception as e:
    sys.exit(f"error: manifest unreadable: {e!r}")
if sorted(commits) != sorted(want):
    sys.exit(f"error: manifest lists {sorted(commits)}, expected exactly {sorted(want)}")
for name in want:
    if not re.fullmatch("[0-9a-f]{40}", str(commits[name])):
        sys.exit(f"error: manifest: {name} has no full commit id")
    print(name, commits[name])' "${SIBLINGS[@]}"
}
