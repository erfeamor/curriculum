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

is_clean() { [ -z "$(git -C "$1" status --porcelain --untracked-files=no)" ]; }

# The commit a local tag points at, or nothing.
local_tag_commit() { git -C "$1" rev-parse -q --verify "refs/tags/$2^{commit}" 2>/dev/null || true; }

# The commit a tag points at on origin (peeled for annotated tags), or nothing.
remote_tag_commit() {
  git -C "$1" ls-remote origin "refs/tags/$2" "refs/tags/$2^{}" \
    | awk -v ref="refs/tags/$2" '{ c[$2] = $1 } END { p = ref "^{}"; print (p in c) ? c[p] : c[ref] }'
}

# Prints "<sibling> <commit>" per line from a manifest given on stdin.
manifest_commits() {
  python3 -c 'import json, sys
for name, repo in json.load(sys.stdin)["repos"].items():
    print(name, repo["commit"])'
}
