---
id: T-045
title: "cv-infra: a GitHub Actions OIDC provider and a deploy role for cv-public-vanilla (bucket root, never admin/)"
repo: cv-infra
status: in_progress
owner: tech-product-owner
branch: feat/github-oidc-public-vanilla
pr:
depends_on: []
risk: normal   # IAM only: no host or edge change
security_review: true   # a new trust relationship (GitHub → AWS) and a write role on the frontend bucket — adapter §5 IAM + CI-credential paths
checkpoint:
  stage: implement   # split out of T-403 at its H1, 2026-10-04
  repo: cv-infra
  branch: feat/github-oidc-public-vanilla
  worktree: none   # main cv-infra checkout
  commit:
  pr:
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a
  updated: 2026-10-04T13:00:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
    status: ok   # human-reported /usage 40–75%: this task to merge, then checkpoint
    checked: 2026-10-04T13:00:00+02:00
---

## Why

Split out of [T-403](T-403-public-vanilla-deploy.md) at its H1 (2026-10-04). T-403's deploy job runs in GitHub Actions; cv-infra had no GitHub → AWS trust, and the only deploy credential is `drone_deploy`'s static key (bucket-wide write), which [T-005](T-005-ci-secret-blast-radius.md) argues against copying into a second system. [T-203](T-203-bff-ci-deploy-stage.md) reuses the provider later.

## H1 — decided by the human, 2026-10-04 (at T-403's H1)

1. **`aws_iam_openid_connect_provider`** for `https://token.actions.githubusercontent.com`, client id `sts.amazonaws.com`. One per account; T-203 reuses it.
2. **A role for cv-public-vanilla's deploys only.** Trust: `sts:AssumeRoleWithWebIdentity` from that provider, conditions `aud = sts.amazonaws.com` **and** `sub = repo:erfeamor/cv-public-vanilla:ref:refs/heads/master` (StringEquals, not a wildcard). Permissions:
   - `s3:ListBucket` on the frontend bucket;
   - `s3:PutObject`/`s3:DeleteObject` on `<bucket>/*`, **plus an explicit `Deny` of `s3:PutObject`/`s3:DeleteObject` on `<bucket>/admin/*`**: the site deploys to the bucket **root**, where the live admin also lives (`admin/`), so a mis-scoped `sync --delete` must be unable to touch it;
   - `cloudfront:CreateInvalidation` on this distribution's ARN only.
   - Nothing else: no `iam:*`, no other buckets.
3. **An output with the role ARN** (not secret), so the driver can set it as a GitHub repo variable for T-403.
4. **Budget:** `/usage` 40–75%: this task through its apply and merge, then checkpoint before T-403.

## Acceptance criteria

- [ ] Offline: `terraform test` asserts the provider URL and client id, the trust conditions (exact `sub` for master, `aud`), the four allowed actions and their resources, and the `Deny` on `admin/*`; red first. check-static if a natural home exists.
- [ ] Applied (IAM only: the plan touches no instance, bucket or distribution).
- [ ] Verified live with the policy simulator (`aws iam simulate-principal-policy`): Put on `index.html` allowed; Put/Delete on `admin/index.html` **denied**; an invalidation on another distribution denied.
- [ ] Gates green; `/security-review` clean.
