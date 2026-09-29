---
id: T-040
title: "The CI GitHub token Jenkins uses expires 2026-11-06 — rotate it before Jenkins stops checking out code"
repo: cv-infra
status: todo
owner:
branch: chore/rotate-ci-github-pat
pr:
depends_on: []
risk: normal
security_review: false   # a credential rotation through the existing tfvars → SSM path; no new surface
due: 2026-10-30
---

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
