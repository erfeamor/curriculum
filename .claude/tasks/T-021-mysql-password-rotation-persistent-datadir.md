---
id: T-021
title: "Rotating db_password silently breaks the stack now that the MySQL datadir persists"
repo: cv-infra
status: todo
owner:
branch: fix/mysql-password-rotation
pr:
depends_on: [T-018]
risk: normal
security_review: true
---

## Why this exists

Filed from **T-018's review round 1** (finding 5, 2026-08-14). Not a defect in T-018 — a **behaviour change T-018 necessarily introduces**, deliberately documented rather than fixed there, because the obvious fix is a credential-rewriting branch in a boot script and that deserves its own review.

### The mechanism

The `mysql:8.4` entrypoint applies `MYSQL_ROOT_PASSWORD` / `MYSQL_PASSWORD` **only when it initializes an empty datadir**. Before T-018, every instance replacement wiped `/var/lib/cv-mysql`, so MySQL re-initialized on each boot and silently picked up whatever `db_password` was current in SSM. Rotation "just worked" — by accident, as a side effect of the data loss T-018 exists to stop.

Now the datadir survives. Initialization is skipped, the database keeps the **old** credentials, and the bootstrap reads the **new** one from SSM (`templates/domain-service-user-data.sh`, `param cv/db/password`). They disagree, and nothing says so.

### What that looks like when it happens

Not a clean failure at the point of change — the box comes up and then falls over downstream:

1. Flyway's container fails to authenticate.
2. `set -euo pipefail` aborts the bootstrap at that line.
3. **The domain-service container is never started** — the API is simply absent.
4. `mysql-backup.sh` fails the same way, so the nightly dump stops landing in S3 (T-001's mechanism, still reporting success at the timer level).

The trigger is a `terraform apply` after someone edits `var.db_password` — an action that looks routine and has no warning attached to it.

## Scope

Pick one and implement it; they are not equivalent and the choice is the interesting part of this task:

- **A · Reconcile on boot.** Detect the reattach case and `ALTER USER` both accounts to the SSM value before Flyway runs. Makes rotation work, but puts credential rewriting into a boot script that runs unattended — needs care that a partial failure cannot leave the database with neither password valid.
- **B · Fail loudly, early.** Probe credentials immediately after the mount and abort with an explicit message naming the cause, before Flyway's opaque auth error. Cheap, safe, honest — rotation still requires a manual step, but it stops being a mystery.
- **C · Take rotation out of `terraform apply`.** Document a runbook (`ALTER USER` against the live container, then update SSM) and make `var.db_password` changes a deliberate, documented operation rather than an incidental one.

**B is the recommended default** — it converts a silent multi-step failure into a one-line diagnosis for a fraction of A's risk. A is worth doing only if rotation is expected to be routine, which for this demo it is not.

## Acceptance criteria

- [ ] Rotating `var.db_password` and applying produces either a working stack (A) or an immediate, explicit failure naming the cause (B/C) — **proven by actually rotating it against the live stack**, not by reading the script.
- [ ] Flyway and the domain-service container are not left in the "aborted bootstrap, no API" state described above.
- [ ] The nightly backup path is checked under the same condition — a rotation must not silently stop the dumps.
- [ ] `terraform fmt -check -recursive`, `terraform validate`, `terraform test` pass.
- [ ] Whichever option is chosen, `cv-infra/CLAUDE.md` documents how rotation is supposed to be performed.

## Definition of done

PR open against `master` from `fix/mysql-password-rotation`, gates green, verified by a real rotation, merged.

## dev-loop notes

- **Developer:** `infrastructure-engineer`. **`security_review: true`** — this task handles database credentials directly, and option A writes them at boot.
- **Depends on T-018** because the failure mode does not exist until the datadir persists.
- **Do not bundle this into T-018.** It was deliberately scoped out at review-round-1 adjudication: a credential-rewriting branch in an unattended boot script is a different risk profile from a storage-layout change, and mixing them makes both harder to review and to roll back.
- The same class of trap may exist for other first-init-only MySQL settings now that the datadir survives — worth a look while in here, but anything found goes in its own task, not this one.
