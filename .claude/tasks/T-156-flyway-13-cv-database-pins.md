---
id: T-156
title: "Flyway 10 → 13.7.0 in cv-database — the Jenkins migration gate and scripts/migrate.sh (split from T-155)"
repo: cv-database
status: todo
owner:
branch: chore/flyway-13
pr:
depends_on: [T-155, T-153]   # T-155: the dev pin moves first, so 13 is proven on the dev stack before the gate; T-153: FILE-LEVEL, both edit cv-database/Jenkinsfile (the T-153 → T-152 precedent) — or ride T-153's PR if H1 prefers one Jenkinsfile diff
risk: normal
security_review: true   # adapter §5 — `Jenkinsfile` is an unconditional /security-review path
---

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

- [ ] `git grep -n "flyway/flyway"` in `cv-database` shows only `13.7.0`.
- [ ] Jenkins goes green on the branch, and the console shows `Flyway OSS Edition 13.7.0` and **no** *"upgrade recommended"* warning against MySQL 8.4 — read the log, don't infer it from the green.
- [ ] `scripts/migrate.sh` run once against a throwaway MySQL 8.4 with the dev-seeds callback: V1 applied, seeds present.
- [ ] `allowPublicKeyRetrieval=true` still present in every URL (`flyway.conf`, `Jenkinsfile`) — the driver did not change, so neither does the gotcha.

## Watch-outs

- The first cold-start build pulls a new image — slower than usual; T-153's timeout bound must allow for it.
- Read Jenkins results through the statuses API, not `gh pr checks`.
- Needs the CI host started — run it in the same CI-host session as T-153 and T-111.

## dev-loop notes

- **Developer:** `backend-developer` (adapter §2, cv-database). **Reviewers:** `/code-review` + `infrastructure-engineer` + `/security-review` (the `Jenkinsfile` path).
