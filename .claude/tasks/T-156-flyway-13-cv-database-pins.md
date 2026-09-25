---
id: T-156
title: "Flyway 10 → 13.7.0 in cv-database — the Jenkins migration gate and scripts/migrate.sh (split from T-155)"
repo: cv-database
status: done
owner: tech-product-owner
branch: chore/flyway-13
pr: https://github.com/erfeamor/cv-database/pull/6
depends_on: [T-155, T-153]   # T-155: the dev pin moves first, so 13 is proven on the dev stack before the gate; T-153: FILE-LEVEL, both edit cv-database/Jenkinsfile (the T-153 → T-152 precedent) — or ride T-153's PR if H1 prefers one Jenkinsfile diff
risk: normal
security_review: true   # adapter §5 — `Jenkinsfile` is an unconditional /security-review path
checkpoint:
  stage: done   # merged 3548284 (squash of cv-database#6), 2026-09-24 — H2 accepted by the human
  repo: cv-database
  branch: chore/flyway-13
  worktree: none   # removed after merge
  pr: https://github.com/erfeamor/cv-database/pull/6
  commit: 3548284   # squash merge on master (branch head was 5cdccab)
  developer: tech-product-owner   # proposed at H1: two image tags and one doc line, done inline
  reviewers: [code-review, infrastructure-engineer, security-review]
  risk: normal
  security_review: true   # adapter §5: Jenkinsfile
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: none   # verification is Jenkins on the CI host plus a local migrate.sh run
  updated: 2026-09-24T16:11:15+02:00
  budget:
    turns: 190   # --since 2026-09-24T10:59:18.694Z
    total_tokens: 22500000
    subagent_tokens: 45054
    spawns: 1   # infrastructure-engineer review (H1: implementation and QA inline)
    status: ok
    checked: 2026-09-24T15:00:44+02:00
---

## H1 + QA record — 2026-09-24 (PR [#6](https://github.com/erfeamor/cv-database/pull/6) @ `5cdccab`)

**H1 (human-approved):** the driver implements inline, and the QA plan is this task's four ACs, run by the driver. One reviewer spawn (`infrastructure-engineer` plus `/security-review`). The meta repo's own "Flyway 10" mentions (`CLAUDE.md:11`, adapter §2 and §3) ride the board-sync PR.

| AC | Evidence | Result |
|---|---|---|
| 1 grep | `git grep -n "flyway/flyway"` → `Jenkinsfile:84`, `scripts/migrate.sh:9`, both `13.7.0` | ✅ |
| 2 Jenkins | PR-6 build 1: SUCCESS, **45 s including the first cold pull** (`Downloaded newer image for flyway/flyway:13.7.0`), `Flyway OSS Edition 13.7.0`, **no** *"upgrade recommended"*, 0 retries, V1 applied, `Deploy skipped due to when conditional`. Read from the console, not inferred from the green | ✅ |
| 3 `migrate.sh` | Throwaway `mysql:8.4` from the repo compose: 13.7.0, V1 applied, `afterMigrate - seed dev` ran (person 1, experience 3, education 2, project 4) | ✅ |
| 4 `allowPublicKeyRetrieval` | `Jenkinsfile:79`, `flyway.conf:6` | ✅ |

**Review (round 1):** no blocking findings. Notes:
- **CI host disk.** No image-prune step exists. 13.7.0 is 428 MB against 283 MB for `:10`. The host has a 30 GiB gp3 root with 12.8 GiB free (Jenkins disk monitor, read during the build), so there is no risk today. Forwarded to [T-007](T-007-ecs-agent-cleanup.md), whose planned ~10 GB root would not fit the current ~17 GiB in use.
- Exact tag rather than digest pin (the same class as `mysql:8.4`).
- Whether 13.x makes an update-check call could not be ruled out offline. Not a credential or auth issue.

## Why this exists

[T-155](T-155-flyway-version-supports-mysql-84.md)'s H1 decided on 2026-09-24 to **bump Flyway to `13.7.0`**, on the evidence in its § *Empirical answers* (MariaDB-only driver unchanged, no 8.4 warning, clean takeover of a Flyway-10 history). T-155 spans three repos; per adapter §2 it is split into single-repo tasks:

| Pin | Task |
|---|---|
| meta `docker-compose.dev.yml:33` | [T-155](T-155-flyway-version-supports-mysql-84.md) (kept for the meta half) |
| **`cv-database` `Jenkinsfile:27`, `scripts/migrate.sh:9`** | **this task** |
| `cv-infra` `templates/domain-service-user-data.sh:181` (production) | rides [T-014](T-014-deploy-bff-to-aws.md)'s apply |

**Order is the point:** dev pin → **this task (the CI gate)** → production. And **no new migration in `sql/migrations/` until all four pins agree** — Flyway 10 reading a history 13 has written to is the one direction T-155 could not test.

## Scope

- `Jenkinsfile:27` and `scripts/migrate.sh:9`: `flyway/flyway:10` → `flyway/flyway:13.7.0` (exact tag, not `:13` — `:10` is a floating tag, the class T-152's review flagged).
- Nothing else in the Jenkinsfile — T-153 owns its other changes.

## Acceptance criteria

- [x] `git grep -n "flyway/flyway"` in `cv-database` shows only `13.7.0`.
- [x] Jenkins goes green on the branch, and the console shows `Flyway OSS Edition 13.7.0` and **no** *"upgrade recommended"* warning against MySQL 8.4 — read the log, don't infer it from the green.
- [x] `scripts/migrate.sh` run once against a throwaway MySQL 8.4 with the dev-seeds callback: V1 applied, seeds present.
- [x] `allowPublicKeyRetrieval=true` still present in every URL (`flyway.conf`, `Jenkinsfile`) — the driver did not change, so neither does the gotcha.

## Watch-outs

- The first cold-start build pulls a new image — slower than usual; T-153's timeout bound must allow for it.
- Read Jenkins results through the statuses API, not `gh pr checks`.
- Needs the CI host started — run it in the same CI-host session as T-153 and T-111.

## dev-loop notes

- **Developer:** `backend-developer` (adapter §2, cv-database). **Reviewers:** `/code-review` + `infrastructure-engineer` + `/security-review` (the `Jenkinsfile` path).
