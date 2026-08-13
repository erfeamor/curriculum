# Board

Protocol: [README.md](README.md) · Contract: [docs/api-contract.md](../../docs/api-contract.md)

## M2 — Complete the domain model end-to-end

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-101](T-101-experience-resource.md) | Experience resource in the domain API | cv-domain-service | done | backend-developer | — | [#3](https://github.com/erfeamor/cv-domain-service/pull/3) |
| [T-102](T-102-education-resource.md) | Education resource in the domain API | cv-domain-service | todo (H1 done) | | — | |
| [T-103](T-103-skills-catalog-and-assignments.md) | Skill catalog + person-skill assignments | cv-domain-service | todo (H1 done) | | — | |
| [T-104](T-104-project-resource.md) | Project resource in the domain API | cv-domain-service | todo (H1 done) | | — | |
| [T-105](T-105-experience-ordering-retrofit.md) | Retrofit contract ordering onto the merged Experience resource | cv-domain-service | todo | | T-006 | |
| [T-151](T-151-dev-seeds-cv-sections.md) | Dev seed data for CV sections | cv-database | todo | | — | |
| [T-201](T-201-bff-cv-aggregate.md) | BFF: aggregated public CV endpoint | cv-bff-node | todo | | T-101…T-104, T-006 | |
| [T-301](T-301-admin-cv-sections-crud.md) | Admin UI: CRUD for the four sections | cv-admin-react | todo | | T-101…T-104 | |
| [T-401](T-401-public-cv-sections.md) | Public site: render full CV | cv-public-vanilla | todo | | T-201 | |
| [T-402](T-402-public-react-cv-sections.md) | Public site (React): render full CV sections | cv-public-react | todo | | T-201 | |
| [T-501](T-501-e2e-cv-milestone.md) | End-to-end verification + roadmap close-out | cv-project | todo | | all above | |

### Parallelization notes (read before claiming)

- **Wave 1 (5 agents in parallel):** T-101, T-102, T-103, T-104, T-151 — fully independent; the four API tasks touch disjoint packages, so PRs won't conflict except trivially.
  - **Status as of 2026-08-09:** T-101 is **merged** (PR #3, `09282ed` — CI green, stage-4 QA passed). T-102/T-103/T-104 reached **H1 and stopped** — refinement and their DoR/test plans are complete and ratified, but no code was written; their claims were reset from a stale `in_progress` so they can be picked up. **Start them at implementation, not refinement.** T-151 never started.
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
| [T-001](T-001-selfhost-mysql-followups.md) | Backup: replace the managed backups lost when MySQL left RDS | cv-infra | done (applied + restore verified) | infrastructure-engineer | — | [#15](https://github.com/erfeamor/cv-infra/pull/15) |
| [T-016](T-016-dev-prod-mysql-parity.md) | Dev/prod parity: bump the local MySQL to 8.4 | cv-project (meta) | todo | | — | |
| [T-017](T-017-docs-drift-rds-to-selfhosted.md) | Docs drift: the repo still says RDS in five places | cv-project (meta) + cv-database | todo | | — | |
| [T-018](T-018-mysql-on-dedicated-ebs-volume.md) | MySQL on a dedicated EBS volume, surviving instance replacement | cv-infra | todo | | — | |
| [T-002](T-002-jenkins-on-drone-host.md) | Host Jenkins on the existing Drone CI instance | cv-infra | done | infrastructure-engineer | — | [#11](https://github.com/erfeamor/cv-infra/pull/11) |
| [T-003](T-003-ci-docs-reflect-jenkins.md) | Correct the CI documentation to match reality | cv-project (meta) | todo | | T-002 | |
| [T-004](T-004-terraform-state-hardening.md) | Harden Terraform state: permissions now, remote backend properly | cv-infra | todo | | — | |
| [T-005](T-005-ci-secret-blast-radius.md) | Limit CI secret blast radius: block IMDS from containers | cv-infra | todo | | T-002 | |
| [T-006](T-006-contract-section-ordering.md) | Contract: define ordering for the CV section collections | cv-project (meta) | done | tech-product-owner | — | [#23](https://github.com/erfeamor/curriculum/pull/23) |
| [T-007](T-007-ecs-agent-cleanup.md) | Remove the crash-looping ecs-agent from the CI host | cv-infra | todo | | T-002 | |
| [T-008](T-008-drone-host-backup-and-snapshot.md) | Retire the T-002 gate snapshot, give the CI host a real backup | cv-infra | todo | | T-002 | |
| [T-009](T-009-user-data-size-ceiling.md) | Get the provisioning script out of user_data before it hits the 16 KB wall | cv-infra | todo | | T-002 | |
| [T-010](T-010-aws-credit-runway.md) | Track the AWS credit runway and free-plan cliff before it stops the demo | cv-project (meta) | done | tech-product-owner | — | |
| [T-011](T-011-budget-credit-alarm.md) | Budget alarm that fires on credit burn, not on the invoice | cv-infra | done | infrastructure-engineer | — | [#13](https://github.com/erfeamor/cv-infra/pull/13) |
| [T-012](T-012-aws-endgame-decision.md) | **Decide Paid-vs-teardown before the Free-plan window closes** | cv-project (meta) | todo | | — | **due 2026-12-20** |

> T-013, T-014 and T-015 are part of the deployment chain below and are boarded there, not here, so there is one line per task to claim.

**Board-line correction 2026-08-13.** T-002's line above read `in_review` while its own task file had said `done` since PR [#11](https://github.com/erfeamor/cv-infra/pull/11) merged on 2026-08-09 — rule 1 requires both to be updated and only the file was. The line is now `done`. The practical cost was not cosmetic: **T-003, T-005, T-007, T-008 and T-009 all gate on T-002**, so five infra tasks read as un-claimable for four days. They are claimable now, and none is owned. T-001 is also unowned and is the only thing that has to happen before the deployment chain reaches its destructive step.

> **T-001 applied and verified 2026-08-13 — backups are now real.** The nightly timer is enabled on `i-038600c71d141035b` (next run 03:04 UTC), a forced run landed `cv-20260813T152654Z.sql.gz` in `s3://cv-project-mysql-backup-dev/mysql-dumps/`, and that dump was **restored into a throwaway MySQL 8.4 container** — all six tables plus the Flyway history. The restore, not the upload, is what makes this claim worth anything.
>
> The instance was replaced as expected, so the previous test data is gone and the verified dump is schema-only. The mechanism is proven; it has simply had no authored content to capture yet. **[T-018](T-018-mysql-on-dedicated-ebs-volume.md) is still the thing that matters before real content exists** — a nightly dump does not save data written between dumps, and T-014's apply will replace this box again.

## Public-path deployment gap (cross-repo — blocks T-501)

**`cv-bff-node` has never been deployed to AWS, and neither has `cv-public-vanilla`.** Verified against the live account 2026-08-11/12: no BFF ECR repo, no BFF container in `user_data`, CloudFront `/api/*` goes straight to Java on :8080, and `s3://cv-project-frontend-dev/` holds only `admin/`. The only BFF-named object in the account is an empty log group. The whole **public** path is absent; the admin is live and unaffected because it bypasses the BFF by design (`docs/architecture.md:28`) — which is exactly why the gap stayed invisible.

It stayed unfiled because the IaC asserts the opposite: `cv-infra/compute.tf:1` and `cv-infra/README.md:14` both claim the box already runs the BFF. Same failure class as T-010 — a documented assumption never re-checked against the account.

Deploying it is **not** just adding a container. Two blockers are contract-level, which is why T-013 leads: the BFF serves `GET /api/v1/people/:id` on the **same path** CloudFront already routes to Java (`src/app.ts:26`), and it gates *all* of `/api/v1` behind `requireAuth()` when `AUTH_ENABLED=true` (`src/app.ts:22-25`), which would 401 every anonymous visitor.

One task per repo, strictly sequential — each task's `depends_on` enforces the order, so exactly one is claimable at a time. **This is the board line for all six; claim here.**

| # | ID | Title | Repo | Status | Owner | Depends on | PR |
|---|----|-------|------|--------|-------|------------|----|
| 1 | [T-013](T-013-contract-bff-public-routing.md) | Contract: BFF public edge path + anonymous reads | cv-project (meta) | done | tech-product-owner | — | [#22](https://github.com/erfeamor/curriculum/pull/22) |
| 2 | [T-202](T-202-bff-public-routing-and-auth.md) | BFF: public edge path + anonymous read routes | cv-bff-node | done | fullstack-developer | T-013 | [#4](https://github.com/erfeamor/cv-bff-node/pull/4) |
| 3 | [T-014](T-014-deploy-bff-to-aws.md) | **Deploy cv-bff-node to AWS — registry, container, edge route** | cv-infra | todo | | T-013, T-202 | |
| 4 | [T-403](T-403-public-vanilla-deploy.md) | Public site (vanilla): deploy + point at the deployed BFF | cv-public-vanilla | todo | | T-014 | |
| 5 | [T-015](T-015-docs-reflect-deployed-bff.md) | Correct the meta docs that claim the BFF is deployed | cv-project (meta) | todo | | T-014, T-403 | |
| — | [T-203](T-203-bff-ci-deploy-stage.md) | BFF CI: push to ECR and roll the container on master | cv-bff-node | todo | | T-014 | |
| — | [T-204](T-204-bff-validate-person-id-param.md) | BFF: validate the person id before the upstream call | cv-bff-node | todo | | T-202 | |

**T-013 and T-202 both merged 2026-08-13** ([#22](https://github.com/erfeamor/curriculum/pull/22), [cv-bff-node#4](https://github.com/erfeamor/cv-bff-node/pull/4)). The contract settles the edge path (`/bff/*`, prefix carried to the origin), the two-route anonymous allowlist, and `/metrics`; the BFF now implements them and `/api/v1` is gone from that repo.

**T-014 is next in the chain but is NOT claimable yet** — it also gates on **T-001 §1** (the `mysqldump`→S3 backup), which is still `todo` and unowned. That is deliberate: T-014's apply replaces the instance and destroys the self-hosted MySQL volume. Do T-001 §1 first, or take a hand dump and record it in T-014's checkpoint.

Two things T-014 inherited from this chain's reviews, both of which fail quietly:
- `spa_router` rewrites extensionless URIs to `/index.html`, so `/metrics` and `/health` answer **200 with the SPA shell**, not 404. T-014 carries an acceptance criterion to exclude them, and to verify by request rather than by reading the Terraform.
- The BFF now serves `/bff/api/v1`, so CloudFront must forward the prefix **unstripped**. A behavior that strips it produces a deploy that 404s with nothing obviously wrong in the config.

**[T-204](T-204-bff-validate-person-id-param.md) was filed from T-202's security review.** Pre-existing defect, but T-202 moved the route from JWT-gated to anonymous — so it goes public the moment T-014 deploys. It does not block T-014; it should not sit unfixed for long after it.

> **T-202 merged without stage-4 QA.** Its auth matrix is proven by unit tests against `createApp()`, not against a live stack — no request has traversed a real CloudFront → BFF → domain-service path. T-014's own stage-4 verification is the first time that happens, so treat its live checks as covering both tasks.

Personas and risk (assigned per the adapter's capability→repo map; each task file carries the reviewer set and gate commands):

| ID | Developer | Risk | `security_review` |
|---|---|---|---|
| T-013 | tech-product-owner | normal | false — no code changes; it fires on the consumers |
| T-202 | fullstack-developer | normal | **true** — auth wiring + CORS (adapter §5) |
| T-014 | infrastructure-engineer | **high** | **true** — SG ingress, published ports, CORS |
| T-403 | fullstack-developer | normal | **true** — `.github/workflows/**` + AWS deploy creds |
| T-015 | tech-product-owner | trivial | false — docs only |
| T-203 | infrastructure-engineer | normal | **true** — CI config + AWS creds; read T-005 first |

- **T-203 is off the critical path.** T-501 needs the BFF *deployed*, not *auto-deployed*; T-014's manual deploy is a legitimate stopping point.
- **T-014 is the expensive one** (adapter §7: real apply + stage-4 AWS verification = budget for the full ceiling, never run it in a wave). It replaces the instance via `user_data_replace_on_change`, which **destroys the self-hosted MySQL volume**.
- **Correction, same day (2026-08-13):** T-001 was added to T-014's `depends_on` that morning as the mitigation, then removed again. The dependency rested on an assumption never checked — that the volume held something worth keeping. The human confirmed it holds **test data only**, so the loss is *accepted*, not mitigated, and T-014 no longer waits on T-001. Recorded rather than quietly reverted, because the reasoning was the error, not the typing.
- **That is a dated fact.** Once the demo holds authored CV content, this apply destroys it and no nightly-dump task changes that. The durable fix is **[T-018](T-018-mysql-on-dedicated-ebs-volume.md)** (MySQL on an independent EBS volume), filed from T-001's refinement. **Re-check the database contents before applying T-014.**
- **T-403 was not part of the original ask.** It surfaced while verifying the BFF gap; without it T-014 delivers a BFF that nothing in AWS consumes.
- **Deadline context:** anything meant to be demonstrated live must exist before the T-012 dates (credits ~2026-12-20, Free-plan window 2027-01-12). If T-012 resolves to teardown-and-rebuild, this chain must be **in Terraform before teardown** or the rebuild will not reproduce it.
