---
id: T-040
title: "The CI GitHub token Jenkins uses expires 2026-11-06 — rotate it before Jenkins stops checking out code"
repo: cv-infra
status: in_progress
owner: tech-product-owner
branch: feat/jenkins-pat-rotation-trigger
pr:
depends_on: []
risk: normal
security_review: false   # a credential rotation through the existing tfvars → SSM path; no new surface
due: 2026-10-30
checkpoint:
  stage: implement   # H1 2026-11-01
  repo: cv-infra
  branch: feat/jenkins-pat-rotation-trigger
  worktree: none
  commit:
  pr:
  developer: tech-product-owner   # a one-trigger Terraform change + test, driver-written to save quota under the 2026-11-06 deadline
  reviewers: [code-review]
  risk: normal
  security_review: false
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live CI host
  updated: 2026-11-01T12:00:00+01:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
    status: ok   # human-reported /usage 40–75%
    checked: 2026-11-01T12:00:00+01:00
---

## H1 — decided by the human, 2026-11-01

**Stage 0:** `jenkins-provision.sh` reads `ci/github-pat` from SSM and passes it to the Jenkins container as `GITHUB_PAT`. The token is part of `JENKINS_CONFIG_HASH`, so re-running the script recreates **only** the Jenkins container. But `null_resource.jenkins_provision` triggers only on the script's hash and the instance id. An apply would update SSM and leave Jenkins on the old token, and a restart keeps the old env.

1. **Make rotations automatic:** add the token parameter's SSM `version` to `null_resource.jenkins_provision`'s triggers, so a future rotation re-provisions on a plain apply. **This task's own apply does the cutover through that new trigger** (one apply: the SSM value plus the re-provision on the running host, started with `CIKeepAlive`). The human has already put the new fine-grained token in `terraform.tfvars` (2 repos; Commit statuses read/write, Contents/PRs read-only).
2. **Proof:** on the host via SSM (the admin password stays on the host and is never printed), trigger a multibranch scan and a build of `cv-database` master. Then check GitHub for a **new** `continuous-integration/jenkins/branch` status posted after the cutover. Nothing deploys: the migrate workflow runs on pushes, not on statuses.
3. **Reminder:** a dated board task due one month before the new expiry, shown in the lane's Human section; the expiry is also recorded here.
4. **Budget:** `/usage` 40–75%. The change is small and the token expires **2026-11-06**, so implement, review, apply and verify in this window.

## Why

Found on 2026-09-29 (T-034's H1) while checking whether the CI token could manage webhooks. GitHub's response to `/cv-infra` SSM `ci/github-pat` (`aws_ssm_parameter.github_pat_ci`, fed from `var.github_pat_ci`) carries **`github-authentication-token-expiration: 2026-11-06 07:53:53 UTC`**. Jenkins' `github-pat` credential (JCasC in `templates/jenkins-provision.sh`) is that value. When it expires, both Jenkins pipelines (`cv-domain-service`, `cv-database`) can no longer scan or check out, and the failure looks like a GitHub auth error in the build rather than a calendar event.

## Scope

- **The human** creates a replacement fine-grained token with the same repositories and permissions as today, sets `github_pat_ci` in `terraform.tfvars`, and revokes the old one after the cutover.
- Apply (this updates the SSM value). Re-provision Jenkins so its credential picks up the new value; check whether `null_resource.jenkins_provision` needs a trigger, or a host restart is enough. Prove a Jenkins scan and build are green.
- Record the new expiry here, and consider a reminder (e.g. an item in T-012's human list or a calendar entry).

## Acceptance criteria

- [ ] The new token is in SSM, and Jenkins uses it: a scan and a `master` build are green after the cutover.
- [ ] The old token is revoked on GitHub.
- [ ] The new expiry date is recorded on this task and in a place a human will see it before it lapses.

## Provenance

Filed by the driver on 2026-09-29 during T-034's H1. Not in T-034's scope: T-034 needs a *different* token (webhooks on `cv-admin-react` only).
