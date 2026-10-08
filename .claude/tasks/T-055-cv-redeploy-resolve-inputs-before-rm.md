---
id: T-055
title: "cv-infra: `cv-redeploy` removes the running container before reading its SSM parameters — a failed read leaves the service down"
repo: cv-infra
status: in_progress
owner: tech-product-owner
branch: fix/cv-redeploy-resolve-before-rm
pr:
depends_on: [T-054]
risk: normal   # changes cv-app.sh/cv-redeploy, so applying replaces the app host
security_review: true   # touches the code path that handles the DB password and the BFF client secret
checkpoint:
  stage: implement   # H1 2026-10-08
  repo: cv-infra
  branch: fix/cv-redeploy-resolve-before-rm
  worktree: none
  commit:
  pr:
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live app host (replaced once)
  updated: 2026-10-08T12:00:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
    status: ok   # human-reported /usage 40–75%: implement + review, checkpoint before the apply
    checked: 2026-10-08T12:00:00+02:00
---

## H1 — decided by the human, 2026-10-08

1. **Split resolve / start.** Each service gets `cv_resolve_<svc>`, which does every SSM read plus the instance id into non-exported shell variables, and `cv_start_<svc>`, which runs the `docker run` with exactly today's arguments. `cv_run_<svc>` is resolve then start, so the bootstrap path is unchanged. `roll` becomes pull → resolve → `docker rm -f` → start. There is still one definition of the run arguments. Rejected: start-new-then-swap (collides on the published ports 8080/3000; a redesign).
2. **Apply:** one host replacement (as in T-054), with a backup and row baseline first, then both SSM redeploy documents proven live.
3. **Budget:** `/usage` 40–75%: implement and review, then **checkpoint before the apply**.

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
