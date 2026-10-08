---
id: T-054
title: "cv-infra: ship the app containers' logs to the existing CloudWatch log groups (awslogs driver), so production logs survive a host replacement"
repo: cv-infra
status: done
owner: tech-product-owner
branch: feat/app-logs-to-cloudwatch
pr: https://github.com/erfeamor/cv-infra/pull/42
depends_on: [T-052]
risk: high   # changes every container's run arguments (cv-app.sh), so the app host is replaced once
security_review: true   # a new IAM grant on the app host's role; logs could carry request data
checkpoint:
  stage: done   # merged f91334d (squash of cv-infra#42), 2026-10-08 — applied from the branch first; H2 accepted; master plans No changes
  repo: cv-infra
  branch: feat/app-logs-to-cloudwatch
  worktree: none
  commit: f91334d
  pr: https://github.com/erfeamor/cv-infra/pull/42
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: high
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live app host (replaced once)
  updated: 2026-10-08T10:00:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 225000   # developer ~96k (build + 1 fix round), security sub-task ~49k, reviews forked
    spawns: 2   # infrastructure-engineer (fresh, resumed once) + security-review identification sub-task
    status: ok   # human-reported /usage under ~40%
    checked: 2026-10-08T10:00:00+02:00
---

## H1 — decided by the human, 2026-10-08

