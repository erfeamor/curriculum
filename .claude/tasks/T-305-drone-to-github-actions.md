---
id: T-305
title: "Drone replaced by GitHub Actions (OIDC deploy)"
repo: cv-admin-react
status: done
owner: infrastructure-engineer
branch: feat/ci-github-actions
pr: https://github.com/erfeamor/cv-admin-react/pull/18
depends_on: [T-063]
risk: normal
security_review: true
checkpoint:
  stage: done
  repo: cv-admin-react
  branch: feat/ci-github-actions
  worktree: none
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

- [x] A master push deploys the admin, and a human login and save work.

## DONE (2026-11-09)

[cv-admin-react#18](https://github.com/erfeamor/cv-admin-react/pull/18) merged. `.github/workflows/ci.yml`: a `test` job on Node 22 (lint, typecheck, test, build, a guard that `dist/` has no `localhost:8080`, build-storybook, 25 structural tests) and a master-only `deploy` job that assumes the T-063 role by OIDC (no `environment:`), syncs `admin/` in two passes (immutable assets, then `index.html` no-cache with `--delete`), invalidates `/admin/*` and smoke-tests `https://erfeamor.com/admin/` with a retry. `.drone.yml` is deleted. An independent security review found no blockers.

First master run (`9b72347`) green: assume-role, both syncs and the invalidation worked under the role's exact permissions. Live `/admin/` serves the new bundle with the right cache headers, no `localhost:8080`, and the old Cognito hosted-UI domain. Human acceptance by the user: login and save work.

**Not done here, carried to T-064:** the two cv-admin-react webhooks (Drone `687961843`, doorbell `689017760`) are still in place. They are harmless (Drone's pipeline is gone) and the user has not yet OK'd deleting them; T-064 removes the doorbell Lambda anyway, so delete them first. Drone's static deploy key stays until T-064.
