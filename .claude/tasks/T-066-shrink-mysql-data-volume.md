---
id: T-066
title: "Shrink the MySQL data volume from 8 GB to 2 GB"
repo: cv-infra
status: done
owner: claude
branch: feat/shrink-mysql-volume
pr: cv-infra#52
depends_on: []
risk: high
security_review: true
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

The data is a few MB, and the 8 GB volume costs ~$0.74/month; a 2 GB one costs ~$0.19. The 8 GB root is the AMI's minimum and stays.

## Scope

- Run a planned swap:
  1. `systemctl start mysql-backup.service`, and keep a local copy
  2. create a new 2 GB `aws_ebs_volume`
  3. restore from the dump
  4. switch the attachment
  5. retire the old volume (its `final_snapshot` is kept)
- `prevent_destroy` (`storage.tf:193-195`) means a deliberate two-step change. Document it as a runbook.

## Acceptance criteria

- [x] Row counts match before and after, and the public CV is unchanged.

## DONE 2026-11-07

- cv-infra#52: the 2 GiB `aws_ebs_volume.mysql_data_v2` (`var.mysql_volume_size_gb`) replaces the 8 GiB `mysql_data`, which a `removed { destroy = false }` block forgot instead of destroying (a size change would have been an in-place modify that AWS rejects mid-apply, so this was a new resource, not a resize). `mysql` now runs with `--binlog-expire-logs-seconds=604800`. Runbook: `cv-infra/docs/runbooks/mysql-volume.md`.
- Review: code-review (8 findings: 6 taken, mostly runbook ordering and readiness gates; 2 rejected) and security-review (none). check-static check 27, 8 mutants red.
- Rollout (human applied, driver restored): backup `cv-20261107T184011Z.sql.gz`, apply (4 add, 2 change, 3 destroy; the old volume only forgotten), restore via a 15-minute presigned URL, no IAM change.
- Verified: per-table row counts identical (education 3, experience 8, flyway_schema_history 2, person 1, person_skill 30, project 2, skill 30); sha256 of `/bff/api/v1/people/1/cv` identical before and after; `/` `/admin/` and react.erfeamor.com 200; `/api` 401 without a token; `/var/lib/cv-mysql` 2.0G with 13% used; backup timer active; a plan afterwards shows no changes. The app host is now `i-01d65fad1c681070c`. The apply and the restore took the API down for about 7 minutes (the first checks hit 500/504 while the containers were still starting).
- **Still open (moved to T-069):** the old 8 GiB volume `vol-092113db466c84bc1` is detached and still bills ~$0.74/month. After a few days of the new volume being fine (not before 2026-11-14), snapshot it and delete it (runbook step 6), then delete the `removed` block in `storage.tf`. Until then the saving is not realised.
