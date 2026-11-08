---
id: T-159
title: "Jenkins migration gate replaced by GitHub Actions"
repo: cv-database
status: in_review
owner: infrastructure-engineer
branch: feat/ci-github-actions
pr: https://github.com/erfeamor/cv-database/pull/11
depends_on: [T-060, T-061]
risk: normal
security_review: true
checkpoint:
  stage: H2
  repo: cv-database
  branch: feat/ci-github-actions
  worktree: /home/erfeamor/work/cvdl-worktrees/T-159-cv-database
  developer: infrastructure-engineer
  reviewers: [backend-developer]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-11-08T21:00:00Z
  budget: {turns: 420, spawns: 3, status: ok}
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

This repo's Jenkinsfile runs Flyway 13.7.0 against a throwaway MySQL 8.4. `migrate.yml` waits for that status before migrating production.

## Scope

- A reusable gate workflow: a `mysql:8.4` service container, with Flyway run by `docker run --network ${{ job.services.mysql.network }}`. Keep `?allowPublicKeyRetrieval=true` (the meta CLAUDE.md gotcha).
- `ci.yml` runs the gate on PRs. `migrate.yml` (master pushes touching `sql/migrations/**`, plus dispatch) calls it before `cv-redeploy-migrate`.
- Smoke URL `migrate.yml:34` → `https://erfeamor.com`.
- Delete the `Jenkinsfile` and this repo's doorbell webhook (`663035258`).

## Acceptance criteria

- [ ] A PR that adds a broken migration goes red; a dispatch still migrates production.
