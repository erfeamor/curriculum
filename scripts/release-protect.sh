#!/usr/bin/env bash
# Creates, or updates in place, a tag ruleset in all nine GitHub repos that
# blocks updating or deleting any release tag (refs/tags/M*). No bypass, not
# even for admins; creating a new tag stays allowed. Safe to re-run. (T-504)
# Usage: scripts/release-protect.sh
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/release-lib.sh"

RULESET_NAME="Protect release tags"
payload="$(python3 -c 'import json, sys
print(json.dumps({
    "name": sys.argv[1],
    "target": "tag",
    "enforcement": "active",
    "bypass_actors": [],
    "conditions": {"ref_name": {"include": ["refs/tags/M*"], "exclude": []}},
    "rules": [{"type": "update"}, {"type": "deletion"}],
}))' "$RULESET_NAME")"

for repo in "$META_GITHUB_REPO" "${SIBLINGS[@]}"; do
  path="repos/$GITHUB_ORG/$repo/rulesets"
  id="$(gh api "$path" --jq ".[] | select(.name == \"$RULESET_NAME\") | .id")"
  if [ -n "$id" ]; then
    gh api "$path/$id" --method PUT --input - <<<"$payload" > /dev/null
    echo "$repo: updated ruleset $id"
  else
    gh api "$path" --method POST --input - <<<"$payload" > /dev/null
    echo "$repo: created ruleset"
  fi
done
