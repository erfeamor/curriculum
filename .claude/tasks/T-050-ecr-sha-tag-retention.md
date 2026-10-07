---
id: T-050
title: "cv-infra: ECR keeps every `:<sha>` deploy image forever — add a retention rule for sha tags"
repo: cv-infra
status: in_progress
owner: tech-product-owner
branch: fix/ecr-sha-tag-retention
pr:
depends_on: [T-112, T-203]
risk: low
security_review: false
checkpoint:
  stage: implement   # H1 2026-10-07
  repo: cv-infra
  branch: fix/ecr-sha-tag-retention
  worktree: none
  commit:
  pr:
  developer: infrastructure-engineer
  reviewers: [code-review]
  risk: low
  security_review: false
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live ECR
  updated: 2026-10-07T14:30:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
    status: ok   # human-reported /usage under ~40%
    checked: 2026-10-07T14:30:00+02:00
---

## H1 — decided by the human, 2026-10-07

**Stage 0 finding that shapes the rule:** each deploy pushes a multi-arch **index** (tagged `latest` + `<sha>`) and 2 per-arch child manifests (up to 4 with attestations), and **the children are untagged**. Live: domain-service 11 untagged / 3 indexes, bff-node 8 / 3. T-035's rule keeps only the 20 newest *untagged*, so once more than ~5 deploys accumulate it expires the children of older sha-tagged indexes, leaving a `:<sha>` tag that no longer pulls (a silent rollback break). Sha retention must therefore fit the untagged budget.

1. **Retention: 5 deploys of rollback depth, untagged budget unchanged at 20.** Rule 1 selects tag prefix `latest` (`imageCountMoreThan 1`, so it never expires; ECR never lets a lower-priority rule expire an image a higher-priority rule's tag selection matched, so `:latest` stays protected even after a rollback re-tags an older image). Rule 2 keeps the **4 newest other tagged images** (`tagPatternList ["*"]`): `latest` + 4 = 5 indexes × ≤4 children = ≤20, inside rule 3, the untagged rule (20, unchanged). Both repos.
2. **Proof:** before the apply, `start-lifecycle-policy-preview` with the new policy shows nothing current would expire; after it, `docker manifest inspect` shows `:latest` and every kept sha still resolve with both architectures.
3. **Budget:** `/usage` under ~40%: the whole task this window.

## Why

Found at T-112/T-203's review (non-blocking), filed by the 2026-10-06 board review. Every automated deploy pushes `:latest` **and** an immutable `:<sha>` multi-arch image (~100 MB). T-035's lifecycle rule expires only **untagged** images, so sha-tagged ones accumulate without bound (ECR storage $0.10/GB-month: cents now, unbounded later).

## Scope

- A lifecycle rule on both repos that keeps the **last N (e.g. 10) sha-tagged images** and never touches `:latest`. ECR rules match `tagPatternList`; sha tags are 40 hex chars, so use a pattern that can't match `latest`. Keep T-035's untagged rule.
- `terraform test` assertion; the runbook's rollback note says only the last N shas are kept.

## Acceptance criteria

- [ ] Applied; `aws ecr get-lifecycle-policy-preview` shows only old sha tags would expire, never `:latest`.
