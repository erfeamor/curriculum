---
id: T-017
title: "Docs drift: the repo still says RDS in five places"
repo: cv-project (meta) + cv-database
status: todo
owner:
branch: docs/rds-to-selfhosted
pr:
depends_on: []
risk: trivial
security_review: false
---

## Why this exists

Split out of T-001 on 2026-08-13 (§3 of its original scope). MySQL moved off RDS onto a self-hosted 8.4 container (cv-infra PR #8), but the documentation still describes the old topology. Same failure class as T-010 and the T-013 deployment gap: **a documented assumption nobody re-checked against reality**, which is how the BFF gap stayed invisible for months.

## Scope

- Root `README.md` / `README.es.md` — the architecture layer and the roadmap infra line still say "RDS MySQL".
- `docs/architecture.md` — drop RDS from the topology.
- `diagrams/architecture.mmd` — same, in the renderable diagram.
- `cv-database` CLAUDE.md / README — state the target engine is MySQL 8.4.
  - **Sequence against [T-152](T-152-mysql-84-parity-cv-database.md), do not run concurrently** (added 2026-08-22). Both land in `cv-database`: T-152 changes the pins (`docker-compose.yml`, `Jenkinsfile`) and touches `CLAUDE.md:8` for the volume gotcha; this task changes the prose at `CLAUDE.md:3` and `README.md:9`. Adjacent lines in one file, two branches — cheap to avoid, annoying to merge.
  - **Re-scope check before claiming** (added 2026-08-22): the rest of this task is largely already satisfied. All five surviving RDS mentions in the meta repo are contrastive or historical (*"instead of RDS"*, *"replacing RDS's automated backups"*, *"no RDS"*) — which AC1 below explicitly permits — and `diagrams/architecture.mmd:15` reads `MySQL`, never RDS. Verify before doing the work; what is genuinely left may be just the two `cv-database` prose lines.

## Acceptance criteria

- [ ] `grep -ri "rds" ` across the meta repo and cv-database returns nothing that describes current architecture. Historical notes (changelogs, the T-001 rationale, cost-model history explaining *why* RDS was dropped) may keep the word — this is not a blind find-and-replace.
- [ ] The architecture diagram and prose agree with each other and with `cv-infra`.
- [ ] MySQL **8.4** is named as the target engine in cv-database's docs.

## Definition of done

PR open against `master` from `docs/rds-to-selfhosted`, task updated.

## dev-loop notes

- **Developer:** `tech-product-owner` (docs only, spans two repos — meta and cv-database, so it is two PRs if the split is cleaner).
- `risk: trivial` and it genuinely is: prose only, no decisions. The `trivial` fast-path applies to the gates. Unlike T-006 and T-013, this task decides nothing — it records a decision already made and applied.
