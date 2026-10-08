---
id: T-050
title: "cv-infra: ECR keeps every `:<sha>` deploy image forever — add a retention rule for sha tags"
repo: cv-infra
status: done
owner: tech-product-owner
branch: fix/ecr-sha-tag-retention
pr: https://github.com/erfeamor/cv-infra/pull/41
depends_on: [T-112, T-203]
risk: low
security_review: false
checkpoint:
  stage: done   # merged 3f8d80d (squash of cv-infra#41), 2026-10-07 — applied from the branch first; H2 accepted; master plans No changes
  repo: cv-infra
  branch: fix/ecr-sha-tag-retention
  worktree: none
  commit: 3f8d80d
  pr: https://github.com/erfeamor/cv-infra/pull/41
  developer: infrastructure-engineer
  reviewers: [code-review]
  risk: low
  security_review: false
  review_round: 2
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live ECR
  updated: 2026-10-07T14:30:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 53531
    spawns: 1   # infrastructure-engineer (fresh), resumed once for the fix round
    status: ok   # human-reported /usage under ~40%
    checked: 2026-10-07T14:30:00+02:00
---

## H1 — decided by the human, 2026-10-07

**Stage 0 finding that shapes the rule:** each deploy pushes a multi-arch **index** (tagged `latest` + `<sha>`) and 2 per-arch child manifests (up to 4 with attestations), and **the children are untagged**. Live: domain-service 11 untagged / 3 indexes, bff-node 8 / 3. T-035's rule keeps only the 20 newest *untagged*, so once more than ~5 deploys accumulate it expires the children of older sha-tagged indexes, leaving a `:<sha>` tag that no longer pulls (a silent rollback break). Sha retention must therefore fit the untagged budget.

1. **Retention: 5 deploys of rollback depth, untagged budget unchanged at 20.** Rule 1 selects tag prefix `latest` (`imageCountMoreThan 1`, so it never expires; ECR never lets a lower-priority rule expire an image a higher-priority rule's tag selection matched, so `:latest` stays protected even after a rollback re-tags an older image). Rule 2 keeps the **4 newest other tagged images** (`tagPatternList ["*"]`): `latest` + 4 = 5 indexes × ≤4 children = ≤20, inside rule 3, the untagged rule (20, unchanged). Both repos.
2. **Proof:** before the apply, `start-lifecycle-policy-preview` with the new policy shows nothing current would expire; after it, `docker manifest inspect` shows `:latest` and every kept sha still resolve with both architectures.
3. **Budget:** `/usage` under ~40%: the whole task this window.

## Implement, review, live — 2026-10-07 (cv-infra#41)

- **Developer** (fresh infrastructure-engineer, about 54k tokens across the build and one fix round):
  - one shared `local.ecr_lifecycle_policy` for both repos;
  - `terraform test` run `t050_ecr_lifecycle_rules`, plan-only and target-scoped;
  - runbook and CLAUDE.md updated.
- **Review round 1** (`/code-review` medium on e577531; scope matched): 9 findings, all accepted.
  - **An H1 design error.** Lower-priority ECR rules still *count* images a higher rule claimed ("as if they haven't been expired"). So rule 2's `imageCountMoreThan 4` would have kept `latest` + 3, not + 4. It is now **5**.
  - Rule 1 is an exact `tagPatternList ["latest"]`; the prefix list also matched `latest-*`.
  - Both workflows build with `provenance: false` (checked), so each deploy leaves exactly **2** children. The untagged budget is now derived: rule 3 = keep 5 × children 2 + orphan headroom 10 = 20 (unchanged). The headroom absorbs failed merges and same-sha re-runs.
  - Tautological tests were replaced by assertions that can fail (two mutations proven).
  - The header comment no longer says tagged images are never touched.
  - The runbook no longer promises a tarball fallback: `~/.local/share/cv-image-backups/` is a partial manual archive with no BFF images. Rollback beyond retention means rebuilding the commit.
- **Round 2** (bed7dd7): the driver read the fix diff; 27/27 tests passed. Non-blocking nit: a stray `#` in the header comment ("at # $0.10").
- **Live:**
  - `start-lifecycle-policy-preview` with the final policy on both repos: **0 images would expire**. The first draft's preview was also 0.
  - State backed up (`2026-10-07/pre-t050.tfstate`). The plan replaced exactly the two lifecycle policies (the provider replaces a policy on any change). **2 added, 2 destroyed.** The branch plans No changes.
  - Live policies read back: `(1, latest, 1)`, `(2, *, 5)`, `(3, untagged, 20)` on both repos.
  - **Every tagged index still resolves both architectures:**
    - domain-service `latest`/`b0a32e6` and `f487615`;
    - bff-node `latest`/`1037ea6`.
- **Not provable today:** the first real expiry. With 3 and 2 tagged indexes, nothing is over the limit yet; the 6th domain-service deploy is the first that expires a sha.

## Why

Found at T-112/T-203's review (non-blocking), filed by the 2026-10-06 board review. Every automated deploy pushes `:latest` **and** an immutable `:<sha>` multi-arch image (~100 MB). T-035's lifecycle rule expires only **untagged** images, so sha-tagged ones accumulate without bound (ECR storage $0.10/GB-month: cents now, unbounded later).

## Scope

- A lifecycle rule on both repos that keeps the **last N (e.g. 10) sha-tagged images** and never touches `:latest`. ECR rules match `tagPatternList`; sha tags are 40 hex chars, so use a pattern that can't match `latest`. Keep T-035's untagged rule.
- `terraform test` assertion; the runbook's rollback note says only the last N shas are kept.

## Acceptance criteria

- [x] Applied; `aws ecr get-lifecycle-policy-preview` shows only old sha tags would expire, never `:latest`.
