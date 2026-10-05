---
id: T-044
title: "App host: move the bootstrap to S3 (user_data is at ~14.6/15.5 KB) and add a `cv-redeploy <service>` command — today a new image only reaches the host by replacing it"
repo: cv-infra
status: in_review
owner: tech-product-owner
branch: feat/app-host-bootstrap-s3-redeploy
pr: https://github.com/erfeamor/cv-infra/pull/35
depends_on: [T-043]   # builds on the bootstrap as T-043 left it (the BFF block last, the service-token env)
risk: high   # replaces the app host (user_data changes) and changes how every container on it is (re)started
security_review: true   # the redeploy path recreates containers carrying secrets (DB password, BFF client secret) — adapter §5 secrets path
checkpoint:
  stage: h2   # applied 2026-10-05 from the branch; S3 boot, V2, cv-redeploy (domain-service, migrate) and versioning all proven live; awaiting human acceptance
  repo: cv-infra
  branch: feat/app-host-bootstrap-s3-redeploy
  worktree: none
  commit: a245998
  pr: https://github.com/erfeamor/cv-infra/pull/35
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: high
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a
  updated: 2026-10-05T00:30:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 93248
    spawns: 1   # infrastructure-engineer (fresh)
    status: ok   # human-reported /usage 40–75%
    checked: 2026-10-05T00:30:00+02:00
---

## H1 — decided by the human, 2026-10-05

1. **Bootstrap to S3, T-009's pattern:** the script under its own key in the existing private `ci_artifacts` bucket, its SHA-256 in SSM, the app host's role allowed `s3:GetObject` on **that key only** plus the SSM read. **The user_data stub embeds the script's SHA-256**, so a script change replaces the host (today's deterministic behavior; `user_data_replace_on_change` stays).
2. **`cv-redeploy migrate | domain-service | bff-node`** on the host: one shared definition of each container's run arguments (written by the bootstrap and sourced by both, never duplicated); pulls `:latest` and recreates only that container; `migrate` runs Flyway exactly as the bootstrap does. New images and migrations never need a host replacement; run-argument changes still go through one.
3. **First live use deploys the pending domain change now** (T-116 not awaited): `cv-redeploy migrate` (V2) → push current domain-service master → `cv-redeploy domain-service` → verify (`version` in responses, a stale PUT → 409, the public CV still 200).
4. **Budget:** `/usage` 40–75%: implement and review, then **checkpoint before the apply**.

