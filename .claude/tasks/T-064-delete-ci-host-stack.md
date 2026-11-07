---
id: T-064
title: "Delete the CI host stack (Jenkins, Drone, doorbell, reaper)"
repo: cv-infra
status: todo
owner: 
branch: feat/delete-ci-host
pr:
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

- [ ] `describe-instances` shows no CI host; `plan` is clean afterwards.
- [ ] Every repo's PR and master runs are green.
- [ ] No IAM key remains for a deploy path.
