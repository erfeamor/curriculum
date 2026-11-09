---
id: T-058
title: "Rotate Jenkins' GitHub token again: the current one expires 2027-01-30"
repo: cv-infra
status: done
owner: infrastructure-engineer
branch: chore/rotate-jenkins-pat-2027
pr: none   # a rotation through terraform.tfvars + apply needs no code change since T-040
depends_on: [T-040]
risk: low
security_review: false
due: 2026-12-30
---

## M3 note (2026-11-07)

[T-064](T-064-delete-ci-host-stack.md) deletes Jenkins with the CI host, which makes this rotation obsolete. **If T-064 hasn't landed by mid-December, rotate anyway**, because the token expires 2027-01-30.

## Why

Filed at [T-040](T-040-jenkins-github-pat-expiry.md)'s H2 (2026-11-02). The fine-grained token Jenkins uses (cv-domain-service + cv-database; Commit statuses read/write, Contents and Pull requests read-only) **expires 2027-01-30**. When it lapses, Jenkins can't scan or post commit statuses, so the domain-service deploy and the cv-database migration (both wait for Jenkins' status) stop.

## How (no code change since T-040)

Follow `cv-infra/CLAUDE.md` § "Rotating Jenkins' GitHub token":
1. **The human** creates a new fine-grained token with the same two repositories and permissions (https://github.com/settings/personal-access-tokens/new) and puts it in `cv-infra/terraform.tfvars` as `github_pat_ci`.
2. Tag the CI host `CIKeepAlive` and start it, then wait until Jenkins is idle.
3. Apply. The token's SSM version triggers `null_resource.jenkins_provision`, which recreates the Jenkins container with the new token.
4. Prove it: a forced `cv-database` master build posts a new green `continuous-integration/jenkins/branch` status (T-040 has the commands). Then remove `CIKeepAlive`.
5. **The human** revokes the old token, and the new expiry is recorded here, with the next dated task filed.

## Acceptance criteria

- [ ] New token in SSM and in Jenkins; a new green commit status after the cutover.
- [ ] Old token revoked; the next expiry recorded and its reminder filed.

## DONE (2026-11-09): closed as obsolete

Not carried out. [T-064](T-064-delete-ci-host-stack.md) deleted the CI host and the user revoked the Jenkins token, so there is nothing to rotate.
