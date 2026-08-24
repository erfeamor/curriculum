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

## Recommended outcome: STAY ON FLYWAY 10 and record why (2026-08-24, on the human's instruction)

**This task's own AC1 already legitimizes it** — *"leave Flyway at 10 and document why is a legitimate outcome and must be written down if chosen"*. The recommendation is to take that branch, and the reasoning is a cost/blast-radius argument, not a shrug:

1. **The warning says untested, not broken.** The entire migration set is **one file of plain DDL**, and Flyway 10 has been observed applying it correctly against real 8.4 four separate times: T-152 stage 1, the driver's local pipeline reproduction, T-152's stage-4 QA, and now Jenkins PR-4 build #2.
2. **It is a two-major jump, not a tag bump.** The console pins the current version at **10.22.0** against **13.3.0** advertised as latest. §2's question — does a newer Flyway still bundle the MariaDB driver? — is the sharp edge: if it ships the MySQL driver instead, the `allowPublicKeyRetrieval` gotcha changes and **every JDBC URL in the workspace needs re-checking**, along with the three `CLAUDE.md` files that document it. That is a workspace-wide blast radius bought to silence a warning on a green build.
3. **The `cv-infra` half costs a production instance replacement**, with [T-021](T-021-mysql-password-rotation-persistent-datadir.md)'s `db_password` precondition to respect on the way.
4. **The demo is time-boxed.** [T-012](T-012-aws-endgame-decision.md) puts the Free-plan window at **2027-01-12**. Spending a three-repo change with a production apply on an untested-but-working pairing is poor value against that horizon.

**The honest counter-argument, recorded so it is not lost:** the unsupported pairing is now load-bearing in the **gate** as well as production, and a future migration using anything 8.0/8.4-divergent gets its first real test the day it is written. That is a real risk and it is why this is *"stay on 10 **and record why**"*, not *"close as won't-fix"*.

**Therefore, if this outcome is taken, the decision must carry a revisit condition, not just a rationale:** revisit the moment a migration beyond plain DDL is added to `sql/migrations/`, or if [T-012](T-012-aws-endgame-decision.md) chooses to extend the demo's life. Write both into the closing note. A decision with no trigger to re-examine it is how this board's stale premises are made.

**This is a recommendation for H1, not a decision taken here.** The cross-repo decomposition below still applies if H1 chooses to bump.

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


## Confirmed in CI, not only locally — 2026-08-22

The warning this task is about is now observed in a real Jenkins run (`cv-database` PR-4 build #2 console, supplied by the human):

```
Flyway OSS Edition 10.22.0 by Redgate
...
Database: jdbc:mysql://cv-mysql-ci-2:3306/cv?allowPublicKeyRetrieval=true (MySQL 8.4)
WARNING: Flyway upgrade recommended: MySQL 8.4 is newer than this version of Flyway
and support has not been tested. The latest supported version of MySQL is 8.1.
Successfully applied 1 migration to schema `cv`, now at version v1
```

Two things this pins down that the task previously argued from local runs:

1. **The exact version in play is Flyway OSS 10.22.0**, not "flyway 10" generically. Whoever prices the bump at H1 now has the concrete starting point, and the log also shows Flyway itself advertising **13.3.0** as current — a two-major jump, which is a materially different proposition from a patch bump and should be weighed at H1 rather than assumed cheap.
2. **The unsupported pairing is load-bearing in CI as well as in production.** The migration applies cleanly against 8.4 — one more data point for *"it says untested, not broken"* — but it now does so in the gate that is supposed to be the safety net, which is the argument for deciding this rather than leaving it to accumulate.
