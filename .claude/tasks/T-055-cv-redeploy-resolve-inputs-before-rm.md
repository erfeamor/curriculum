---
id: T-055
title: "cv-infra: `cv-redeploy` removes the running container before reading its SSM parameters — a failed read leaves the service down"
repo: cv-infra
status: in_review
owner: tech-product-owner
branch: fix/cv-redeploy-resolve-before-rm
pr: https://github.com/erfeamor/cv-infra/pull/43
depends_on: [T-054]
risk: normal   # changes cv-app.sh/cv-redeploy, so applying replaces the app host
security_review: true   # touches the code path that handles the DB password and the BFF client secret
checkpoint:
  stage: h2   # applied from the branch 2026-10-08; host i-05c8e011117d30b34; both SSM redeploys green; awaiting H2
  repo: cv-infra
  branch: fix/cv-redeploy-resolve-before-rm
  worktree: none
  commit: 680a6ba
  pr: https://github.com/erfeamor/cv-infra/pull/43
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 2
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live app host (replaced once)
  updated: 2026-10-08T12:00:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 146000   # developer ~102k (build + 2 fix rounds), security sub-task ~44k
    spawns: 2   # infrastructure-engineer (fresh, resumed twice) + security sub-task
    status: ok   # human-reported /usage 40–75% (apply window, no subagents)
    checked: 2026-10-08T12:00:00+02:00
---

## H1 — decided by the human, 2026-10-08

1. **Split resolve / start.** Each service gets `cv_resolve_<svc>`, which does every SSM read plus the instance id into non-exported shell variables, and `cv_start_<svc>`, which runs the `docker run` with exactly today's arguments. `cv_run_<svc>` is resolve then start, so the bootstrap path is unchanged. `roll` becomes pull → resolve → `docker rm -f` → start. There is still one definition of the run arguments. Rejected: start-new-then-swap (collides on the published ports 8080/3000; a redesign).
2. **Apply:** one host replacement (as in T-054), with a backup and row baseline first, then both SSM redeploy documents proven live.
3. **Budget:** `/usage` 40–75%: implement and review, then **checkpoint before the apply**.

## Live — 2026-10-08, applied from the branch (cv-infra#43 @ 680a6ba)

- **Before:** backup `cv-20261008T094624Z.sql.gz`; rows 1/7/3/2/30/30 at V2; state `2026-10-08/pre-t055.tfstate`.
- **Plan and apply:** the S3 object and hash updated in place; the instance, EIP association and volume attachment replaced. **3 added, 2 changed, 3 destroyed.** New host `i-05c8e011117d30b34`; the public CV was back to 200 after **185 s**.
- **Host:** cloud-init done; rows identical; volume mounted, backup timer enabled. The deployed `cv-app.sh` has 5 `local +x` declarations, and `cv-redeploy`'s `roll` is `"cv_run_${name//-/_}" docker rm -f "$name"`. Both apps still on awslogs.
- **Both SSM redeploy documents, live:**
  - `cv-redeploy-domain-service`: Success, CV 200 after 14 s.
  - `cv-redeploy-bff-node`: Success, CV 200 after 1 s.
  - **Neither command's output contains the DB password or the BFF client secret.** The real values were compared in-process from shredded temp files and never printed.
- The failure path (an SSM read failing leaves the old container serving) is proven by the harness (case 9), not live.
- The branch plans **No changes**.
 — 2026-10-08 (cv-infra#43, 680a6ba)

- **Developer, first pass (0cd8022):** the split H1 asked for (`cv_resolve_*` / `cv_start_*` / `cv_clear_*`, with global non-exported secrets).
- **`/code-review` high:** behaviour correct, but **three mutations passed all 159 checks**:
  - swapping `bff/token-url` and `bff/token-scope` (the stub returned identical values);
  - `return "$rc"` changed to a bare `return`;
  - a cut-down `cv_clear_bff_node`.
- The reviewer proposed a simpler shape that **keeps H1's intent while replacing its mechanism**. The driver accepted it.
  - `cv_run_<svc>` declares its inputs `local`, resolves them all, then runs an optional pre-start hook (`"$@"`), then `docker run` last.
  - `roll` = `cv_run_<svc> docker rm -f <svc>`; the bootstrap calls it unchanged.
  - The secrets are function-local, so `cv_resolve_*`, `cv_start_*` and `cv_clear_*` are gone.
- **Round 1 fixes (b06a377):**
  - unique stub values per parameter, with the golden regenerated from master;
  - the `docker run` failure path is tested;
  - no-leak tests on every path;
  - `cv_need` for `db/password` in Flyway and the boot MySQL run;
  - check 23 rewritten: it strips comments and rejects `|| true` and a bare `rm`;
  - stale comments and docs updated.
  - Every mutation is now caught.
- **Driver finding (680a6ba):** bash 5.3 `local` **inherits an existing export flag**. With a pre-exported `CV_DS_DB_PASSWORD`, child processes (`aws`, `docker`) would receive the SSM secret in their environment; verified in a shell.
  - Inputs are now `local +x`.
  - Case 15 failed 3 checks without it and passes with it.
  - Gate: harness 191/191, `terraform test` 28/28, check-static 28 OK.
- **Security review (680a6ba): no findings.**
  - `cv_need`'s errors name the parameter, never the value.
  - No xtrace, export, `set -a` or `declare -x` anywhere.
  - Nothing new is written to disk.
  - The `printf -v` targets are literals, and dispatch comes from a fixed `case` behind parameterless SSM documents.

## Why

Found by T-054's code review, 2026-10-08, and filed on the human's H2. Pre-existing since [T-044](T-044-app-host-bootstrap-s3-and-redeploy.md). `cv-redeploy`'s `roll` runs `docker rm -f <svc>` first, then calls `cv_run_<svc>`, which reads its parameters from SSM (`param db/password`, `cognito/issuer-uri`, the BFF's four `bff/*` values) **after** the old container is gone. A transient SSM failure, or a parameter the role can no longer read (T-005's Deny-NotResource: a new parameter missing from `app_host_ssm_parameter_names`), makes `cv_run_*` return non-zero. The service then stays down until someone redeploys again, and every automated deploy (T-112/T-203) goes through this path. T-054 already moved the instance-id read before the `rm`; the SSM reads are the rest of the same hazard.

## Scope

- Split each `cv_run_*` into "resolve inputs" (all `param` reads, the instance id) and "start the container", or have `roll` resolve everything first. Then `docker rm -f` happens only once every input is in hand. Secrets stay in local variables only and are never printed or written to disk.
- Keep one definition of the run arguments, shared by the bootstrap and `cv-redeploy`.
- Harness: with an SSM read failing, the running container is **not** removed and the exit is non-zero. The bootstrap path is unchanged.

## Acceptance criteria

- [x] Offline, red first: the harness case above.
- [x] Applied (one host replacement, as in T-054). `cv-redeploy domain-service` and `bff-node` still work live through their SSM documents.
- [x] Gates green; `/security-review` clean.
