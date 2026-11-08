---
id: T-305
title: "Drone replaced by GitHub Actions (OIDC deploy)"
repo: cv-admin-react
status: in_review
owner: infrastructure-engineer
branch: feat/ci-github-actions
pr: https://github.com/erfeamor/cv-admin-react/pull/18
depends_on: [T-063]
risk: normal
security_review: true
checkpoint:
  stage: H2
  repo: cv-admin-react
  branch: feat/ci-github-actions
  worktree: /home/erfeamor/work/cvdl-worktrees/T-305-cv-admin-react
  developer: infrastructure-engineer
  reviewers: [infrastructure-engineer]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-11-09T08:00:00Z
  budget: {turns: 70, spawns: 2, status: ok}
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

Drone builds and deploys the admin on the CI host with a static IAM key.

## Scope

- Move the `.drone.yml` steps to Actions: install, lint, typecheck, test, build, build-storybook. Use Node 22, because Drone's `node:20` is past end of life.
- **Master deploy:** OIDC (role from T-063), `aws s3 sync` to `admin/` and invalidate `/admin/*`, mirroring cv-public-vanilla's `ci.yml:101-123`. Keep the `VITE_*` build values, still on the old Cognito domain (T-306 changes it).
- Delete `.drone.yml` and both webhooks: the doorbell (`689017760`) and Drone (`687961843`).

## Acceptance criteria

- [ ] A master push deploys the admin, and a human login and save work.