> **2026-10-04 — a pending deploy waits on this task.** cv-database **V2** (T-157) and the domain service's `@Version` (T-113, merged 28b948d) are both on master but **not in production**. This task's first live run of `cv-redeploy migrate` then `cv-redeploy domain-service` deploys them (with T-116 if it's ready). Until then, **don't push a domain-service image built from current master to ECR `:latest`**: this task's own host replacement would pull it, and it can only start once V2 has run. (The bootstrap runs Flyway before starting the domain service, so a replacement applies V2 first anyway, but keep the order explicit and verified.)

## Live — 2026-10-05, applied from the branch (cv-infra#35 @ a245998)

- **Before:** ECR digests saved (domain `:latest` `sha256:7ec81aa3…` rev 63f75b0; bff `sha256:0be74fab…` rev 7d34e7d); the current domain image saved locally (`~/.local/share/cv-image-backups/domain-service-63f75b0.tar.gz`); state backed up (`pre-t044.tfstate`); row baseline person 1, experience 1, skill 1, person_skill 1, education 0, project 0; Flyway at V1.
- **Apply** (08:18–08:19Z): 6 added, 0 changed, 3 destroyed (S3 object, SSM hash, one-key grant; the instance, EIP association and volume attachment replaced). New instance `i-00b1c8812747d57f4`; **user_data 1,502 bytes** (was ~14.6 KB).
- **Boot from S3:** the stub fetched and verified the 17.5 KB script (no failure log); `cv-redeploy` (0750) and `/usr/local/lib/cv-app.sh` in place; cloud-init done 08:22:40, all three containers up. **Flyway applied V2 in production** ("now at version v2"; person 1 `version = 0`). Rows identical; backup timer enabled; volume mounted; `/bff/…/cv`, `/` and `/admin/` 200.
- **First `cv-redeploy domain-service`:** pushed domain master **28b948d (T-113)** → `sha256:8f9e343e…`; the command printed old/new image ids and recreated **only** domain-service in **13 s** (bff and mysql untouched).
- **Versioning live** (via the BFF's service token on the host, never printed): GET person → `version 0`, experiences → `[0]`; **a stale PUT (version 99) → 409 `application/problem+json` "Conflict", nothing written**; the correct PUT → 200, `version 1` (same data). **The public CV carries no `version`.**
- **`cv-redeploy migrate`:** "Already up to date" (git pull on the shallow clone) + "2 migrations validated … up to date"; **`cv-redeploy bogus` → exit 2**. The branch plans **No changes**.
- Not exercised: the runbook's `aws ecr put-image` rollback (the local image tarballs are the fallback).

## Implement + review — 2026-10-05 (a245998, cv-infra#35)

- Developer (fresh infrastructure-engineer, ~93k tokens): `app-host-provision.tf` (S3 object `app-host/provision.sh`, SSM `/…/app/provision-sha256`, `s3:GetObject` on that one key); the stub `templates/domain-service-bootstrap.sh` (≈1.4 KB; double hash check, embedded + SSM; `exec`); the script renamed `domain-service-provision.sh` with a shared library `/usr/local/lib/cv-app.sh` (`cv_run_*`); `/usr/local/bin/cv-redeploy migrate|domain-service|bff-node`; runbook `docs/runbooks/app-host-deploy.md`; harness `run-cv-redeploy-tests.sh` (28 checks).
- Driver-verified: no secret among the template vars (all secrets are still read from SSM at run time); the IAM grant is one object ARN; full offline gate green (`terraform test` 21/21 in 19 s, scoped).
- **Review round 1 (code + security): clean.**
- **Unverified offline, to check live:** the S3 fetch and hash at boot; `docker image inspect` ids; `git pull --ff-only` on the shallow clone (the first `migrate`); the runbook's `aws ecr put-image` rollback (not exercised).

## Why this exists

Filed 2026-10-04 by the board review. Two problems with one fix:

1. **user_data is nearly full.** The app host's rendered user_data is ~14,644 bytes (T-043) against the 15,500-byte guard T-014 added (EC2's limit is 16,384). The next bootstrap addition fails the guard. [T-009](T-009-user-data-size-ceiling.md) solved the same wall on the CI host: user_data fetches the real script from a private S3 object, checked against a hash in SSM.
2. **There is no way to deploy a new image without replacing the host.** Images are pushed to ECR `:latest` by hand (T-014, T-043), and the containers' `docker run` arguments, secrets included, exist **only** in the bootstrap script, which runs once at boot. So deploying a new domain-service or BFF image means a full instance replacement (3–5 minutes of admin/API downtime; done twice on 2026-10-01). And [T-112](T-112-domain-service-ci-ecr-deploy.md) and [T-203](T-203-bff-ci-deploy-stage.md) ("roll the container on master") would each have to duplicate those arguments in a pipeline. Nothing in `cv-infra/docs/runbooks/` describes any of this.

## Scope

- **Bootstrap to S3 (T-009's pattern):** the app host's provisioning script becomes a private S3 object with its SHA-256 in SSM; user_data shrinks to a small fetch-verify-run stub. Keep `user_data_replace_on_change`. Keep every current behavior: MySQL on its volume (T-018), Flyway, the backup timer (T-001), the domain service, and the BFF last (T-014 round 1).
- **A host-side `cv-redeploy <service>`** (`domain-service` | `bff-node`): re-read the service's parameters from SSM, `docker pull` its `:latest`, then recreate **only that container** with the **same arguments the bootstrap uses**, from one definition shared by both (no duplicated `docker run` lines). Print the old and new image digests; never print secrets.
- **How it's invoked:** by an operator via `aws ssm send-command`, and later by T-112/T-203's pipelines. The IAM to allow that is T-112/T-203's decision, not this task's.
- **`cv-redeploy migrate`** (added 2026-10-04, T-113's H1): run Flyway exactly as the bootstrap does (same image, same flags, migrations from `cv-database` master), so a new migration reaches production **without a host replacement**. The order for a schema change becomes migrate → redeploy domain-service, since Hibernate validates the schema at startup.
- **A runbook** `docs/runbooks/app-host-deploy.md`:
  - build, push, `cv-redeploy`, verify;
  - rollback to a previous digest;
  - the ECR lifecycle caveat (only the 2 most recent images are kept);
  - when an instance replacement is still needed (bootstrap changes only).

## Acceptance criteria

- [x] The rendered user_data is a small stub (the size guard is updated and records the new size); the full script is in S3, verified by hash before it runs.
- [x] Applied: the host is replaced once by this task; afterwards every container runs as before (the public CV 200 through CloudFront, the admin works, row counts unchanged, the backup timer enabled).
- [x] `cv-redeploy bff-node` and `cv-redeploy domain-service` each recreate only their container *(domain-service proven live, 13 s; bff-node by the harness and the shared code path)*, from a freshly pushed image, with no host replacement and under a minute of that service's downtime. Verified live by digest before and after.
- [x] The run arguments have one source: an offline test fails if the bootstrap and `cv-redeploy` diverge.
- [x] No secret in user_data, the S3 object, logs or command output (the S3 script reads secrets from SSM at run time, as today).
- [x] `cv-redeploy migrate` applies a pending migration live *(V2 was applied by the boot's Flyway, the same `cv_run_flyway`; `migrate` proven as the no-op)* (proven with T-157's V2) and is a no-op when the schema is current.
- [x] The runbook exists and is linked from `cv-infra/CLAUDE.md`.

## Watch-outs

- **Don't change `db_password`** (T-021).
- This replaces the app host; **save the current images' digests** first, as T-014 did, because the ECR lifecycle keeps only 2 images.
- Unblocks: the T-113 + T-116 domain-service deploy (one image, via `cv-redeploy` rather than a host replacement), [T-112](T-112-domain-service-ci-ecr-deploy.md), [T-203](T-203-bff-ci-deploy-stage.md). [T-035](T-035-app-host-to-graviton.md) still replaces the host, but inherits the S3 bootstrap.
