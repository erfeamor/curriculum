---
id: T-045
title: "cv-infra: a GitHub Actions OIDC provider and a deploy role for cv-public-vanilla (bucket root, never admin/)"
repo: cv-infra
status: in_review
owner: tech-product-owner
branch: feat/github-oidc-public-vanilla
pr: https://github.com/erfeamor/cv-infra/pull/34
depends_on: []
risk: normal   # IAM only: no host or edge change
security_review: true   # a new trust relationship (GitHub → AWS) and a write role on the frontend bucket — adapter §5 IAM + CI-credential paths
checkpoint:
  stage: h2   # applied 2026-10-04 from the branch (IAM only); simulator 10/10 as designed; awaiting human acceptance
  repo: cv-infra
  branch: feat/github-oidc-public-vanilla
  worktree: none   # main cv-infra checkout
  commit: 7aaa1f8
  pr: https://github.com/erfeamor/cv-infra/pull/34
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a
  updated: 2026-10-04T13:00:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 53263
    spawns: 1   # infrastructure-engineer (fresh)
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

## Implement, review and apply — 2026-10-04 (7aaa1f8, cv-infra#34)

- **Developer** (fresh infrastructure-engineer, ~53k tokens): `github-oidc.tf` (the provider with no thumbprint, optional in aws 5.100.0; the role with exact `StringEquals` `aud`/`sub`, 1 h sessions; the inline policy: 3 Allow + 1 Deny on `admin/*`), output `public_vanilla_deploy_role_arn`, a red-first `terraform test` run (scoped `apply` + targets, as `backup_iam_scoping` does), check-static 2b (mutation-checked), a CLAUDE.md line.
- **Process note:** the developer's first, discarded test run was unscoped and reached `null_resource.jenkins_provision`'s local-exec, making **read-only** `aws ssm describe-instance-information` calls with the machine's real credentials against a random mock instance id (it timed out). That breaks the brief's offline rule. CloudTrail shows **no `SendCommand`** in the window; nothing was sent or created. The final run is scoped and takes 14 s.
- **Driver-verified:** diff read; full offline gate green (`terraform test` 19/19). **Review round 1 (code + security): clean.**
- **Apply** (IAM only): 3 added. Role `arn:aws:iam::760904708057:role/cv-project-public-vanilla-deploy`.
- **Live, `simulate-principal-policy`:** allowed: PutObject `index.html`, DeleteObject `assets/old.js`, ListBucket, CreateInvalidation on E2AV0INGJW1UO2. **explicitDeny:** PutObject `admin/index.html`, DeleteObject `admin/assets/index.js`. implicitDeny: an invalidation on another distribution, PutObject on the tfstate bucket, GetObject (not needed for an upload sync), `iam:PassRole`. The trust condition reads back exactly. The branch plans **No changes**.

## Acceptance criteria

- [x] Offline: `terraform test` asserts the provider URL and client id, the trust conditions (exact `sub` for master, `aud`), the four allowed actions and their resources, and the `Deny` on `admin/*`; red first. check-static if a natural home exists.
- [x] Applied (IAM only: the plan touches no instance, bucket or distribution).
- [x] Verified live with the policy simulator (`aws iam simulate-principal-policy`): Put on `index.html` allowed; Put/Delete on `admin/index.html` **denied**; an invalidation on another distribution denied.
- [x] Gates green; `/security-review` clean.
