---
id: T-054
title: "cv-infra: ship the app containers' logs to the existing CloudWatch log groups (awslogs driver), so production logs survive a host replacement"
repo: cv-infra
status: todo
owner:
branch: feat/app-logs-to-cloudwatch
pr:
depends_on: [T-052]
risk: high   # changes every container's run arguments (cv-app.sh), so the app host is replaced once
security_review: true   # a new IAM grant on the app host's role; logs could carry request data
---

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

- [ ] Applied (one host replacement, done the way T-044/T-035 did it). After it, both groups receive log events from the running containers, including one request's log line made through CloudFront.
- [ ] `cv-redeploy domain-service` keeps the driver (the new container still logs to the group).
- [ ] The role can write only to those groups (IAM simulator), and no secret shows up in the shipped logs (spot-check the startup lines).
- [ ] Gates green; `/security-review` clean.

## Watch-outs

- **Don't change `db_password`** (T-021).
- Run-argument changes replace the host (T-044's model), so save the images' digests first. Since T-050, ECR keeps `latest` + 4 shas.
