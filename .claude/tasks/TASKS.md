# Board

Protocol: [README.md](README.md) · Contract: [docs/api-contract.md](../../docs/api-contract.md)

## M2 — Complete the domain model end-to-end

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-101](T-101-experience-resource.md) | Experience resource in the domain API | cv-domain-service | in_review | backend-developer | — | [#3](https://github.com/erfeamor/cv-domain-service/pull/3) |
| [T-102](T-102-education-resource.md) | Education resource in the domain API | cv-domain-service | in_progress | backend-developer | — | |
| [T-103](T-103-skills-catalog-and-assignments.md) | Skill catalog + person-skill assignments | cv-domain-service | in_progress | backend-developer | — | |
| [T-104](T-104-project-resource.md) | Project resource in the domain API | cv-domain-service | in_progress | backend-developer | — | |
| [T-151](T-151-dev-seeds-cv-sections.md) | Dev seed data for CV sections | cv-database | todo | | — | |
| [T-201](T-201-bff-cv-aggregate.md) | BFF: aggregated public CV endpoint | cv-bff-node | todo | | T-101…T-104, T-006 | |
| [T-301](T-301-admin-cv-sections-crud.md) | Admin UI: CRUD for the four sections | cv-admin-react | todo | | T-101…T-104 | |
| [T-401](T-401-public-cv-sections.md) | Public site: render full CV | cv-public-vanilla | todo | | T-201 | |
| [T-402](T-402-public-react-cv-sections.md) | Public site (React): render full CV sections | cv-public-react | todo | | T-201 | |
| [T-501](T-501-e2e-cv-milestone.md) | End-to-end verification + roadmap close-out | cv-project | todo | | all above | |

### Parallelization notes (read before claiming)

- **Wave 1 (5 agents in parallel):** T-101, T-102, T-103, T-104, T-151 — fully independent; the four API tasks touch disjoint packages, so PRs won't conflict except trivially.
- **Wave 2:** T-201 and T-301 — both may *start* against the contract (mocked upstreams) during wave 1; their final verification needs wave 1 merged.
- **Wave 3:** T-401 and T-402 after T-201 (different repos — run them in parallel); T-501 strictly last.
- T-103 is the highest-risk API task (composite key, upsert, 409) — assign it to the strongest agent or start it first.

### Recent structural changes (context — no M2 work started yet)

The four-section milestone is untouched (every task above is genuinely `todo`), but some repos changed since the board was written — read before claiming:

- **cv-bff-node is now TypeScript** (strict, ts-jest/tsc). T-201's route and tests are `.ts`, type the aggregate payload, and `npm run typecheck` is a gate.
- **cv-admin-react is hexagonal TypeScript** (`domain ← application ← composition → infrastructure`). T-301 follows the repo CLAUDE.md's "adding a section resource" recipe (entity/port → adapter → store factory → composition root → form/pages) — there is no flat `src/api/client.js`.
- **cv-public-react** exists as a second public site (Next.js/ISR from the BFF), currently person-only. Rendering its CV sections is now tracked as **T-402** (the React counterpart of T-401); its domain types already cover all four sections, so the work is presentation + use-case only.
- **The database is self-hosted MySQL 8.4**, not RDS. cv-infra moved MySQL onto a container on the domain-service EC2 (PR #8) to shed the RDS cost and the MySQL 8.0 Extended Support charge. Impact on M2: the target engine is **MySQL 8.4** (migrations verified compatible), and **production applies migrations only** — dev-seeds (T-151) stay dev-only. Backups, dev/prod version parity, and doc cleanup are tracked as **T-001** (below), outside M2.

## Infra & ops (outside M2)

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-001](T-001-selfhost-mysql-followups.md) | Self-hosted MySQL follow-ups: backup, dev parity, docs | cv-infra + meta | todo | | — | |
| [T-002](T-002-jenkins-on-drone-host.md) | Host Jenkins on the existing Drone CI instance | cv-infra | in_review | infrastructure-engineer | — | [#11](https://github.com/erfeamor/cv-infra/pull/11) |
| [T-003](T-003-ci-docs-reflect-jenkins.md) | Correct the CI documentation to match reality | cv-project (meta) | todo | | T-002 | |
| [T-004](T-004-terraform-state-hardening.md) | Harden Terraform state: permissions now, remote backend properly | cv-infra | todo | | — | |
| [T-005](T-005-ci-secret-blast-radius.md) | Limit CI secret blast radius: block IMDS from containers | cv-infra | todo | | T-002 | |
| [T-006](T-006-contract-section-ordering.md) | Contract: define ordering for the CV section collections | cv-project (meta) | todo | | — | |
