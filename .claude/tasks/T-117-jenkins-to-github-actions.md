---
id: T-117
title: "Jenkins replaced by GitHub Actions"
repo: cv-domain-service
status: in_progress
owner: infrastructure-engineer
branch: feat/ci-github-actions
pr:
depends_on: [T-060, T-061]
risk: normal
security_review: true
checkpoint:
  stage: 1
  repo: cv-domain-service
  branch: feat/ci-github-actions
  worktree: /home/erfeamor/work/cvdl-worktrees/T-117-cv-domain-service
  developer: infrastructure-engineer
  reviewers: [backend-developer]
  risk: normal
  security_review: true
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-11-08T21:00:00Z
  budget: {turns: 0, spawns: 0, status: ok}
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

Phase B of M3 deletes the CI host. This repo's Jenkinsfile is its PR gate, and `deploy.yml` polls Jenkins' commit status before deploying.

## Scope

- Move the Jenkinsfile stages into a **reusable workflow** (`workflow_call`): checkstyle, `mvn test`, package, and the Docker image build (`Jenkinsfile:50-53`). `ci.yml` calls it on PRs and pushes; `deploy.yml` calls it instead of polling Jenkins (`:33-68`). `needs:` can't cross workflows.
- **No `environment:`** on the deploy job: it changes the OIDC `sub` claim, and the trust matches `ref:refs/heads/master` exactly.
- Smoke URL `deploy.yml:30` → `https://erfeamor.com`.
- Delete the `Jenkinsfile` and this repo's doorbell webhook (`663034880`).
- **Decide at H1:** arm64-only images. It saves only cents and touches `cv-infra/CLAUDE.md:91`; take the same decision as T-212.

## Acceptance criteria

- [ ] A PR run and a master run are green; a master push still deploys and the smoke test passes.
- [ ] No webhook points at the doorbell.