1. **Containers:** domain-service and bff-node only, into their existing groups. MySQL stays on `docker logs`: it's started by the bootstrap, not `cv-app.sh`, and has no group.
2. **Driver mode:** `mode=non-blocking`, `max-buffer-size=4m`. The apps never stall on logging; a long CloudWatch outage drops the oldest buffered lines, and `docker logs` keeps working (dual logging).
3. **Stream name** (driver's call, recorded): `<container>-<instance id>` (from IMDS at run time in `cv-app.sh`), so each host replacement starts fresh streams and old ones age out under the 14-day retention.
4. **Budget:** `/usage` under ~40%: the whole task this window, including the host replacement.

## Implement, review, live — 2026-10-08 (cv-infra#42)

- **Developer** (fresh infrastructure-engineer): awslogs in the shared `cv_run_domain_service`/`cv_run_bff_node` (non-blocking, 4m, stream `<container>-<instance id>`), group names as template vars, `aws_iam_role_policy.app_write_container_logs` (CreateLogStream + PutLogEvents on the two groups' `:*`), harness + `terraform test` + check-static, runbook "Reading the logs".
- **`/code-review` high (0fe28a6): 10 findings, 7 fixed.**
  - The instance id now comes from cloud-init's `/var/lib/cloud/data/instance-id`, not IMDS. That removes a network dependency at boot under `set -e`, and a second IMDS call after `docker rm -f` in `roll`. The file was confirmed on the live host first.
  - The instance `depends_on` the new grant, enforced by check 18. This was also a driver finding.
  - The check was renumbered 22 and widened to managed CloudWatch/Logs policy attachments.
  - The runbook now says non-blocking mode drops the *newest* lines and that a missing grant is silent.
  - domain-service gets `awslogs-datetime-format`, so a stack trace is one event.
  - Not fixed: the plan test's resource assertion (the ARNs are unknown at plan time; check-static guards the references), the 27 copied fixtures (pre-existing), and the pre-existing T-044 hazard that `param()` SSM reads happen after `docker rm -f` in `roll`. Filed as [T-055](T-055-cv-redeploy-resolve-inputs-before-rm.md) at H2.
  - The reviewer confirmed from Docker's source that in non-blocking mode the stream is created in the background with retries, so a missing grant or an outage never stops a container from starting.
- **`/security-review` (ca622cd): no findings.** Only stdout/stderr ship, never the `-e` environment. cv-domain-service has no logging code of its own (Spring/Hikari/Hibernate INFO, no `show-sql`, no request logging). cv-bff-node prints only the listening port, a token-failure message designed never to contain the secret, and 500-handler errors without headers. No Authorization header, request body or email is logged.
- **Live, 2026-10-08, applied from the branch:**
  - **Before:** backup `cv-20261008T013031Z.sql.gz`; row baseline 1/7/3/2/30/30 at V2; state `2026-10-08/pre-t054.tfstate`.
  - **Plan:** policy, S3 object, hash, and the instance + EIP association + volume attachment replaced. **4 added, 2 changed, 3 destroyed.** The policy was created before the instance (the ordering fix). New host `i-0ec8607bffc070d6a`; the public CV was back to 200 after **138 s**.
  - **Host:** cloud-init done. Both apps run `awslogs` with the exact options (domain-service also has the datetime format); mysql stays on json-file. Rows identical (1/7/3/2/30/30, V2). Volume `/dev/nvme1n1` mounted, backup timer enabled. `docker logs` still works (dual logging).
  - **CloudWatch:**
    - domain-service stream `domain-service-i-0ec8607bffc070d6a`: 26 events, including the request-driven `DispatcherServlet` lines; the Spring banner is one multi-line event.
    - bff-node: the "listening" line.
    - A regex scan for password/secret/Bearer/JWT found nothing.
  - **`cv-redeploy bff-node`** (its SSM document): Success. The new container kept the driver, the stream went from 1 to 2 events, and the CV was 200.
  - **IAM:** the live policy was read back, exact. **The IAM simulator can't evaluate CloudWatch Logs resource ARNs**: even a `Resource: "*"` policy returns implicitDeny for any concrete log-stream ARN. So it was replaced by real probes from the host. CreateLogStream in the doorbell's group, CreateLogGroup and GetLogEvents on its own group are all **AccessDenied**. Neither managed policy on the role grants a `logs:` action.
  - The branch plans **No changes**.

## Why

Decided at [T-052](T-052-observability-scope-decision.md) (2026-10-07). Today production logs exist only as `docker logs` (json-file) on the app host. They vanish with every host replacement and can only be read through SSM; T-044 and T-503 both had to read the host directly. `cv-infra/observability.tf` already provisions `/cv-project/cv-domain-service` and `/cv-project/cv-bff-node` (14-day retention), but nothing writes to them (0 bytes stored).

**Measured 2026-10-07:** domain-service ~7 KB since its 09:15Z start, bff-node ~1.7 KB in ~19 h, mysql ~2.5 KB in ~2 days. That is kilobytes a day, so CloudWatch ingest and storage cost about $0.

## Scope

- **One definition:** add `--log-driver awslogs` with `awslogs-region`, `awslogs-group` (the service's group) and `awslogs-stream` (the container name, or include the instance id) to `cv_run_domain_service` and `cv_run_bff_node` in the shared `/usr/local/lib/cv-app.sh` library. That way the bootstrap and `cv-redeploy` both pick it up, never two copies. Decide at H1 whether MySQL (a third group) and the one-shot Flyway run join them.
- **The driver runs in dockerd on the host**, not in the containers, so it uses the instance role through IMDS. The host's IMDSv2 hop limit of 1 (T-035) blocks containers, not dockerd; confirm this live.
- **IAM:** an app-host role policy granting `logs:CreateLogStream` and `logs:PutLogEvents` on **those groups' ARNs only** (`…:log-group:/cv-project/cv-*:*`, or the two exact ARNs). No `CreateLogGroup`, no `*`.
- **Failure mode:** decide `mode=non-blocking` (with a `max-buffer-size`) versus the default blocking mode. Blocking can stall a container when CloudWatch is unreachable; non-blocking can drop lines under pressure. `docker logs` keeps working either way through docker's dual logging.
- Offline: `terraform test` asserts the grant's exact actions and resources; the `cv-redeploy` harness asserts the driver flags are in the shared definition only.
- Runbook `app-host-deploy.md`: where logs are now, how to read them (`aws logs tail /cv-project/cv-domain-service --follow`), and the 14-day retention.

## Acceptance criteria

- [x] Applied (one host replacement, done the way T-044/T-035 did it). After it, both groups receive log events from the running containers, including one request's log line made through CloudFront.
- [x] `cv-redeploy domain-service` keeps the driver (the new container still logs to the group).
- [x] The role can write only to those groups (IAM simulator), and no secret shows up in the shipped logs (spot-check the startup lines).
- [x] Gates green; `/security-review` clean.

## Watch-outs

- **Don't change `db_password`** (T-021).
- Run-argument changes replace the host (T-044's model), so save the images' digests first. Since T-050, ECR keeps `latest` + 4 shas.
