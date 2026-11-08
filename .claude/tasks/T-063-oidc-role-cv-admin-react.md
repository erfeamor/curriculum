---
id: T-063
title: "OIDC deploy role for cv-admin-react (replaces Drone's static key)"
repo: cv-infra
status: in_progress
owner: infrastructure-engineer
branch: feat/admin-oidc-role
pr:
depends_on: [T-060]
risk: normal
security_review: true
checkpoint:
  stage: 1
  repo: cv-infra
  branch: feat/admin-oidc-role
  worktree: /home/erfeamor/work/cvdl-worktrees/T-063-cv-infra
  developer: infrastructure-engineer
  reviewers: [infrastructure-engineer]
  risk: normal
  security_review: true
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-11-08T23:00:00Z
  budget: {turns: 0, spawns: 0, status: ok}
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

- [ ] The role can't write outside `admin/*` (proved with the policy simulator or a real denied call).
