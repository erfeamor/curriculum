---
id: T-069
title: "M3 close: hygiene, budgets, re-measure, docs, tag M3"
repo: cv-infra + cv-project (meta)
status: done
owner: infrastructure-engineer
branch: chore/m3-close
pr: https://github.com/erfeamor/cv-infra/pull/62   # meta: https://github.com/erfeamor/curriculum/pull/144
depends_on: [T-064, T-066, T-068]
risk: normal
security_review: false
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

Close M3 on measured numbers. Depend on T-068 only if T-067 said go; otherwise drop that dependency.

## Scope

- Lifecycle expiry for noncurrent object versions in the artifacts bucket.
- **Retire T-066's old MySQL volume** `vol-092113db466c84bc1` (detached, ~$0.74/month): snapshot, delete (`cv-infra/docs/runbooks/mysql-volume.md` step 6, not before 2026-11-14), then remove the `removed` block in `storage.tf`; delete the snapshot a few weeks later.
- `gross_usage` budget from $30 to about 2× the measured rate. Retire `credit_runway` (`budgets.tf:207-250`) after 2027-07-12, or now with a note.
- **One week after the last host change:** measure in Cost Explorer (`RECORD_TYPE=Usage`; the zone fee posts on the 1st) and `aws freetier get-account-plan-state`.
- **Refresh the docs:**
  - the cost models in `cv-infra/CLAUDE.md` (including the stale `:72` and `:125`) and the meta CLAUDE.md
  - `docs/architecture.md` (diagram, routes, CI)
  - both READMEs
- Tag `M3` with `scripts/release-manifest.sh` and `release-tag.sh`.

## Acceptance criteria

- [x] The measured rate is about $0.28/day (go) or $0.40/day (no-go) (T-065 dropped Spot, 2026-11-07); budgets retuned; `M3` tagged in all 9 repos.

## DONE (2026-11-15)

**Measured** (Cost Explorer, `RECORD_TYPE=Usage`): **$0.287/day**, flat for each full day 2026-11-10..13 (app host `t4g.micro` $0.226, EBS $0.056, S3 $0.003, Cognito machine tokens $0.002; the Route 53 zone fee posts on the 1st). That is the "go" figure the plan aimed for (~$0.28/day), down from ~$0.51/day at M2. With the old data volume gone the expected rate is ~$0.28/day, ~$8.5/month, plus the domain renewal. The account is PAID and ACTIVE with **$99.47** of credits on 2026-11-15; at this rate ~$67 is spent by their expiry on 2027-07-12, so ~$32 expire unused. Measured over four flat days rather than a full week after the last cost-relevant change (the CI host, 2026-11-09), because the rate had not moved.

**cv-infra#62 merged and applied** (plan before: 1 add, then 1 change once `budget_monthly_limit_amount = "17"` was set in the gitignored tfvars; plan afterwards: no changes): an `aws_s3_bucket_lifecycle_configuration` on the artifacts bucket that expires only noncurrent versions after 30 days and aborts incomplete uploads after 7 (no `expiration` block, guarded by check-static and a `terraform test` run, the guard mutation-checked); `gross_usage` budget $30 -> $17; `credit_runway` kept at $160 with a note that it is informational now and can be retired after 2027-07-12; the cost model in `cv-infra/CLAUDE.md` and the meta `CLAUDE.md` refreshed with the measured numbers.

**Old MySQL data volume retired:** snapshot `snap-06959e64ad62b3259` of `vol-092113db466c84bc1` (8 GB, completed) taken 2026-11-15, then the volume deleted on the user's explicit OK (it was detached; the 2 GB volume had served production for a week with no missing write); `terraform plan` stayed empty. **Still to do:** delete the snapshot around 2026-12-15, and drop the now-pointless `removed { from = aws_ebs_volume.mysql_data }` block in `storage.tf` (it changes no plan; the runbook has the commands).

**M3 tag:** `releases/M3.json` records each sibling's `origin/master` commit (cv-database 367a1bb, cv-domain-service f4da5e1, cv-bff-node f1b6b2d, cv-admin-react c154fff, cv-public-vanilla 609342d, cv-public-react 6071115, cv-observability 99b4711, cv-infra ab32705), all clean and up to date when written; the tag is cut with `scripts/release-tag.sh M3` from the commit that adds this file. M3 closes without T-506 (serverless spike) and T-021 (conditional on a password rotation); both stay `todo`.
