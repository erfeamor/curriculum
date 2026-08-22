---
id: T-155
title: "Flyway 10 does not claim MySQL 8.4 support — and it runs against 8.4 in production"
repo: cv-database + cv-project (meta) + cv-infra
status: todo
owner:
branch: chore/flyway-supports-mysql-84
pr:
depends_on: []
risk: normal
security_review: true   # touches `Jenkinsfile` (adapter §5, unconditional) and Terraform user_data; A1 re-checks against the real diff
---

## Goal

Every Flyway run in this workspace now emits:

```
WARNING: Flyway upgrade recommended: MySQL 8.4 is newer than this version of Flyway
and support has not been tested. The latest supported version of MySQL is 8.1.
```

Migrations apply and builds stay green. This task decides whether to move to a Flyway version that claims 8.4, and does it if so.

## The important framing — do not read this as a regression from T-152

[T-152](T-152-mysql-84-parity-cv-database.md) made this **visible**; it did not create it. `cv-infra/templates/domain-service-user-data.sh:181` has been running `flyway/flyway:10` against production's `mysql:8.4` on **every instance replacement** since MySQL left RDS. The unsupported pairing was already load-bearing for real deploys and tested nowhere.

Before T-152, CI validated migrations against **8.0** while production applied them on **8.4** — a green gate that said nothing about the engine actually receiving them. T-152 is the fix for that gap. This task is the next step, not a rollback of it.

## Scope — cross-repo, decompose at refinement

`flyway/flyway:10` is pinned in **at least four places across three repos**. Per adapter §2's cross-repo rule and board rule 3, stage 0 must split this into dependency-ordered single-repo tasks before H1:

| Repo | Where |
|---|---|
| `cv-database` | `Jenkinsfile:27` (the CI gate) and `scripts/migrate.sh` |
| `cv-project` (meta) | `docker-compose.dev.yml` — the `flyway` service the dev stack and every QA env use |
| `cv-infra` | `templates/domain-service-user-data.sh:181` — **production**; changing it means a `terraform apply` and an instance replacement |

**The cv-infra half is the expensive one** and carries real risk: an apply replaces the instance. Since [T-018](T-018-mysql-on-dedicated-ebs-volume.md) the datadir survives on its own volume, so this is no longer destructive to data — but confirm `/var/lib/cv-mysql` is mounted from the dedicated volume (`findmnt`) before applying, and read [T-021](T-021-mysql-password-rotation-persistent-datadir.md) first: the persistent datadir means a `db_password` change would abort the bootstrap.

## Decide at H1, do not assume the bump is right

1. **Is the warning worth acting on at all?** It says *untested*, not *broken*. The migration set is one file of plain DDL; Flyway 10 applies it correctly against 8.4, verified repeatedly (T-152 stage 1, driver reproduction, and stage-4 QA).
2. **What does a newer Flyway cost?** Check whether it still bundles the MariaDB driver — the `allowPublicKeyRetrieval` gotcha documented in three CLAUDE.md files is a consequence of that bundling. If a newer version ships the MySQL driver instead, the gotcha changes and **every URL in the workspace needs re-checking**, which is a much larger blast radius than a tag bump.
3. **Does it need to be all three repos at once?** Production and CI disagreeing on Flyway version would reintroduce exactly the parity gap T-152 closed, one layer up. If the answer is "yes, together", say so and sequence it.

## Acceptance criteria

- [ ] A decision recorded either way, with reasoning — "leave Flyway at 10 and document why" is a legitimate outcome and must be written down if chosen, not left implicit.
- [ ] If bumping: no pin left at the old version anywhere (`grep -rn "flyway/flyway"` across all three repos), and the `allowPublicKeyRetrieval` question in §2 answered empirically, not from release notes.
- [ ] If bumping: migrations verified applying on the new version against **real MySQL 8.4**, with the version read from the running container.
- [ ] Production and CI end on the **same** Flyway version, or the divergence is deliberate and recorded.

## Provenance

Found during [T-152](T-152-mysql-84-parity-cv-database.md)'s implementation, 2026-08-22, and confirmed not-blocking by that task's stage-2 review — which argued explicitly that blocking T-152 over this would have protected the more dangerous status quo. Filed at T-152's H2 gate.
