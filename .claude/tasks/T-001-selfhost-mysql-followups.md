---
id: T-001
title: "Backup: replace the managed backups lost when MySQL left RDS"
repo: cv-infra
status: done
owner: infrastructure-engineer
branch: feat/mysql-backup-to-s3
pr: https://github.com/erfeamor/cv-infra/pull/15
depends_on: []
risk: normal
security_review: true
checkpoint:
  stage: done               # merged as 56dea10 (cv-infra#15), 2026-08-13
  APPLIED: false            # <-- READ THIS. The code is merged; terraform apply has NOT been run.
  applied_note: "T-001 is `done` against its ratified DoD, which excluded the apply by H1 ruling. It does NOT mean backups are running. Until someone runs `terraform apply`, NO nightly dump exists and the database has exactly the durability it had before this task: one instance volume, no copy. Do not read `done` here as `protected`. The runbook is in cv-infra#15's body; record the apply and the verified restore on this task when they happen."
  repo: cv-infra
  branch: feat/mysql-backup-to-s3
  worktree: none   # cv-infra cannot be worked from a worktree — local backend, tfstate/tfvars live only in the main clone (see T-002's worktree_rationale)
  developer: infrastructure-engineer
  reviewers: [code-review, infrastructure-engineer, security-review]
  risk: normal
  security_review: true   # IAM policy + S3 bucket policy — adapter §5 security paths
  base: 71b0a48
  commit: c784bb3
  pushed: true   # branch on origin; no PR opened
  a1: pass   # fmt -check -recursive clean, validate Success, terraform test 2 passed — re-run independently by the driver
  driver_verified: "IAM least-privilege confirmed by reading the policy: s3:PutObject alone, Resource scoped to bucket ARN + prefix + /*, no s3:* and no bucket-root grant. No credential in any committed file — DB_PASSWORD is read from SSM with --with-decryption at RUN time, not baked into the unit or template. Failure handling verified: set -euo pipefail, mysqldump pipeline failure caught despite gzip always exiting 0, empty-file guard, temp removed on both failure paths, timestamped keys so a bad run cannot clobber the last good dump."
  driver_finding: "NON-BLOCKING, not yet fixed: the dump runs `docker exec mysql mysqldump -u root -p\"$DB_PASSWORD\"`, so the password appears in the host process list and is readable via ps/proc by any local user. Low severity on a single-tenant box with SSM-only access and no other human logins, but it is a textbook finding and the fix is one line — pass it as `docker exec -e MYSQL_PWD=\"$DB_PASSWORD\"` and drop the -p flag. Raised by the driver during A1 verification; hand to the security lens rather than fixing unreviewed."
  security_review_status: PASS   # infrastructure-engineer lens, ran 2026-08-13. No blocking, no critical.
  security_review_result: "IAM least-privilege CONFIRMED by exact-equality assertion, not eyeball. A compromised instance cannot destroy its own backups — no s3:DeleteObject and per-run timestamped keys, so PutObject cannot clobber. SSM read fails closed under set -e before anything is written or uploaded. Default SSE-S3 already covers encryption at rest on this account (created after Jan 2023), so no explicit resource needed. TLS-only bucket policy assessed LOW value here and skipped deliberately on cost grounds, not missed."
  security_findings_applied: "1 non-blocking, in 01242b6: the temp dump landed 0644 under root default umask — the entire database world-readable while on disk. Fixed with umask 077."
  security_finding_deferred: "mysqldump still passes the password via -p, visible in the host process list. Assessed non-blocking: SSM Session Manager is the only shell access and implies root-equivalent already, so the same principal could read the SSM parameter directly. Revisit before the box stops being single-tenant."
  driver_finding_was_wrong: "The driver proposed `docker exec -e MYSQL_PWD=` as the fix. The security lens refuted it: -e lands in the docker CLI's own argv on the host, exactly as visible in ps as -p — it relocates the exposure rather than closing it. Correct fix is --defaults-extra-file or --env-file with a 0600 file so only a filename reaches any command line. Recorded because the wrong fix looks obviously right."
  test_landmine: "tests/plan.tftest.hcl's O7 comment claims `command = apply` is safe under mock_provider. It is NOT: ci.tf's null_resource.jenkins_provision has a local-exec that shells out to real `aws ssm` calls regardless of provider mocking. A full-module apply run block hangs on a 300s SSM timeout and fails teardown. Worked around by scoping the new apply run with plan_options.target. The real terraform.tfstate was verified untouched (terraform test uses ephemeral state). The stale O7 comment is worth correcting in a later PR."
  scope_ruling: "H1 2026-08-13 — build + offline gates + PR only. terraform apply is DEFERRED to the human and is NOT part of this task's DoD."
  data_ruling: "H1 2026-08-13 — the human confirmed the prod MySQL holds only test data, nothing authored. The instance replacement this apply causes therefore loses nothing of value. No pre-apply dump is needed; the restore is verified against a throwaway container per the AC."
