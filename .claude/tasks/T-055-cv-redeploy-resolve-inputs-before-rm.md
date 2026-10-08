---
id: T-055
title: "cv-infra: `cv-redeploy` removes the running container before reading its SSM parameters — a failed read leaves the service down"
repo: cv-infra
status: todo
owner:
branch: fix/cv-redeploy-resolve-before-rm
pr:
depends_on: [T-054]
risk: normal   # changes cv-app.sh/cv-redeploy, so applying replaces the app host
security_review: true   # touches the code path that handles the DB password and the BFF client secret
---

## Why

Found by T-054's code review, 2026-10-08, and filed on the human's H2. Pre-existing since [T-044](T-044-app-host-bootstrap-s3-and-redeploy.md). `cv-redeploy`'s `roll` runs `docker rm -f <svc>` first, then calls `cv_run_<svc>`, which reads its parameters from SSM (`param db/password`, `cognito/issuer-uri`, the BFF's four `bff/*` values) **after** the old container is gone. A transient SSM failure, or a parameter the role can no longer read (T-005's Deny-NotResource: a new parameter missing from `app_host_ssm_parameter_names`), makes `cv_run_*` return non-zero. The service then stays down until someone redeploys again, and every automated deploy (T-112/T-203) goes through this path. T-054 already moved the instance-id read before the `rm`; the SSM reads are the rest of the same hazard.

## Scope

- Split each `cv_run_*` into "resolve inputs" (all `param` reads, the instance id) and "start the container", or have `roll` resolve everything first. Then `docker rm -f` happens only once every input is in hand. Secrets stay in local variables only and are never printed or written to disk.
- Keep one definition of the run arguments, shared by the bootstrap and `cv-redeploy`.
- Harness: with an SSM read failing, the running container is **not** removed and the exit is non-zero. The bootstrap path is unchanged.

## Acceptance criteria

- [ ] Offline, red first: the harness case above.
- [ ] Applied (one host replacement, as in T-054). `cv-redeploy domain-service` and `bff-node` still work live through their SSM documents.
- [ ] Gates green; `/security-review` clean.
