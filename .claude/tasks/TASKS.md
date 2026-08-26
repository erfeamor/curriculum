# Board

Protocol: [README.md](README.md) · Contract: [docs/api-contract.md](../../docs/api-contract.md)

## M2 — Complete the domain model end-to-end

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-101](T-101-experience-resource.md) | Experience resource in the domain API | cv-domain-service | done | backend-developer | — | [#3](https://github.com/erfeamor/cv-domain-service/pull/3) |
| [T-102](T-102-education-resource.md) | Education resource in the domain API | cv-domain-service | done | backend-developer | — | [#5](https://github.com/erfeamor/cv-domain-service/pull/5) |
| [T-103](T-103-skills-catalog-and-assignments.md) | Skill catalog + person-skill assignments | cv-domain-service | done | backend-developer | — | [#7](https://github.com/erfeamor/cv-domain-service/pull/7) |
| [T-104](T-104-project-resource.md) | Project resource in the domain API | cv-domain-service | done | backend-developer | — | [#8](https://github.com/erfeamor/cv-domain-service/pull/8) |
| [T-105](T-105-experience-ordering-retrofit.md) | Retrofit contract ordering onto the merged Experience resource | cv-domain-service | done | backend-developer | T-006 ✔ | [#9](https://github.com/erfeamor/cv-domain-service/pull/9) |
| [T-106](T-106-restrict-openapi-and-actuator-exposure.md) | Stop serving the OpenAPI spec and Prometheus metrics anonymously | cv-domain-service | done | backend-developer | — | [#4](https://github.com/erfeamor/cv-domain-service/pull/4) |
| [T-107](T-107-post-id-cross-person-write.md) | **POST with a client-supplied id overwrites another person's row** (person, experience) | cv-domain-service | done | backend-developer | — | [#6](https://github.com/erfeamor/cv-domain-service/pull/6) |
| [T-108](T-108-untransacted-update-read-modify-write.md) | **PUT is an untransacted read-modify-write** — a concurrent DELETE makes it re-INSERT the row under a new id (all three section resources) | cv-domain-service | todo | | — | |
| [T-109](T-109-ordering-tiebreak-unevidenced-siblings.md) | The `id ASC` tiebreaker is asserted by tests that **cannot go red** — every ordered collection except experience | cv-domain-service | todo | | T-105 | |
| [T-151](T-151-dev-seeds-cv-sections.md) | Dev seed data for CV sections | cv-database | done | backend-developer | — | [#4](https://github.com/erfeamor/cv-database/pull/4) |
| [T-201](T-201-bff-cv-aggregate.md) | BFF: aggregated public CV endpoint | cv-bff-node | todo | | T-101…T-104, T-006 | |
| [T-301](T-301-admin-cv-sections-crud.md) | Admin UI: CRUD for the four sections | cv-admin-react | todo | | T-101…T-104 | |
| [T-401](T-401-public-cv-sections.md) | Public site: render full CV | cv-public-vanilla | todo | | T-201 | |
| [T-402](T-402-public-react-cv-sections.md) | Public site (React): render full CV sections | cv-public-react | todo | | T-201 | |
| [T-501](T-501-e2e-cv-milestone.md) | End-to-end verification + roadmap close-out | cv-project | todo | | all above **+ T-105, T-014, T-403, T-404** | |

### Parallelization notes (read before claiming)

- **Wave 1 complete:** T-101 (`09282ed`), T-102 (`42abe91`), T-103 (`2e54394`), T-104 (`7677fee`), T-151 (`865784f`) all merged. **Wave 2 unblocked:** T-201 and T-301 may start against the contract (mocked upstreams). **Wave 3:** T-401 and T-402 after T-201 (run in parallel); T-501 strictly last. ~~**T-105** is still `todo` and blocks T-501 — it is the only task making Experience contract-compliant on ordering.~~ **T-105 MERGED 2026-08-26** (`1b9b398`, [#9](https://github.com/erfeamor/cv-domain-service/pull/9)) — all four section collections are now contract-compliant on ordering, and **T-501's last M2-domain blocker is gone**. What still gates T-501 is the deployment chain (T-014 → T-403/T-404) plus T-201/T-301/T-401/T-402. **[T-201](T-201-bff-cv-aggregate.md) is the head of everything remaining**: it is claimable today and T-014 waits on it.
- **Concurrency lesson from T-103:** highest-risk tasks (composite key, upsert, 409) should start first so review convergence failures surface earliest.
- **T-105 was unowned by anything until 2026-08-17.** It is critical to the milestone yet appeared in no `depends_on` — an ordering retrofit needed for T-501's final check.

### Recent structural changes (context — M2 is one task in)

- **cv-bff-node is now TypeScript** (strict, ts-jest/tsc). T-201's route and tests are `.ts`, type the aggregate payload, and `npm run typecheck` is a gate.
- **cv-admin-react is hexagonal TypeScript** (domain ← application ← composition → infrastructure). T-301 follows the repo CLAUDE.md's "adding a section resource" recipe.
- **cv-public-react** exists as a second public site (Next.js/ISR from the BFF). Rendering its CV sections is tracked as **T-402** (the React counterpart of T-401); domain types already cover all four sections.
- **The database is self-hosted MySQL 8.4**, not RDS. Migrations verified compatible; production applies migrations only — dev-seeds stay dev-only. Backups and dev/prod version parity tracked as **T-001**, outside M2.

## Infra & ops (outside M2)

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-001](T-001-selfhost-mysql-followups.md) | Backup: replace the managed backups lost when MySQL left RDS | cv-infra | done | infrastructure-engineer | — | [#15](https://github.com/erfeamor/cv-infra/pull/15) |
| [T-016](T-016-dev-prod-mysql-parity.md) | Dev/prod parity: bump the local MySQL to 8.4 | cv-project (meta) | done | infrastructure-engineer | T-152 ✔ | [#52](https://github.com/erfeamor/curriculum/pull/52) |
| [T-152](T-152-mysql-84-parity-cv-database.md) | Dev/CI parity: bump cv-database's stack **and its migration gate** to MySQL 8.4 | cv-database | done | backend-developer | — | [#3](https://github.com/erfeamor/cv-database/pull/3) |
| [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md) | cv-database's Jenkins `Deploy` stage is gated on `main`, a branch that does not exist here | cv-database | todo | | T-152 | |
| [T-154](T-154-jenkins-pipeline-timeout.md) | No `timeout {}` on cv-database's pipeline: a hung build holds the only CI host up | cv-database | todo | | — | |
| [T-155](T-155-flyway-version-supports-mysql-84.md) | Flyway 10 does not claim MySQL 8.4 support — yet it runs against 8.4 in production | cv-database + meta + cv-infra | todo | | — | |
| [T-017](T-017-docs-drift-rds-to-selfhosted.md) | Docs drift: name MySQL 8.4 as the target engine in cv-database's docs | cv-project (meta) + cv-database | todo | | — | |
| [T-018](T-018-mysql-on-dedicated-ebs-volume.md) | MySQL on a dedicated EBS volume, surviving instance replacement | cv-infra | done | infrastructure-engineer | — | [#16](https://github.com/erfeamor/cv-infra/pull/16) |
| [T-021](T-021-mysql-password-rotation-persistent-datadir.md) | Rotating `db_password` breaks silently now the datadir persists | cv-infra | todo | | T-018 | |
| [T-022](T-022-domain-service-origin-bypasses-cloudfront.md) | Domain service reachable on :8080 bypassing CloudFront; leaks OpenAPI spec | cv-infra | done | infrastructure-engineer | — | [#20](https://github.com/erfeamor/cv-infra/pull/20) |
| [T-019](T-019-ci-host-on-demand.md) | Stop paying for an idle CI host: start on demand, stop when quiet | cv-infra | done | infrastructure-engineer | — | [#17](https://github.com/erfeamor/cv-infra/pull/17) |
| [T-002](T-002-jenkins-on-drone-host.md) | Host Jenkins on the existing Drone CI instance | cv-infra | done | infrastructure-engineer | — | [#11](https://github.com/erfeamor/cv-infra/pull/11) |
| [T-003](T-003-ci-docs-reflect-jenkins.md) | Correct the CI documentation to match reality | cv-project (meta) | todo | | T-002 | |
| [T-004](T-004-terraform-state-hardening.md) | Harden Terraform state: permissions now, remote backend properly | cv-infra | todo (**part 1 done: 0600** — start at part 2) | | — | |
| [T-005](T-005-ci-secret-blast-radius.md) | Limit CI secret blast radius: block IMDS from containers | cv-infra | todo | | T-002 | |
| [T-006](T-006-contract-section-ordering.md) | Contract: define ordering for the CV section collections | cv-project (meta) | done | tech-product-owner | — | [#23](https://github.com/erfeamor/curriculum/pull/23) |
| [T-007](T-007-ecs-agent-cleanup.md) | Remove the crash-looping ecs-agent from the CI host | cv-infra | todo | | T-002 | |
| [T-008](T-008-drone-host-backup-and-snapshot.md) | Retire the T-002 gate snapshot, give the CI host a real backup | cv-infra | todo | | T-002 | |
| [T-009](T-009-user-data-size-ceiling.md) | Get the provisioning script out of user_data before it hits the 16 KB wall | cv-infra | done | infrastructure-engineer | T-002 | [#18](https://github.com/erfeamor/cv-infra/pull/18) |
| [T-010](T-010-aws-credit-runway.md) | Track the AWS credit runway and free-plan cliff before it stops the demo | cv-project (meta) | done | tech-product-owner | — | none |
| [T-011](T-011-budget-credit-alarm.md) | Budget alarm that fires on credit burn, not on the invoice | cv-infra | done | infrastructure-engineer | — | [#13](https://github.com/erfeamor/cv-infra/pull/13) |
| [T-012](T-012-aws-endgame-decision.md) | **Decide Paid-vs-teardown before the Free-plan window closes** | cv-project (meta) | todo | | — | **due 2026-11-01** |
| [T-020](T-020-cost-model-correction.md) | Correct the stale cost model; stop the budget alarm crying wolf | cv-project (meta) + cv-infra | done | tech-product-owner | — | [#36](https://github.com/erfeamor/curriculum/pull/36) + [cv-infra#19](https://github.com/erfeamor/cv-infra/pull/19) |
| [T-023](T-023-meta-docs-stale-bff-smoke-path.md) | The documented E2E smoke command curls a path the BFF no longer serves | cv-project (meta) | todo | | — | |
| [T-024](T-024-contract-skill-assignment-put-shape.md) | Contract: split the skill-assignment PUT's request body from its response | cv-project (meta) | done | tech-product-owner | — | [#41](https://github.com/erfeamor/curriculum/pull/41) |
| [T-025](T-025-verify-requests-come-from-our-cloudfront.md) | The edge is not an authenticator: prove requests come from OUR distribution | cv-infra + cv-domain-service | todo | | T-022 | |
| [T-026](T-026-first-build-after-cold-start-fails.md) | First build after a Jenkins restart fails — **ROOT CAUSE FOUND 2026-08-26: JENKINS-23152 build-number collision**; the DSL seed recreates the jobs every boot against a persistent `JENKINS_HOME`. Ready to fix. | cv-infra | todo | | T-019 | |
| [T-027](T-027-contract-ordering-note-sql-vs-jpql.md) | Contract: the ordering note prescribes SQL syntax for a JPQL context | cv-project (meta) | todo | | — | |
| [T-028](T-028-qa-env-generator-worktree-build-context.md) | QA stack builds `master`, not the worktree under test (**silent false pass**) | cv-project (meta) | done | infrastructure-engineer | — | [#49](https://github.com/erfeamor/curriculum/pull/49) |
| [T-029](T-029-code-review-cannot-see-worktrees.md) | `/code-review` **silently reviews the wrong thing** without an explicit target | cv-project (meta) | todo | | — | |
| [T-030](T-030-pr3-build1-success-then-error.md) | A Jenkins build posted `success` then `error` one second later — **DIAGNOSED: a mid-build Jenkins restart, NOT T-026** | cv-infra | done | tech-product-owner | — | none |
| [T-031](T-031-board-frontmatter-validator.md) | **A validator for the task board** — the checks this board keeps running by hand and keeps failing | cv-project (meta) | done | infrastructure-engineer | — | [#59](https://github.com/erfeamor/curriculum/pull/59) |
| [T-032](T-032-board-check-re-review-after-live-use.md) | Re-review `board-check.py` after a week of real use — **the finding rate never fell** — and add the **link-integrity check** (5 dead links passed as clean, 2026-08-24) | cv-project (meta) | todo | | T-031 ✔ | **not before 2026-08-30** |
| [T-033](T-033-ci-host-tls.md) | CI host serves Jenkins login and Drone OAuth over plain HTTP on a scanned public IP — decide TLS or record the accepted risk | cv-infra | todo | | — | |

### The measured model — [T-020](T-020-cost-model-correction.md), read 2026-08-19

**No console needed, and that is itself a finding.** `aws freetier get-account-plan-state` and `list-account-activities` post-date T-010 and return everything its `human_dependency` declared console-only. T-020's §1 was parked on a constraint that had expired.

| | |
|---|---|
| Plan | **FREE**, ACTIVE, expires **2027-01-12T15:38:35Z** |
| Credits remaining | **$111.08** |
| Grant | **$160** — the two $20 activities T-010 ratified on 2026-08-11 are still `NOT_STARTED` |
| Run rate | **$0.6837/day ≈ $20.81/month** |
| Binding constraint | **WINDOW** (2027-01-12); credits now last to ~2027-01-28 |

**Why the rate fell: `cv-project-drone` has been `stopped` since 2026-08-14 08:12 GMT** (`User initiated`), and it was 46% of the bill. Nothing on the board recorded that. Daily Cost Explorer confirms all three eras — $0.92 (Aug 5–7), $1.226 (Aug 9–13), **$0.684 (Aug 15–17)** — so both earlier models were accurate for their moment and both are now wrong.

Four consequences:

1. **The binding constraint flipped back to the window**, reversing the 2026-08-14 re-derivation above. Crossover is **$0.761/day**: below it the window binds, above it the credits do. Restart the CI host 24/7 and it is credits again at ~2026-11-17.
2. **[T-012](T-012-aws-endgame-decision.md) stays at `due: 2026-11-01`** — deliberately *not* relaxed. The low rate rests on a stopped box and an unbuilt automation; one forgotten `start-instances` restores the November cliff, and a loosened deadline would then sit after it.
3. **The budget alarm's premise evaporated.** The `$30` monthly limit is not structurally exceeded at $20.81/month — September projects to **68%**. August still breaches once (~$34.68, 116%) on the strength of its first half. T-020 §4 now recommends **changing nothing**: a $30 limit against a $20.81 rate fires precisely when the CI host is left running, which is the one behaviour worth an alert.
4. **Jenkins and Drone are on the stopped box, and T-102/T-103/T-104 all require "Jenkins CI green".** The M2 backend wave cannot close while it is off — so the cost model and the milestone schedule became the same decision. **[T-019](T-019-ci-host-on-demand.md)'s H1 was ratified 2026-08-19: build the start-on-push automation**, which keeps the rate *and* unblocks M2. Its "runs 24/7" premise is corrected in that file.
> **Earlier cost-model derivations** — the superseded $0.92/day and $1.23/day models, and the close-out notes for T-019 and T-001 — are in [HISTORY.md](HISTORY.md). They were correct for the rates they assumed; quote the table above, not them.

## Public-path deployment gap (cross-repo — blocks T-501)

**`cv-bff-node` has never been deployed to AWS, and neither has `cv-public-vanilla`.** Verified against the live account 2026-08-11/12: no BFF ECR repo, no BFF container in `user_data`, CloudFront `/api/*` goes straight to Java on :8080, and `s3://cv-project-frontend-dev/` holds only `admin/`. The only BFF-named object in the account is an empty log group. The whole **public** path is absent; the admin is live and unaffected because it bypasses the BFF by design (`docs/architecture.md:28`) — which is exactly why the gap stayed invisible.

It stayed unfiled because the IaC asserts the opposite: `cv-infra/compute.tf:1` and `cv-infra/README.md:14` both claim the box already runs the BFF. Same failure class as T-010 — a documented assumption never re-checked against the account.

Deploying it is **not** just adding a container. Two blockers are contract-level, which is why T-013 leads: the BFF serves `GET /api/v1/people/:id` on the **same path** CloudFront already routes to Java (`src/app.ts:26`), and it gates *all* of `/api/v1` behind `requireAuth()` when `AUTH_ENABLED=true` (`src/app.ts:22-25`), which would 401 every anonymous visitor.

One task per repo. The **numbered** rows are strictly sequential and their `depends_on` enforces the order; the unnumbered rows hang off the chain and are claimable independently once their own dependency is met. **This is the board line for all seven; claim here.** (Corrected 2026-08-17: this said "exactly one is claimable at a time", which stopped being true when T-202 merged — T-204 became claimable alongside T-014, and T-404 now joins it.)

| # | ID | Title | Repo | Status | Owner | Depends on | PR |
|---|----|-------|------|--------|-------|------------|----|
| 1 | [T-013](T-013-contract-bff-public-routing.md) | Contract: BFF public edge path + anonymous reads | cv-project (meta) | done | tech-product-owner | — | [#22](https://github.com/erfeamor/curriculum/pull/22) |
| 2 | [T-202](T-202-bff-public-routing-and-auth.md) | BFF: public edge path + anonymous read routes | cv-bff-node | done | fullstack-developer | T-013 | [#4](https://github.com/erfeamor/cv-bff-node/pull/4) |
| 3 | [T-014](T-014-deploy-bff-to-aws.md) | **Deploy cv-bff-node to AWS — registry, container, edge route** | cv-infra | todo (**H1 done** — seven rulings + test plan, start at implementation) | | T-013, T-202, **T-201** | |
| 4 | [T-403](T-403-public-vanilla-deploy.md) | Public site (vanilla): deploy + point at the deployed BFF | cv-public-vanilla | todo | | T-014 | |
| 5 | [T-015](T-015-docs-reflect-deployed-bff.md) | Correct the meta docs that claim the BFF is deployed | cv-project (meta) | todo | | T-014, T-403 | |
| — | [T-203](T-203-bff-ci-deploy-stage.md) | BFF CI: push to ECR and roll the container on master | cv-bff-node | todo | | T-014 | |
| — | [T-204](T-204-bff-validate-person-id-param.md) | BFF: validate the person id before the upstream call | cv-bff-node | todo | | T-202 | |
| — | [T-404](T-404-public-react-point-at-deployed-bff.md) | Public site (React): point Vercel's `BFF_URL` at the deployed BFF | cv-public-react | todo | | T-014 | |

**~~[T-022](T-022-domain-service-origin-bypasses-cloudfront.md) should be done before T-014~~ — DONE 2026-08-20 ([cv-infra#20](https://github.com/erfeamor/cv-infra/pull/20)); the sequencing advice below is satisfied, and what T-014 inherits from it is recorded in T-014 itself (its own security group — the prefix list burns 46 of the 60-rule quota). Kept for the reasoning. It was invisible on this board until 2026-08-17.** Both tasks argue it — T-014's ruling 1 and T-022's dev-loop notes — but neither the chain table nor its prose mentioned T-022, and T-014 is the task everyone is told to claim next. It is **not** a `depends_on` edge in either direction (deliberately: neither blocks the other). The argument is that T-022 applies the *same* managed-prefix-list fix to port 8080 that T-014's ruling 1 mandates for port 3000, so doing it first means T-014 follows an established pattern instead of inventing one, and the reviewer sees one consistent approach across both ports. T-022 is also cheap (in-place SG change, `risk: normal`, easily reverted) and closes a live unauthenticated `/v3/api-docs` disclosure that grows automatically with every M2 resource that lands.

**T-013 and T-202 both merged 2026-08-13** ([#22](https://github.com/erfeamor/curriculum/pull/22), [cv-bff-node#4](https://github.com/erfeamor/cv-bff-node/pull/4)). The contract settles the edge path (`/bff/*`, prefix carried to the origin), the two-route anonymous allowlist, and `/metrics`; the BFF now implements them and `/api/v1` is gone from that repo.

~~**T-014 is next in the chain and IS claimable.** Its `depends_on` is `[T-013, T-202]` and both are `done`.~~ **Stale again — corrected 2026-08-24, and note the irony: the 2026-08-24 session that added `T-201` to T-014's `depends_on` updated the task file and the chain table but not this paragraph, the exact failure this same paragraph's closing sentence warns about.** Current state: T-014's `depends_on` is `[T-013, T-202, T-201]`; the first two are `done`, **T-201 is `todo`, so T-014 is NOT claimable until T-201 merges** — a deliberate sequencing decision (the first deployed image must carry the aggregate; see T-014's frontmatter note). **T-201 is what is claimable now**, and it is the head of the whole chain. This paragraph previously said the opposite — that T-014 "is NOT claimable yet" because it gated on T-001 §1, "which is still `todo` and unowned" — and both halves of that were false by the time it was written: T-001 is `done` (applied and restore-verified 2026-08-13), and T-001 had already been **removed** from T-014's `depends_on` that same day for the reason recorded at the end of this section. **Corrected 2026-08-14.** This is the T-002 board-line bug repeating one day later: prose that gates a task, contradicted by the frontmatter it claims to describe. When a dependency changes, the task file and *every* prose reference to it move together.

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

- ~~**T-203 is off the critical path.** T-501 needs the BFF *deployed*, not *auto-deployed*; T-014's manual deploy is a legitimate stopping point.~~ **True, and it had a consequence nobody had traced — corrected 2026-08-24.** T-203 being off the critical path is exactly *why* [T-201](T-201-bff-cv-aggregate.md)'s arrival had no owner: T-014's ruling 7 planned to deploy an image that 404s the contract's aggregate, and the only task that would rebuild and roll that container is **T-203**, which is downstream of T-014 and absent from T-501's `depends_on`. So T-501 could reach its end-to-end check against a deployed BFF that still 404s `/cv`, with no board line holding the redeploy. **Fixed by sequencing rather than by adding another task: T-201 is now in T-014's `depends_on`**, so the first deployed image already serves the aggregate and T-014's single expensive apply verifies it. T-203 remains off the critical path and remains a legitimate later step — it is now an *optimisation*, not a silent prerequisite.
- **T-014 is the expensive one** (adapter §7: real apply + stage-4 AWS verification = budget for the full ceiling, never run it in a wave). It replaces the instance via `user_data_replace_on_change`, which **destroys the self-hosted MySQL volume**.
- **Correction, same day (2026-08-13):** T-001 was added to T-014's `depends_on` that morning as the mitigation, then removed again. The dependency rested on an assumption never checked — that the volume held something worth keeping. The human confirmed it holds **test data only**, so the loss is *accepted*, not mitigated, and T-014 no longer waits on T-001. Recorded rather than quietly reverted, because the reasoning was the error, not the typing.
- ~~**That is a dated fact.** Once the demo holds authored CV content, this apply destroys it...~~ **RESOLVED 2026-08-14 — [T-018](T-018-mysql-on-dedicated-ebs-volume.md) is `done`** ([cv-infra#16](https://github.com/erfeamor/cv-infra/pull/16)). MySQL's datadir now lives on `vol-092113db466c84bc1`, a volume with a lifecycle independent of the instance, and survival across replacement was **proven by test**: rows written between two applies read back intact, with the volume UUID unchanged. **T-014's apply no longer destroys the database** — its watch-out to that effect (`T-014` §"user_data_replace_on_change", and its H2 note) is superseded. T-014 is still `high` risk for its other reasons (SG ingress, published ports, CORS, edge routing); it is simply no longer destructive to data.
  - Still re-check the database before T-014's apply, but the check is now cheap insurance rather than a gate: confirm `/var/lib/cv-mysql` is mounted from the dedicated volume (`findmnt`), not that the data is expendable.
  - **One new trap arrived with the fix**, filed as **[T-021](T-021-mysql-password-rotation-persistent-datadir.md)**: because the datadir now survives, `mysql:8.4` skips initialization and keeps its original credentials, so rotating `var.db_password` makes Flyway fail auth, aborts the bootstrap under `set -e`, and leaves the box with **no domain-service container at all**. Anyone editing `db_password` before T-021 lands should expect that.
- **T-403 was not part of the original ask.** It surfaced while verifying the BFF gap; without it T-014 delivers a BFF that nothing in AWS consumes.
- **Deadline context:** anything meant to be demonstrated live must exist before the T-012 dates (credits **~2026-11-17** at the real burn rate — re-derived 2026-08-14, was ~2026-12-20; Free-plan window 2027-01-12). If T-012 resolves to teardown-and-rebuild, this chain must be **in Terraform before teardown** or the rebuild will not reproduce it.


---

For historical context and board consistency sweeps, see [HISTORY.md](HISTORY.md).