---

## Goal

Close the loose ends left by moving MySQL off RDS onto a self-hosted 8.4 container on the domain-service EC2 (cv-infra PR #8). Self-hosting removed the RDS instance cost and the MySQL 8.0 Extended Support charge, but it also dropped RDS's managed backups and left some docs/config referencing the old setup.

## Scope

Nightly logical backup of the self-hosted MySQL, replacing what RDS used to do for free.

- `mysqldump` from the `mysql` container on the domain-service EC2 → `aws s3 cp` to a dedicated bucket/prefix, on a **systemd timer** provisioned via `templates/domain-service-user-data.sh`.
- IAM: extend the instance role (`iam.tf`) with least-privilege `s3:PutObject` **to that prefix only**. No `s3:*`, no bucket-wide grant.
- Retention via an S3 lifecycle rule — a handful of daily dumps, sized to stay negligible against the credit burn (T-010).
- Verify a dump restores into a throwaway MySQL 8.4 container.

**Split note (2026-08-13).** This task was originally three bundled pieces. §2 (dev/prod parity) and §3 (docs drift) are now [T-016](T-016-dev-prod-mysql-parity.md) and [T-017](T-017-docs-drift-rds-to-selfhosted.md), so that `T-014`'s dependency on "T-001" means exactly this backup and nothing else, and so a docs cleanup cannot block an infra chain.

## The instance-replacement trap — read before applying

`compute.tf:49` sets `user_data_replace_on_change = true`, and this task **edits `user_data`**. The apply therefore **replaces the instance**, and MySQL's data at `/var/lib/cv-mysql` (`domain-service-user-data.sh:38,44`) lives on the instance volume, so **it is destroyed**.

That is accepted here, not overlooked: the human confirmed at H1 that the database holds only test data. Two consequences worth carrying forward anyway:

- The admin UI is briefly down across the replacement. Not data loss, but it is user-visible.
- **The moment the demo holds authored content, this trap becomes real** — for this task *and* for T-014, which replaces the instance again. The durable fix is moving MySQL onto its own EBS volume that survives replacement; that is filed as [T-018](T-018-mysql-on-dedicated-ebs-volume.md) rather than smuggled into this one.

## Acceptance criteria

- [ ] A systemd timer + unit is provisioned by `user_data`, dumps the `mysql` container nightly, and uploads to the S3 prefix.
- [ ] IAM is **least-privilege**: `s3:PutObject` scoped to the backup prefix only — not the bucket root, not `s3:*`. A reviewer must be able to see the scoping in the policy resource ARN.
- [ ] The bucket blocks public access and has a lifecycle rule expiring old dumps.
- [ ] `terraform fmt -check -recursive`, `terraform validate`, and `terraform test` all pass **offline** (mocks extended, assertions added for the new resources — the repo requires assertions in the same PR as the resources they pin).
- [ ] The PR body carries an **apply runbook**: the exact commands, the expected plan shape, that the instance is replaced, and how to verify the first dump lands and restores into a throwaway MySQL 8.4 container.
- [ ] No secret in a committed file; no new EIP; no port-22 ingress.

## Definition of done

PR open against `master` from `feat/mysql-backup-to-s3`, offline gates green, runbook written, task updated.

**`terraform apply` is explicitly NOT in this DoD** — ratified at H1. The human runs it, since it churns a live instance and takes the admin UI down briefly. Restore verification happens after that apply and is recorded on this task when it does.

## dev-loop notes

- **Developer:** `infrastructure-engineer` (adapter §2 — `cv-infra`). **Reviewers:** `/code-review` + `infrastructure-engineer` specialist lens + `/security-review`.
- **`security_review: true`** — the diff adds an IAM policy and an S3 bucket, both named security paths in adapter §5. Least-privilege scoping is the thing to review hardest.
- Gates (adapter §3): `terraform fmt -check -recursive` · `terraform validate` · `terraform test`, from `cv-infra/`. No CI system in this repo — the gates are the local commands.
- `terraform apply` stays in `ask` in `settings.local.json` **on purpose**. Do not allowlist it.
- **cv-infra cannot be worked from a git worktree** while the backend is local — `terraform.tfstate` and `terraform.tfvars` exist only in the main clone and are gitignored. See T-002's `worktree_rationale`.
