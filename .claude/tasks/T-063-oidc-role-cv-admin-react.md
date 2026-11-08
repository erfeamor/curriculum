---
id: T-063
title: "OIDC deploy role for cv-admin-react (replaces Drone's static key)"
repo: cv-infra
status: done
owner: infrastructure-engineer
branch: feat/admin-oidc-role
pr: https://github.com/erfeamor/cv-infra/pull/59
depends_on: [T-060]
risk: normal
security_review: true
checkpoint:
  stage: done
  repo: cv-infra
  branch: feat/admin-oidc-role
  worktree: none
  developer: infrastructure-engineer
  reviewers: [infrastructure-engineer]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-11-08T23:00:00Z
  budget: {turns: 60, spawns: 2, status: ok}
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

Drone deploys the admin with a static IAM key (`cv-project-drone-deploy`, T-008). Actions needs a keyless role instead.

## Scope

- Mirror `public_vanilla_deploy` (`github-oidc.tf:26-86`) inverted: write **only** under `admin/*` in the frontend bucket, and allow `cloudfront:CreateInvalidation` on this distribution.
- Trust exactly `repo:erfeamor/cv-admin-react:ref:refs/heads/master` (`StringEquals` on `aud` and `sub`).
- Add an output and set the repo variable `AWS_DEPLOY_ROLE_ARN` on cv-admin-react.
- check-static guards the prefix scope and the exact trust.

## Acceptance criteria

- [x] The role can't write outside `admin/*` (proved with the policy simulator or a real denied call).

## DONE (2026-11-09)

cv-infra#59 merged and applied (role and role policy only). `cv-project-admin-deploy`: trust is `StringEquals` on `aud` = `sts.amazonaws.com` and `sub` = `repo:erfeamor/cv-admin-react:ref:refs/heads/master`; policy `frontend-admin-deploy` is Put/Delete on `cv-project-frontend-dev/admin/*`, `ListBucket` conditioned on `s3:prefix` (`admin/*`, `admin/`), and `cloudfront:CreateInvalidation` on distribution `E2AV0INGJW1UO2`. cv-infra check-static 32 pins exactly those three statements and the exact trust. An independent security review found no blockers.

Proof on the real role (`simulate-principal-policy`): Put/Delete on `admin/*` allowed; Put on the bucket root and `assets/`, and `GetObject`, denied; invalidation allowed on this distribution and denied on another; `ListBucket` allowed with `s3:prefix=admin/` and denied for `assets/` and an empty prefix. A read-only `aws s3 sync … s3://…/admin/ --delete --dryrun --debug` lists with `prefix=admin/`, matching the condition. The repo variable `AWS_DEPLOY_ROLE_ARN` is set on cv-admin-react (not a secret).

Still to confirm in T-305: a real assume-role from a GitHub run and the first real `sync --delete` through the role. Drone's static key stays until T-305 moves the deploy and T-064 deletes it.
