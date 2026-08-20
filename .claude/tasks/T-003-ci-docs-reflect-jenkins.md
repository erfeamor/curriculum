---
id: T-003
title: Correct the CI documentation to match reality (Jenkins)
repo: cv-project (meta)
status: todo
owner:
branch: docs/ci-reflect-jenkins
pr:
depends_on: [T-002]
risk: trivial
security_review: false   # added 2026-08-20 (hygiene): the key was missing entirely while `risk` was set. Value per adapter §5 — the diff touches none of its security paths; A1 forces /security-review anyway if the real diff disagrees, so this is a stage-0 default, not a ruling.
---

## Why this exists

Split from **T-002** at refinement: that task touches `cv-infra`, this one touches the meta repo, and every task leaving stage 0 must target exactly one repo.

`docs/architecture.md` and `.claude/dev-loop-adapter.md` § 3 both name **Jenkins** as the authoritative CI for `cv-domain-service` and `cv-database`. Until T-002 lands, that is false — Jenkins is provisioned nowhere, and T-101's PR #3 demonstrated the consequence (`gh pr checks` → "no checks reported", zero webhooks on the repo).

## Depends on T-002

Sequenced deliberately: **document what was actually built, not what was planned.** T-002's H1 defers the instance-sizing decision (t3.small vs t3.micro + swap) and the exact Jenkins endpoint/ingress shape, so writing these docs first would just re-assert an unverified claim. Do not start this until T-002 is `done`.

## Scope

- `docs/architecture.md` — describe where Jenkins actually runs (co-located on the Drone CI instance), how GitHub reaches it, and how it reports commit status back. Correct any statement implying a dedicated Jenkins host.
- `.claude/dev-loop-adapter.md` § 3 — the CI column for `cv-domain-service` and `cv-database` stays "Jenkins", but add whatever qualifier T-002's outcome makes true (endpoint, trigger mechanism).
- Record the **Free Tier exception** and its actual monthly cost wherever the workspace's "AWS resources stay within Free Tier" rule is stated, so the exception is discoverable rather than folklore.
- If T-002 changed the CI host's instance type, correct any doc that still claims Free Tier sizing for it.

## Acceptance criteria

- [ ] No document asserts a Jenkins deployment that does not exist.
- [ ] The Free Tier exception is written down with its cost and its rationale.
- [ ] The adapter's § 3 CI table matches the deployed reality.
- [ ] No change to any file outside the meta repo.

## Definition of done

PR open against `master` from `docs/ci-reflect-jenkins`, task updated. Docs-only, so the `trivial` fast-path applies: light gates, H1/H2 as one-line confirms.
