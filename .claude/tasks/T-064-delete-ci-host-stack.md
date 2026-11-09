---
id: T-064
title: "Delete the CI host stack (Jenkins, Drone, doorbell, reaper)"
repo: cv-infra
status: done
owner: infrastructure-engineer
branch: feat/delete-ci-host
pr: https://github.com/erfeamor/cv-infra/pull/60
depends_on: [T-117, T-159, T-305]
risk: high
security_review: true
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

With every pipeline on Actions, the CI host only costs money: its 20 GB EBS bills while it's stopped. **Target: before mid-December.** If this slips, do T-058's rotation anyway; the token expires 2027-01-30.

## Scope

- **Terraform objects:**
  - `aws_instance.drone` and its security group
  - `aws_iam_role.drone`, its instance profile and policies (`iam.tf:134-279`)
  - the doorbell and reaper Lambdas, the Function URL, the EventBridge rule, their IAM and log groups
  - `null_resource` and `local_file` (`ci.tf:259+`) and `ci-provision.tf:152`
  - `random_password` (`ssm.tf:27`)
  - the SSM parameters `ci/*` and `doorbell/github-hooks-token` (`ssm.tf:177-187`)
  - `aws_route53_record.ci`
  - the x86 `data.aws_ami.al2023` (`compute.tf:12-20`)
  - the outputs `drone_server_url` and `ci_doorbell_url`
  - the providers this leaves unused (null, local, archive, random), and the lock file
- **The drone-deploy user:** remove `cv-project-drone-deploy`, its key and `deploy/drone-deploy/*`. Run `aws iam get-access-key-last-used` first.
- **Files:**
  - the `drone-user-data.sh` and `jenkins-*.sh` templates
  - `ci-dns-*.sh` and `drone-reseed-secrets.sh`, with their tests and stubs
  - `lambda/` and `generated/`
  - the Drone and CI-host runbooks
  - the matching check-static checks and `plan.tftest.hcl` runs
  - the cost-model text
- **Human:**
  - revoke **both** GitHub tokens (Jenkins' PAT and `github_hooks_token`)
  - delete the Drone OAuth app
  - remove the `drone_*`, `jenkins_*` and `github_*` lines from `terraform.tfvars`
- **Board:** cancel T-058, closing it as obsolete.

- **Rename `data.aws_route53_zone.ci`** to a neutral name (T-061 kept it, to avoid touching ~10 CI files that this task deletes anyway). It is referenced by `domain.tf` and `tests/plan.tftest.hcl`.

## Acceptance criteria

- [x] `describe-instances` shows no CI host; `plan` is clean afterwards.
- [x] Every repo's PR and master runs are green.
- [x] No IAM key remains for a deploy path.

## DONE (2026-11-09)

[cv-infra#60](https://github.com/erfeamor/cv-infra/pull/60) merged and applied by the user: 0 to add, 0 to change, 41 to destroy (the plan had no replacement of the app host, the data volume, the VPC origins or the `ci_artifacts` bucket). An independent security review found no blockers. The `ci_artifacts` bucket stays (the app host's provision script lives there) and moved to `storage.tf` with the same addresses. Providers null, local, archive and random left `providers.tf` and the lock file. `ci-deploy.tf` and `github-oidc.tf` are untouched.

Verified afterwards (2026-11-09): the CI host `i-0ee24b3d917501c4d` is `terminated`; the only instance is the app host; the CI host's 20 GB volume is gone; no Elastic IP; the IAM users are `erfeamor` and `terraform-admin` (`cv-project-drone-deploy` gone); the only Lambda is the unrelated `health-app-backend`; SSM holds only the app host's eight parameters; no `ci.erfeamor.com` record; log groups `/cv-project/cv-bff-node` and `/cv-project/cv-domain-service` only; no webhooks on any of the nine repos (cv-admin-react's two were deleted 2026-11-09); `terraform plan` from master reports no changes and the lock file is clean. The user revoked the Jenkins and `github_hooks_token` PATs, removed the Drone OAuth app and cleaned the `terraform.tfvars` lines. The doorbell and reaper log data went with the log groups.

Open, not part of this task: the detached old data volume `vol-092113db466c84bc1` (8 GB, the T-066 rollback) still bills until deleted, which T-069 does after 2026-11-14. The `Name`-less 8 GB `vol-0bbabf768498a2ad8` is the app host's root disk. The meta repo's `CLAUDE.md`, README and `docs/architecture.md` still describe Jenkins and Drone and need a docs pass (with the T-069 cost refresh).
