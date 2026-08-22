# Board

Protocol: [README.md](README.md) · Contract: [docs/api-contract.md](../../docs/api-contract.md)

## M2 — Complete the domain model end-to-end

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-101](T-101-experience-resource.md) | Experience resource in the domain API | cv-domain-service | done | backend-developer | — | [#3](https://github.com/erfeamor/cv-domain-service/pull/3) |
| [T-102](T-102-education-resource.md) | Education resource in the domain API | cv-domain-service | done (**A1 + stage-4 QA + review**) | backend-developer | — | [#5](https://github.com/erfeamor/cv-domain-service/pull/5) |
| [T-103](T-103-skills-catalog-and-assignments.md) | Skill catalog + person-skill assignments | cv-domain-service | done (**stage-4 QA clean, race proven live**) | backend-developer | — | [#7](https://github.com/erfeamor/cv-domain-service/pull/7) |
| [T-104](T-104-project-resource.md) | Project resource in the domain API | cv-domain-service | done (**stage-4 QA clean; ordering + T-107 proven on live 8.4**) | backend-developer | — | [#8](https://github.com/erfeamor/cv-domain-service/pull/8) |
| [T-105](T-105-experience-ordering-retrofit.md) | Retrofit contract ordering onto the merged Experience resource | cv-domain-service | todo | | T-006 | |
| [T-106](T-106-restrict-openapi-and-actuator-exposure.md) | Stop serving the OpenAPI spec and Prometheus metrics anonymously | cv-domain-service | done (**Jenkins green**) | backend-developer | — | [#4](https://github.com/erfeamor/cv-domain-service/pull/4) |
| [T-107](T-107-post-id-cross-person-write.md) | **POST with a client-supplied id overwrites another person's row** (person, experience) | cv-domain-service | done (**exploit + fix proven live**) | backend-developer | — | [#6](https://github.com/erfeamor/cv-domain-service/pull/6) |
| [T-108](T-108-untransacted-update-read-modify-write.md) | **PUT is an untransacted read-modify-write** — a concurrent DELETE makes it re-INSERT the row under a new id (all three section resources) | cv-domain-service | todo | | — | |
| [T-151](T-151-dev-seeds-cv-sections.md) | Dev seed data for CV sections | cv-database | done (**both T-028 provenance halves obtained; ordering proven through the API**) | backend-developer | — | [#4](https://github.com/erfeamor/cv-database/pull/4) |
| [T-201](T-201-bff-cv-aggregate.md) | BFF: aggregated public CV endpoint | cv-bff-node | todo | | T-101…T-104, T-006 | |
| [T-301](T-301-admin-cv-sections-crud.md) | Admin UI: CRUD for the four sections | cv-admin-react | todo | | T-101…T-104 | |
| [T-401](T-401-public-cv-sections.md) | Public site: render full CV | cv-public-vanilla | todo | | T-201 | |
| [T-402](T-402-public-react-cv-sections.md) | Public site (React): render full CV sections | cv-public-react | todo | | T-201 | |
| [T-501](T-501-e2e-cv-milestone.md) | End-to-end verification + roadmap close-out | cv-project | todo | | all above **+ T-105, T-014, T-403, T-404** | |

### Parallelization notes (read before claiming)

- **Wave 1 (5 agents in parallel):** T-101, T-102, T-103, T-104, T-151 — fully independent; the four API tasks touch disjoint packages, so PRs won't conflict except trivially.
  - ~~**Status as of 2026-08-09:** T-101 is **merged**… T-102/T-103/T-104 reached **H1 and stopped**… T-151 never started.~~ ~~**Superseded 2026-08-20.** **Status as of 2026-08-20:** T-101 (`09282ed`) and T-102 (`42abe91`) are **merged**. **Wave 1 is now T-103, T-104 and T-151.**~~ **Superseded again 2026-08-22 — T-103 merged on 2026-08-21 (`2e54394`) and this line kept sending readers at it.** ~~**Status as of 2026-08-22:** T-101 (`09282ed`), T-102 (`42abe91`) and T-103 (`2e54394`) are **merged**. **Wave 1 is now T-104 and T-151.**~~ ~~**Superseded later the same day — T-104 merged as `7677fee`.** **Wave 1 is now [T-151](T-151-dev-seeds-cv-sections.md) alone**, and it is the only wave-1 task that never started.~~ **WAVE 1 IS COMPLETE, 2026-08-22** — T-151 merged as `865784f`. All five wave-1 tasks are `done`. **All four API resources are done**, so [T-201](T-201-bff-cv-aggregate.md) and [T-301](T-301-admin-cv-sections-crud.md) are unblocked and wave 2 is open. The "start at implementation, not refinement" instruction served all three of T-102/T-103/T-104 and is retained for the record: an 18-day-old ratified H1 was worth more than a re-refinement each time, provided the premises that moved were written down first.
- **Wave 2:** T-201 and T-301 — both may *start* against the contract (mocked upstreams) during wave 1; their final verification needs wave 1 merged.
- **Wave 3:** T-401 and T-402 after T-201 (different repos — run them in parallel); T-501 strictly last.
- ~~T-103 is the highest-risk API task (composite key, upsert, 409) — assign it to the strongest agent or start it first.~~ **Done 2026-08-21** — and the advice was right: it is the task whose acceptance criterion turned out to be wrong. **T-104 is now the only API task left**, and the concurrency lesson it inherits is recorded in §"T-103 merged" below.
- **T-105 was depended on by nothing until 2026-08-17.** It is the only task making Experience contract-compliant on ordering, yet it appeared in no `depends_on` anywhere — so the milestone could have been declared verified with one of four sections served in arbitrary row order. It is now in T-501's. It still does not block T-201 (that is deliberate — see T-105), so it belongs in wave 1 alongside T-102/T-103/T-104.

### Recent structural changes (context — M2 is one task in)

~~The four-section milestone is untouched (every task above is genuinely `todo`)~~ — **stale, corrected 2026-08-17.** That parenthetical sat directly under a note recording T-101 as merged, and above a table whose first row reads `done`; it dates from before T-101 landed on 2026-08-09. M2 is **one of eleven tasks complete**. Some repos changed since the board was written — read before claiming:

- **cv-bff-node is now TypeScript** (strict, ts-jest/tsc). T-201's route and tests are `.ts`, type the aggregate payload, and `npm run typecheck` is a gate.
- **cv-admin-react is hexagonal TypeScript** (`domain ← application ← composition → infrastructure`). T-301 follows the repo CLAUDE.md's "adding a section resource" recipe (entity/port → adapter → store factory → composition root → form/pages) — there is no flat `src/api/client.js`.
- **cv-public-react** exists as a second public site (Next.js/ISR from the BFF), currently person-only. Rendering its CV sections is now tracked as **T-402** (the React counterpart of T-401); its domain types already cover all four sections, so the work is presentation + use-case only.
- **The database is self-hosted MySQL 8.4**, not RDS. cv-infra moved MySQL onto a container on the domain-service EC2 (PR #8) to shed the RDS cost and the MySQL 8.0 Extended Support charge. Impact on M2: the target engine is **MySQL 8.4** (migrations verified compatible), and **production applies migrations only** — dev-seeds (T-151) stay dev-only. Backups, dev/prod version parity, and doc cleanup are tracked as **T-001** (below), outside M2.

## Infra & ops (outside M2)

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-001](T-001-selfhost-mysql-followups.md) | Backup: replace the managed backups lost when MySQL left RDS | cv-infra | done (applied + restore verified) | infrastructure-engineer | — | [#15](https://github.com/erfeamor/cv-infra/pull/15) |
| [T-016](T-016-dev-prod-mysql-parity.md) | Dev/prod parity: bump the local MySQL to 8.4 | cv-project (meta) | done | infrastructure-engineer | T-152 ✔ | [#52](https://github.com/erfeamor/curriculum/pull/52) |
| [T-152](T-152-mysql-84-parity-cv-database.md) | Dev/CI parity: bump cv-database's stack **and its migration gate** to MySQL 8.4 | cv-database | done (**merged; CI-log proof still outstanding**) | backend-developer | — | [#3](https://github.com/erfeamor/cv-database/pull/3) |
| [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md) | cv-database's Jenkins `Deploy` stage is gated on `main`, a branch that does not exist here — and still names RDS | cv-database | todo | | T-152 | |
| [T-154](T-154-jenkins-pipeline-timeout.md) | No `timeout {}` on cv-database's pipeline: a hung build **holds the only CI host up** (~$17.24/mo) | cv-database | todo | | — | |
| [T-155](T-155-flyway-version-supports-mysql-84.md) | Flyway 10 does not claim MySQL 8.4 support — and it runs against 8.4 **in production** | cv-database + meta + cv-infra | todo | | — | |
| [T-017](T-017-docs-drift-rds-to-selfhosted.md) | Docs drift: name MySQL 8.4 as the target engine in cv-database's docs (**title corrected — the meta repo's five RDS mentions are already permitted by its own AC1**) | cv-project (meta) + cv-database | todo | | — | |
| [T-018](T-018-mysql-on-dedicated-ebs-volume.md) | MySQL on a dedicated EBS volume, surviving instance replacement | cv-infra | done (applied + survival proven) | infrastructure-engineer | — | [#16](https://github.com/erfeamor/cv-infra/pull/16) |
| [T-021](T-021-mysql-password-rotation-persistent-datadir.md) | Rotating `db_password` breaks silently now the datadir persists | cv-infra | todo | | T-018 | |
| [T-022](T-022-domain-service-origin-bypasses-cloudfront.md) | Domain service reachable on :8080 bypassing CloudFront; leaks OpenAPI spec | cv-infra | done (**applied + verified by request**) | infrastructure-engineer | — | [#20](https://github.com/erfeamor/cv-infra/pull/20) |
| [T-019](T-019-ci-host-on-demand.md) | Stop paying for an idle CI host: start on demand, stop when quiet | cv-infra | done (**all criteria met bar the billing week**) | infrastructure-engineer | — | [#17](https://github.com/erfeamor/cv-infra/pull/17) |
| [T-002](T-002-jenkins-on-drone-host.md) | Host Jenkins on the existing Drone CI instance | cv-infra | done | infrastructure-engineer | — | [#11](https://github.com/erfeamor/cv-infra/pull/11) |
| [T-003](T-003-ci-docs-reflect-jenkins.md) | Correct the CI documentation to match reality | cv-project (meta) | todo | | T-002 | |
| [T-004](T-004-terraform-state-hardening.md) | Harden Terraform state: permissions now, remote backend properly | cv-infra | todo | | — | |
| [T-005](T-005-ci-secret-blast-radius.md) | Limit CI secret blast radius: block IMDS from containers | cv-infra | todo | | T-002 | |
| [T-006](T-006-contract-section-ordering.md) | Contract: define ordering for the CV section collections | cv-project (meta) | done | tech-product-owner | — | [#23](https://github.com/erfeamor/curriculum/pull/23) |
| [T-007](T-007-ecs-agent-cleanup.md) | Remove the crash-looping ecs-agent from the CI host | cv-infra | todo | | T-002 | |
| [T-008](T-008-drone-host-backup-and-snapshot.md) | Retire the T-002 gate snapshot, give the CI host a real backup | cv-infra | todo | | T-002 | |
| [T-009](T-009-user-data-size-ceiling.md) | Get the provisioning script out of user_data before it hits the 16 KB wall | cv-infra | done (**98.3% → 21.5%**, applied + verified) | infrastructure-engineer | T-002 | [#18](https://github.com/erfeamor/cv-infra/pull/18) |
| [T-010](T-010-aws-credit-runway.md) | Track the AWS credit runway and free-plan cliff before it stops the demo | cv-project (meta) | done | tech-product-owner | — | |
| [T-011](T-011-budget-credit-alarm.md) | Budget alarm that fires on credit burn, not on the invoice | cv-infra | done | infrastructure-engineer | — | [#13](https://github.com/erfeamor/cv-infra/pull/13) |
| [T-012](T-012-aws-endgame-decision.md) | **Decide Paid-vs-teardown before the Free-plan window closes** | cv-project (meta) | todo | | — | **due 2026-11-01** |
| [T-020](T-020-cost-model-correction.md) | Correct the stale cost model; stop the budget alarm crying wolf | cv-project (meta) + cv-infra | done (both halves; alarm decision = **change nothing**) | tech-product-owner | — | [#36](https://github.com/erfeamor/curriculum/pull/36) + [cv-infra#19](https://github.com/erfeamor/cv-infra/pull/19) |
| [T-023](T-023-meta-docs-stale-bff-smoke-path.md) | The documented E2E smoke command curls a path the BFF no longer serves (**four files, not three — scope corrected**) | cv-project (meta) | todo | | — | |
| [T-024](T-024-contract-skill-assignment-put-shape.md) | Contract: split the skill-assignment PUT's request body from its response | cv-project (meta) | done | tech-product-owner | — | [#41](https://github.com/erfeamor/curriculum/pull/41) |
| [T-025](T-025-verify-requests-come-from-our-cloudfront.md) | The edge is not an authenticator: prove requests come from OUR distribution | cv-infra + cv-domain-service | todo | | T-022 | |
| [T-026](T-026-first-build-after-cold-start-fails.md) | First Jenkins build after a cold start fails (`No build record could be located`) | cv-infra | todo | | T-019 | |
| [T-027](T-027-contract-ordering-note-sql-vs-jpql.md) | Contract: the ordering note prescribes SQL syntax for a JPQL context (**T-104 hits it next**) | cv-project (meta) | todo | | — | |
| [T-028](T-028-qa-env-generator-worktree-build-context.md) | QA stack builds `master`, not the worktree under test (**silent false pass**) | cv-project (meta) | done (**bind mounts too; T-151's failure mode closed**) | infrastructure-engineer | — | [#49](https://github.com/erfeamor/curriculum/pull/49) |
| [T-029](T-029-code-review-cannot-see-worktrees.md) | `/code-review` **silently reviews the wrong thing** without an explicit target (cause corrected — not worktrees) | cv-project (meta) | todo | | — | |
| [T-030](T-030-pr3-build1-success-then-error.md) | A Jenkins build posted `success` then `error` one second later — **not** yet attributable to T-026 | cv-infra | todo | | — | |

**Cost model is stale as of 2026-08-14 — the documented figures understate real burn by a third.** `cv-infra/CLAUDE.md` and T-010's runway both encode *~$0.92/day ≈ $28/month*. The 2026-08-08 `t3.micro`→`t3.small` resize of the CI host (T-002, deliberate, for Maven headroom) took the real rate to **~$1.23/day ≈ $37.30/month**, verified against the August cost export and `describe-instances`. Consequences: the credits deplete **~25% sooner in elapsed time**, which moves T-012's date; and the `$30` monthly budget is now **structurally exceeded (~124%)**, so its 100/120% thresholds will fire every month from September — an alarm that always fires stops being a signal. Note [cv-infra#14](https://github.com/erfeamor/cv-infra/pull/14) deliberately refused to raise that limit, so this needs a decision rather than a bump. **T-014 may push it further** — its own watch-outs say the domain-service box may need `t3.small` for RAM, another +$8.62/month → ~$46. [T-019](T-019-ci-host-on-demand.md) is the largest available offset (~$17.24/month).

**Nobody re-ran the division — done 2026-08-14, and it moves two ratified decisions.** The note above recorded that the rate changed but left every date derived from the old one standing. Re-deriving from T-010's console read ($120.66 remaining on 2026-08-11) at the verified **$1.23/day**:

| Grant | modelled at $0.92/day | re-derived at $1.23/day | binds |
|---|---|---|---|
| $160 (current) | 2026-12-20 | **~2026-11-17** | credits, by ~8 weeks |
| $200 (after the two activities) | 2027-01-12 — window binds | **~2026-12-19** | credits still, by ~3 weeks |

Two consequences, neither cosmetic:

1. **[T-012](T-012-aws-endgame-decision.md)'s `due: 2026-12-20` is now after the money is gone** in the $160 case. Re-dated in that file.
2. **T-010's ratified decision (b) — "do NOT trim the run rate" — no longer follows from its own reasoning.** It rested on the crossover at ~$32/month: *below* that the 6-month window binds first and savings expire unspent. Real burn is **$37.30/month, above the crossover**, so credits bind first and trimming now buys real elapsed demo time — up to ~8 weeks in the $160 case. That does not automatically mean *build* [T-019](T-019-ci-host-on-demand.md): its own DoR §4 notes stopping the host by hand saves the identical $17.24 with no new IAM, no public endpoint and nothing to break. What changed is that the saving is now worth *something*, where T-010 correctly concluded it was worth nothing. **Decide it at T-019's H1.**

~~**These figures are derived, not read.** … confirming it needs a console read.~~ **Read 2026-08-19 — see below. Everything above this line is superseded; it is kept because the arithmetic was right each time and only the premises moved.**

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

> **Closed out 2026-08-20: [T-019](T-019-ci-host-on-demand.md) is merged and the M2 backend wave is unblocked.** PR [#17](https://github.com/erfeamor/cv-infra/pull/17) is in `cv-infra` master (`bd65353`), applied 2026-08-19, and the manual webhook re-point **has been done** — `cv-domain-service` and `cv-database` both point at the doorbell Function URL, `active=true`, last delivery OK. A push to either repo now starts the CI host by itself; nothing needs starting by hand. Two criteria remain outstanding and are recorded in T-019 rather than held open as a status: the hook has only ever received a **`ping`** (2026-08-19T09:39:19Z), so *"the build actually runs"* is unproven until the first real push — **T-102 supplies it for free** — and the billing-week rate check needs elapsed time. Drone is deliberately **not** covered (T-019 ruling 5): `cv-admin-react`'s hook still points at `http://13.39.59.12/hook` and reads `last=unused`, so a push there neither builds nor wakes the box. That is T-301's problem when it arrives, and it is now written down somewhere other than inside T-019.

> T-013, T-014 and T-015 are part of the deployment chain below and are boarded there, not here, so there is one line per task to claim.

**Board-line correction 2026-08-13.** T-002's line above read `in_review` while its own task file had said `done` since PR [#11](https://github.com/erfeamor/cv-infra/pull/11) merged on 2026-08-09 — rule 1 requires both to be updated and only the file was. The line is now `done`. The practical cost was not cosmetic: **T-003, T-005, T-007, T-008 and T-009 all gate on T-002**, so five infra tasks read as un-claimable for four days. They are claimable now, and none is owned. (The sentence that followed here named T-001 as "the only thing that has to happen before the deployment chain reaches its destructive step" — superseded the same day: T-001 is `done`, and the destructive step is *accepted*, not gated. The durable fix is [T-018](T-018-mysql-on-dedicated-ebs-volume.md).)

> **T-001 applied and verified 2026-08-13 — backups are now real.** The nightly timer is enabled on `i-038600c71d141035b` (next run 03:04 UTC), a forced run landed `cv-20260813T152654Z.sql.gz` in `s3://cv-project-mysql-backup-dev/mysql-dumps/`, and that dump was **restored into a throwaway MySQL 8.4 container** — all six tables plus the Flyway history. The restore, not the upload, is what makes this claim worth anything.
>
> The instance was replaced as expected, so the previous test data is gone and the verified dump is schema-only. The mechanism is proven; it has simply had no authored content to capture yet. ~~**T-018 is still the thing that matters before real content exists** — a nightly dump does not save data written between dumps, and T-014's apply will replace this box again.~~ **[T-018](T-018-mysql-on-dedicated-ebs-volume.md) landed 2026-08-14** ([cv-infra#16](https://github.com/erfeamor/cv-infra/pull/16)): the datadir is on an independent volume and survival across replacement is proven, so T-014's apply no longer replaces the database along with the box. The nightly dump and the dedicated volume now cover different failures — the dump protects against corruption and bad writes, the volume against instance churn — and neither substitutes for the other.

## Public-path deployment gap (cross-repo — blocks T-501)

**`cv-bff-node` has never been deployed to AWS, and neither has `cv-public-vanilla`.** Verified against the live account 2026-08-11/12: no BFF ECR repo, no BFF container in `user_data`, CloudFront `/api/*` goes straight to Java on :8080, and `s3://cv-project-frontend-dev/` holds only `admin/`. The only BFF-named object in the account is an empty log group. The whole **public** path is absent; the admin is live and unaffected because it bypasses the BFF by design (`docs/architecture.md:28`) — which is exactly why the gap stayed invisible.

It stayed unfiled because the IaC asserts the opposite: `cv-infra/compute.tf:1` and `cv-infra/README.md:14` both claim the box already runs the BFF. Same failure class as T-010 — a documented assumption never re-checked against the account.

Deploying it is **not** just adding a container. Two blockers are contract-level, which is why T-013 leads: the BFF serves `GET /api/v1/people/:id` on the **same path** CloudFront already routes to Java (`src/app.ts:26`), and it gates *all* of `/api/v1` behind `requireAuth()` when `AUTH_ENABLED=true` (`src/app.ts:22-25`), which would 401 every anonymous visitor.

One task per repo. The **numbered** rows are strictly sequential and their `depends_on` enforces the order; the unnumbered rows hang off the chain and are claimable independently once their own dependency is met. **This is the board line for all seven; claim here.** (Corrected 2026-08-17: this said "exactly one is claimable at a time", which stopped being true when T-202 merged — T-204 became claimable alongside T-014, and T-404 now joins it.)

| # | ID | Title | Repo | Status | Owner | Depends on | PR |
|---|----|-------|------|--------|-------|------------|----|
| 1 | [T-013](T-013-contract-bff-public-routing.md) | Contract: BFF public edge path + anonymous reads | cv-project (meta) | done | tech-product-owner | — | [#22](https://github.com/erfeamor/curriculum/pull/22) |
| 2 | [T-202](T-202-bff-public-routing-and-auth.md) | BFF: public edge path + anonymous read routes | cv-bff-node | done | fullstack-developer | T-013 | [#4](https://github.com/erfeamor/cv-bff-node/pull/4) |
| 3 | [T-014](T-014-deploy-bff-to-aws.md) | **Deploy cv-bff-node to AWS — registry, container, edge route** | cv-infra | todo (**H1 done** — seven rulings + test plan, start at implementation) | | T-013, T-202 | |
| 4 | [T-403](T-403-public-vanilla-deploy.md) | Public site (vanilla): deploy + point at the deployed BFF | cv-public-vanilla | todo | | T-014 | |
| 5 | [T-015](T-015-docs-reflect-deployed-bff.md) | Correct the meta docs that claim the BFF is deployed | cv-project (meta) | todo | | T-014, T-403 | |
| — | [T-203](T-203-bff-ci-deploy-stage.md) | BFF CI: push to ECR and roll the container on master | cv-bff-node | todo | | T-014 | |
| — | [T-204](T-204-bff-validate-person-id-param.md) | BFF: validate the person id before the upstream call | cv-bff-node | todo | | T-202 | |
| — | [T-404](T-404-public-react-point-at-deployed-bff.md) | Public site (React): point Vercel's `BFF_URL` at the deployed BFF | cv-public-react | todo | | T-014 | |

**~~[T-022](T-022-domain-service-origin-bypasses-cloudfront.md) should be done before T-014~~ — DONE 2026-08-20 ([cv-infra#20](https://github.com/erfeamor/cv-infra/pull/20)); the sequencing advice below is satisfied, and what T-014 inherits from it is recorded in T-014 itself (its own security group — the prefix list burns 46 of the 60-rule quota). Kept for the reasoning. It was invisible on this board until 2026-08-17.** Both tasks argue it — T-014's ruling 1 and T-022's dev-loop notes — but neither the chain table nor its prose mentioned T-022, and T-014 is the task everyone is told to claim next. It is **not** a `depends_on` edge in either direction (deliberately: neither blocks the other). The argument is that T-022 applies the *same* managed-prefix-list fix to port 8080 that T-014's ruling 1 mandates for port 3000, so doing it first means T-014 follows an established pattern instead of inventing one, and the reviewer sees one consistent approach across both ports. T-022 is also cheap (in-place SG change, `risk: normal`, easily reverted) and closes a live unauthenticated `/v3/api-docs` disclosure that grows automatically with every M2 resource that lands.

**T-013 and T-202 both merged 2026-08-13** ([#22](https://github.com/erfeamor/curriculum/pull/22), [cv-bff-node#4](https://github.com/erfeamor/cv-bff-node/pull/4)). The contract settles the edge path (`/bff/*`, prefix carried to the origin), the two-route anonymous allowlist, and `/metrics`; the BFF now implements them and `/api/v1` is gone from that repo.

**T-014 is next in the chain and IS claimable.** Its `depends_on` is `[T-013, T-202]` and both are `done`. This paragraph previously said the opposite — that T-014 "is NOT claimable yet" because it gated on T-001 §1, "which is still `todo` and unowned" — and both halves of that were false by the time it was written: T-001 is `done` (applied and restore-verified 2026-08-13), and T-001 had already been **removed** from T-014's `depends_on` that same day for the reason recorded at the end of this section. **Corrected 2026-08-14.** This is the T-002 board-line bug repeating one day later: prose that gates a task, contradicted by the frontmatter it claims to describe. When a dependency changes, the task file and *every* prose reference to it move together.

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
- ~~**That is a dated fact.** Once the demo holds authored CV content, this apply destroys it...~~ **RESOLVED 2026-08-14 — [T-018](T-018-mysql-on-dedicated-ebs-volume.md) is `done`** ([cv-infra#16](https://github.com/erfeamor/cv-infra/pull/16)). MySQL's datadir now lives on `vol-092113db466c84bc1`, a volume with a lifecycle independent of the instance, and survival across replacement was **proven by test**: rows written between two applies read back intact, with the volume UUID unchanged. **T-014's apply no longer destroys the database** — its watch-out to that effect (`T-014` §"user_data_replace_on_change", and its H2 note) is superseded. T-014 is still `high` risk for its other reasons (SG ingress, published ports, CORS, edge routing); it is simply no longer destructive to data.
  - Still re-check the database before T-014's apply, but the check is now cheap insurance rather than a gate: confirm `/var/lib/cv-mysql` is mounted from the dedicated volume (`findmnt`), not that the data is expendable.
  - **One new trap arrived with the fix**, filed as **[T-021](T-021-mysql-password-rotation-persistent-datadir.md)**: because the datadir now survives, `mysql:8.4` skips initialization and keeps its original credentials, so rotating `var.db_password` makes Flyway fail auth, aborts the bootstrap under `set -e`, and leaves the box with **no domain-service container at all**. Anyone editing `db_password` before T-021 lands should expect that.
- **T-403 was not part of the original ask.** It surfaced while verifying the BFF gap; without it T-014 delivers a BFF that nothing in AWS consumes.
- **Deadline context:** anything meant to be demonstrated live must exist before the T-012 dates (credits **~2026-11-17** at the real burn rate — re-derived 2026-08-14, was ~2026-12-20; Free-plan window 2027-01-12). If T-012 resolves to teardown-and-rebuild, this chain must be **in Terraform before teardown** or the rebuild will not reproduce it.

## Board consistency sweep — 2026-08-17

A read of all 37 task files against each other and against the contract. **No status changed and no work was done** — this is drift repair. Recorded rather than silently applied, per the convention this board already follows for the T-002 and T-014 board-line corrections.

**Four unowned items filed as tasks.** Each had been handed from one task file to another and never landed:

| New | What it was | Where it was lost |
|---|---|---|
| [T-023](T-023-meta-docs-stale-bff-smoke-path.md) | `CLAUDE.md:37` and `README.md:247` still document the E2E smoke as `curl localhost:3000/api/v1/people/1` — a path T-202 deleted from the BFF on 2026-08-13 | T-015 is gated behind T-014; T-016 notices it in passing; T-202 is in another repo |
| [T-024](T-024-contract-skill-assignment-put-shape.md) | The contract clarification T-103's DoR ruling 1 promised ("a follow-up docs PR clarifies this wording") | promised at refinement, never opened, held by no task |
| [T-404](T-404-public-react-point-at-deployed-bff.md) | Pointing cv-public-react's Vercel `BFF_URL` at the deployed BFF | T-402 → "tracked at T-501"; T-403 → "handle it at T-501"; T-501 → silent |
| — | The meta `CLAUDE.md`'s stale `~$28/mo` | folded into **T-020 §3**, which named only `cv-infra/CLAUDE.md` and T-010 |

**Six contradictions corrected in place**, each struck rather than deleted:

1. **T-401 and T-402 still specified `GET /api/v1/people/:id/cv`** — the pre-T-013 path. T-013's review caught this exact drift in T-201 and fixed it *only there*; the other two consumers of the same endpoint were missed for four days. Both now read `/bff/api/v1`.
2. **T-501's step 2 curled the same dead path**, so the milestone's own end-to-end verification would have 404'd.
3. **T-004 §3 and T-021 contradicted each other on `db_password`.** T-004 offers rotation as an open decision; T-021 says rotating it aborts the bootstrap and leaves the box with no domain-service container. Neither file referenced the other. Cross-linked both ways.
4. **T-014's numbering**: "six rulings" against seven, a pointer to "ruling 7's correction" that belongs to ruling 1, and a baseline capture citing "criterion 4" (the criterion T-018 superseded) instead of 6.
5. **T-014's `user_data_replace_on_change` watch-out still said the apply destroys MySQL** — superseded by T-018, but only two sections further down, so a reader who stopped at the watch-outs got the opposite answer. Struck at the watch-out itself.
6. **This board claimed "every task above is genuinely `todo`"** in the M2 section, directly beneath its own note that T-101 had merged.

**Three stale premises struck**: T-012's threshold dates (24 Sep / 15 Nov / 20 Dec, derived at the superseded $0.92/day, inside the file that re-derives everything else at $1.23/day) · T-004's "do before applying T-002" (T-002 applied 2026-08-09) · T-016's "T-014 gates on T-001" (that edge was removed 2026-08-13) · T-009's housekeeping request that T-007 already fulfilled.

**Frontmatter hygiene**: `security_review: required` normalized to `true` in five files (two vocabularies for one boolean) · T-011's `pr:` filled from its checkpoint, per board rule 6 · T-009 given the missing `pr:` key · T-010's DoD branch name reconciled with its frontmatter · T-101's checkpoint `stage: pr` → `done`.

**Left alone deliberately.** T-201, T-301, T-401, T-402 and T-501 carry no `risk` or `security_review`. Assigning them is a stage-0 refinement output, not a board edit — inventing values here would manufacture ratified-looking decisions nobody made. They get them when they are refined.

## Board consistency sweep — 2026-08-20

A second pass over all 40 task files, this time **verified against the live systems** rather than only against each other: `git log` in the eight sibling repos, `aws ec2 describe-instances`, `aws freetier`, and the GitHub webhook + delivery API. No task's scope changed and no product code was touched.

**What the live checks confirmed.** T-101, T-202, T-006, T-013, T-018, T-009 and T-020 have all genuinely landed in their repos. Every task file appears on this board and every board line has a file (40/40). `cv-project-drone` is still `stopped` and `cv-project-domain-service` still `running`, so T-020's measured cost model holds as of today.

**What was wrong:**

1. **[T-019](T-019-ci-host-on-demand.md) was merged but boarded `in_review`** — PR #17 is in `cv-infra` master as `bd65353`. Board rule 6 says merge → `done`. **Third recurrence** of the drift class this board corrected for T-002 (2026-08-13) and again in the 2026-08-17 sweep. Fixed on the line above and in the file.
2. **T-019's top-level `pr:` was empty** while `checkpoint.pr` held the URL — the *exact* hygiene bug the 2026-08-17 sweep fixed in T-011, recurring on the very next task to reach review. Filled in.
3. **T-019's `remaining:` note was stale in its premise and right in its conclusion.** It said the webhook re-point had not happened and the automation was "inert"; both hooks were in fact re-pointed on 2026-08-19. The criterion *is* still unmet, but only because no `push` has ever reached the doorbell — only a `ping`. Corrected in place, old text kept.
4. **[T-012](T-012-aws-endgame-decision.md) had never absorbed T-020's measured read** — the single most consequential item in this sweep. The board's only deadline-bearing task still argued end to end from the superseded **$1.23/day**: credits binding by ~8 weeks, exhaustion ~2026-11-17, and **option A priced at ~$37/month against a real ~$21**. It still carried *"These dates are derived, not read — T-020 holds that read and will correct this task again if the console disagrees."* T-020 is `done`, it did the read, the console **did** disagree, and §5's conclusion was written into T-020 and into this board but **never into T-012**. A decision document arguing from superseded arithmetic, waiting to be opened on 1 November. Corrected with a measured block at the top; `due: 2026-11-01` **deliberately unchanged**, per T-020 §5.
5. **[T-005](T-005-ci-secret-blast-radius.md) still listed the GitHub webhook secret as work to do.** T-019 ruling 4 built it and said in terms that *"T-005 should drop that bullet rather than build it twice"* — a hand-off recorded only in the file doing the handing. Struck, with a pointer.
6. **[T-023](T-023-meta-docs-stale-bff-smoke-path.md) contradicted itself on scope**: *"Two files, one path each"* above a bullet list of three, the third hedged as *"check `README.es.md`"*. `README.es.md:247` does carry the dead path — verified — so the hedge is now a fact and the count is three.
7. **Frontmatter hygiene**: `security_review` was missing entirely from T-003, T-007 and T-151, all three of which *do* carry `risk` (so they are not covered by the 2026-08-17 sweep's deliberate exemption for unrefined tasks). Set to `false` per adapter §5, flagged in-line as a stage-0 default that A1 overrides on the real diff.
8. **Four stale worktrees** at `cvdl-worktrees/{T-102,T-103,T-104,T-151}` held their `feat/*` branches, clean and zero commits ahead of master — left behind when those claims were reset. They made `git branch` read as work-in-flight. Removed; the dev-loop recreates them on demand.

**Filed as work, not drift:** [T-024](T-024-contract-skill-assignment-put-shape.md) was implemented in this session rather than left on the board ([#41](https://github.com/erfeamor/curriculum/pull/41), **merged 2026-08-20** as `3a45f94`), because it is a docs-only contract change and landing it before T-103 means the implementer builds from `docs/api-contract.md` instead of from a ruling buried in a task file — which is the arrangement the contract exists to replace. **T-103's DoR ruling 1 now points at the merged contract text instead of promising a future PR**, closing the last of the four hand-offs the 2026-08-17 sweep filed.

**The recurring failure this board keeps finding, stated once more:** every item above is a fact that was true when written and was never re-checked. Items 1–3 were each *recorded correctly by the task that did the work* and then not propagated; item 4 is the same shape at the scale of a deadline. The board's convention of striking rather than deleting is what makes them findable — it is working, and it is not a substitute for re-reading.

## T-022 applied — and what its security review cost the next two tasks (2026-08-20)

**The direct-to-origin path is closed, proven by request from outside AWS** ([cv-infra#20](https://github.com/erfeamor/cv-infra/pull/20)). `:8080/v3/api-docs`, `/actuator/health` and `/api/v1/people/1` all answered before the change (200 / 200 / 401) and all time out after it, while the edge is untouched (`cf /api/v1/people/1` 401, `cf /v3/api-docs` 403, `cf /admin/` 200). The 401 through CloudFront is what proves the origin is still reachable from the edge — an unreachable origin gives 502/504.

**Two findings came out of it that other tasks inherit, and both are the kind that fail at apply time rather than review time:**

1. **[T-014](T-014-deploy-bff-to-aws.md) cannot put port 3000 on the domain-service security group.** An AWS-managed prefix list counts against the 60-rule inbound quota as its **entry count**, not as one rule; the CloudFront list held **46** entries on 2026-08-20. One reference fits, two do not. The BFF needs its own security group. Written into T-014 above its scope section, because ruling 1 as drafted would fail on apply.
2. **The prefix list proves "a CloudFront distribution", not "ours"** — it is shared by every CloudFront customer, so an attacker's own distribution still reaches the origin and still reads the spec. Raised as the one MEDIUM finding by T-022's forced `/security-review` and **deliberately not fixed in that PR** (board rule 3 — both remedies are cross-repo or out of scope, which T-022's own body said before the review existed). Filed as **[T-025](T-025-verify-requests-come-from-our-cloudfront.md)** (shared-secret origin header — closes the bypass class) and **[T-106](T-106-restrict-openapi-and-actuator-exposure.md)** (stop `permitAll`-ing `/v3/api-docs`, `/swagger-ui/**` and `/actuator/prometheus` in `SecurityConfig.java:38-39`, which is *why* it was readable — cheap, independent, and the whole answer if T-025 is declined at H1).

**T-022's own claim is corrected on the task**: `/v3/api-docs` is unreachable **directly**, not unreachable from the internet. That distinction is the entire content of finding 2, and stating it the strong way is how it would have been forgotten.

**One acceptance criterion is outstanding and is not being quietly counted as met**: the admin UI loading its people list with a real Cognito JWT needs an interactive login. The anonymous 401 is strong evidence the path is intact; it is not the same check.

## T-019's last criterion is MET — and using it found a defect (2026-08-20)

**The doorbell fired on a real push, for the first time.** T-106's PR to `cv-domain-service` supplied it, exactly as predicted:

```
push 08:11:58Z (delivery 200) -> doorbell -> ec2:StartInstances
  -> i-073e5284ca2a1ceed  stopped -> running
  -> Jenkins boots, multibranch scan finds PR-4, build starts 08:12:45Z
```

So T-019's *"a push to a watched repo starts the CI host"* is **proven end to end**, no longer by synthetic payload. Its companion criterion — *"and the build actually runs"* — is **also met**: builds #2 and #3 ran all four stages green in ~97s (checkstyle 0 violations, 35 tests, image tagged).

**But build #1 — the one the automation itself triggered — failed**, 47 seconds after the instance started, with `No build record cv-domain-service/PR-4#1 could be located` and a `Lint` stage that opened and closed without executing anything. The identical commit then passed twice. Filed as **[T-026](T-026-first-build-after-cold-start-fails.md)**.

**Why that matters beyond one red build:** every first push after an idle period gets a red X whose fix is "push again", and it will be blamed on whatever code was pushed — it briefly looked like T-106 had broken CI. It is also the honest asterisk on T-019's criterion: *met by build #3, not by the build the automation triggered.*

This is the healthy outcome of T-019, not an argument against it. **The value of "prove it with a real push" was precisely this** — the synthetic payload proved the doorbell, and only a real push could have found what happens to the build on the other side of the boot.

## T-102 implemented — M2 is two of eleven (2026-08-20)

Picked up **at implementation**, not refinement, as its `reset_note` directed — the H1 checkpoint from 2026-08-04 was real and was used as written. [cv-domain-service#5](https://github.com/erfeamor/cv-domain-service/pull/5).

Structural twin of T-101 as specified: same package shape, same four rulings, same no-DTO trade-off. **It ships with contract ordering built in** (`findByPersonIdOrderByStartDateDescIdAsc`), which is the thing [T-105](T-105-experience-ordering-retrofit.md) still has to retrofit onto Experience — Education never had the gap.

**Stage-4 QA ran against live MySQL 8.4 on slot 1, and it earned its keep.** 18/18 checks passed, but the reason to run it was the `field_of_study` → `fieldOfStudy` mapping that H2 cannot police, and the strongest evidence is simply that **the service booted**: `ddl-auto: validate` against the real V1 schema fails at startup on a naming-strategy slip.

**It also found a defect — in the test, not the code.** C7 asserted `jsonPath("$.fieldOfStudy").doesNotExist()` for omitted optionals and passed, while the live body is `{"fieldOfStudy":null,...}` — the field *is* present. `jsonPath` treats a JSON null as absent, so C7 was green for the wrong reason and would have stayed green under `@JsonInclude(NON_NULL)`, which **would** break the contract's *"absent optionals serialize as `null`"*. Tightened to assert key count plus a null value. A unit test that passes for the wrong reason is worse than a missing one, and only the live stack showed the difference.

**A control for [T-026](T-026-first-build-after-cold-start-fails.md):** T-102's first push landed on an *already-running* box and its first build succeeded, where the cold-start push earlier the same morning failed on its first build. That is one data point, not a proof, but it points at cold start specifically rather than at first-builds generally — recorded there.

**Closed out:** `/code-review` ran and its three findings were fixed in the PR (see the section below); all three commits on the branch built green on Jenkins. **Merged as `42abe91`.** M2 is now **two of eleven**.

## T-102's code review found a cross-person write, and this board had it mislabelled (2026-08-20)

`/code-review` on [cv-domain-service#5](https://github.com/erfeamor/cv-domain-service/pull/5) returned one HIGH and two LOW. All three are fixed in that PR (`cbe077f`).

**The HIGH is the one worth reading, because this board had already seen it and waved it through.** T-102's test plan carried it as a coverage risk, in these words:

> *A client-supplied `"id": 999` in a POST body must not override the generated id. `PersonController.create` has the same exposure — flag, don't block, don't fix here.*

That is wrong about the impact, and the wrongness is what carried it unfixed through refinement, implementation **and** stage-4 QA. It is not an id override. It is an **authenticated cross-person write**:

1. `Education.id` is a private field with no setter — which reads as un-bindable. Jackson's `INFER_PROPERTY_MUTATORS` binds it anyway (verified empirically, not argued: `getId() == 999`).
2. A non-null id makes Spring Data's `save()` take `merge()` instead of `persist()`.
3. `create()` has already set the owning person to the **caller's**.
4. Net statement: `UPDATE education SET person_id = <caller>, … WHERE id = 999` — **another person's row is overwritten and handed to the caller, with `201` and the victim's id in the response.**

That is precisely the write `findByIdAndPersonId` scopes PUT and DELETE against (DoR ruling 2), arriving through the one verb with no existing row to scope to. **Fixed inside T-102** rather than deferred: shipping new code carrying a known cross-person write, because a task file said "flag, don't block", would be following process off a cliff. The test was confirmed **red first** — `201` where `400` is required.

**`PersonController` and `ExperienceController` have it identically and are already on `master`** — filed as **[T-107](T-107-post-id-cross-person-write.md)**, `risk: high`. Its DoR asks whether the answer is three local guards or one global one (`@JsonProperty(access = READ_ONLY)`, or disabling `INFER_PROPERTY_MUTATORS`), because the global answer would also cover **T-103 and T-104 before they are written** — otherwise those two arrive with the same hole and need the same retrofit.

**Context, recorded so nobody either panics or relaxes too far:** `/api/v1/**` requires a valid Cognito JWT in the deployed config, and since [T-022](T-022-domain-service-origin-bypasses-cloudfront.md) the origin is reachable only through CloudFront. So this is an *authenticated* attack and today the only credentials are the owner's. It becomes materially worse the moment the demo has a second user.

**The failure class, in a new costume.** [T-020](T-020-cost-model-correction.md) was a stale *number*. The T-002 board line was a stale *status*. This was a stale *severity assessment* — written down once in words that undersold it, then honoured by every later reader, including the person implementing the resource it undermined. The flag was not ignored. It was believed.

## T-107: the exploit reproduced, and the reason it survived (2026-08-20)

Fixed in person and experience ([cv-domain-service#6](https://github.com/erfeamor/cv-domain-service/pull/6)); education was already done in T-102. **Demonstrated against live MySQL 8.4 rather than argued** — guard temporarily removed, then restored:

```
POST /api/v1/people/2/experiences  {"id":<row owned by person 3>, "company":"PWNED", ...}

  before    id=1  person_id=3  company=VictimCo  role=Staff Engineer
  response  201,  {"id":1,"company":"PWNED",...}
  after     id=1  person_id=2  company=PWNED     role=owned
  GET /people/3/experiences  ->  []
```

The victim's row was reassigned to the caller and their CV entry disappeared. Guard restored: `400`, row untouched — verified for all three resources against the row itself, which is what T-107's acceptance criterion demanded.

**Why it survived three weeks in `master`, and this is the part worth keeping.** T-101 shipped a test called `clientSuppliedIdInThePostBodyIsIgnored`. It asserted `201` with the id "ignored", **and it passed**. Its comment explained why: *"the entity exposes no id mutator, so Jackson ignores it."* Jackson does not ignore it. The test passed because `givenSaveReturnsWithId(5L)` stubs `save()` to return an entity with id 5 whatever it receives — **the assertion measured the mock, not the code.**

So the sequence was: QA flagged the risk in words that undersold it → the implementer wrote a test that appeared to close it → the test passed → every later reader, including the one implementing T-102 against this very file as a template, took the question as answered. **A green test asserting the safe-looking behaviour is worse than no test**, because it answers the question before anyone thinks to ask it. The old body is kept in a comment where it stood.

**The decision, recorded as a decision.** `@JsonProperty(access = READ_ONLY)` would have closed this structurally — a new resource inherits protection whether or not its author knows the rule. It was **declined**: it discards a supplied id in silence, so a client that sent one believing it was updating gets a `201` for a different row and no signal it was wrong, and T-102 had already shipped `400`. Two behaviours across sibling resources would be worse than either. The price of that choice is that the guard must be *called* — so **[T-103](T-103-skills-catalog-and-assignments.md) and [T-104](T-104-project-resource.md) now carry it in their DoR**, including the instruction to confirm the test fails first.

**Severity in context:** `/api/v1/**` requires a valid Cognito JWT and, since [T-022](T-022-domain-service-origin-bypasses-cloudfront.md), the origin is reachable only through CloudFront. This is an authenticated attack and today the only credentials are the owner's. It becomes real the moment the demo has a second user — which is what an admin UI with logins (T-301) implies.

**[T-026](T-026-first-build-after-cold-start-fails.md) reproduced while landing T-107.** The reaper stopped the box at 09:59:17; T-107's push woke it; `PR-6#1` failed with the identical `No build record … could be located` and an empty `Lint` stage; a rebuild on the warm box went green. **Three for three on the pattern** — cold start fails, warm start succeeds — so it is now reproducible on demand rather than an anecdote, and cheap to bisect. It cost this task one spurious red build and a manual retrigger, which is exactly the papercut T-026 predicts for every developer's first push after an idle period.

## Board consistency sweep — 2026-08-20 (second pass, same day)

A third sweep, run after T-102, T-106, T-107 and T-022 all landed within hours of each other. **No status changed, no scope changed, no product code was touched** — every item is prose that was true when written and was contradicted by work that landed later the same day. Structural state was re-verified first and is clean: **44 task files ↔ 44 board rows**, no orphans in either direction, no frontmatter/board-line status mismatch, no `depends_on` pointing at a non-existent task, no `todo` task holding an owner, and all six recently-claimed merges confirmed in the sibling repos' `git log` (`09282ed` T-101, `4f38f77` T-106, `42abe91` T-102, `1327bf6` T-107, `da17414` T-022, `bd65353` T-019).

**Six contradictions corrected, struck rather than deleted:**

1. **[T-104](T-104-project-resource.md)'s coverage-risk list still said *"Client-supplied `\"id\": 999`: flag, don't block, don't fix here"*** — the exact sentence this board diagnosed as the root cause of [T-107](T-107-post-id-cross-person-write.md), contradicting §"Carry the T-107 guard — do not skip" **in the same file, added the same day**. T-104 is claimable now, and coverage-risk bullets read as instructions. This is the highest-cost item in the sweep: the failure mode is not that the guard is unknown, it is that the file argues both ways and the wrong half is phrased as a ruling. Struck, with a pointer to the binding section. T-103 was checked and is clean.
2. **[T-102](T-102-education-resource.md) carried the same bullet unstruck in its body** while its frontmatter had marked it `SUPERSEDED` since the code review. Lower stakes — the task is `done` — but the strike-don't-delete convention only works if the strike reaches the text a reader actually reads.
3. **[T-019](T-019-ci-host-on-demand.md)'s `remaining:` block asserted the opposite of this board's own record.** It said *"No PUSH has ever reached the doorbell… the NEXT push is the proof — T-102 supplies it for free"*, and the proof then arrived (T-106's push, 08:11:58Z → StartInstances → PR-4 build at 08:12:45Z; builds #2/#3 green in ~97s) and was written into §"T-019's last criterion is MET" **above** and never back into the task. A note that names its own future proof has to be revisited when that proof lands. Corrected; the billing-week criterion is the only one genuinely still open (~6 days of elapsed time, not work).
4. **T-019's board line still read *"awaiting one real push — see sweep 2026-08-20"*** — pointing at a sweep superseded by a later section of this same file. Now `done (**all criteria met bar the billing week**)`.
5. **[T-025](T-025-verify-requests-come-from-our-cloudfront.md)'s H1 was framed against a premise that had already shipped.** It priced [T-106](T-106-restrict-openapi-and-actuator-exposure.md) as a *"cheaper alternative worth pricing at H1"* — but T-106 is `done` and merged, so the leak that motivated T-025 is closed and the cheap half is not an option to weigh. **H1 now decides a genuinely narrower question**, written into the file: is the residual *bypass class* worth a shared secret today, given [T-014](T-014-deploy-bff-to-aws.md) is about to put a second port behind the same weak proof? Left `todo` — this is a reframing, not a decision.
6. **The M2 parallelization note still described T-102 as *"reached H1 and stopped, no code was written"***, and the deployment-gap section still recommended doing T-022 before T-014 as pending work. Both landed. ~~Wave 1 is now **T-103, T-104, T-151**.~~ **Corrected again 2026-08-22: wave 1 is T-104 and T-151** — T-103 merged the next day and this sentence went stale in under 24 hours, for the second time in the same paragraph.**

**Housekeeping:** [README.md](README.md)'s infra range read `T-001…T-024`; it runs to T-026, and those two are among the more actionable items on the board. The stale-branch problem was **repo-wide, not one repo**: 25 local branches across all eight siblings, plus ~25 more on `origin`. Merge status was taken from **GitHub, not from `git`** — `git branch --merged` reports nothing here because every PR is squash-merged, and `git merge-tree` over-reports because `master` has since edited the same files; both would have been read as "unmerged work" by anyone doing this by eye. `gh pr list --state all` settles it: **every branch in every repo maps to a MERGED PR — ~~47 PRs~~, zero open, zero closed-unmerged.** The 25 local branches are deleted, each checked against that list by name first. ~~**The `origin` copies are NOT yet deleted** — that push was blocked by this machine's permission policy and is left for the human, deliberately not worked around.~~ Same false "work in flight" signal the previous sweep removed stale worktrees to kill.

  **Corrected within the hour, and the correction is the point.** Two of the three factual claims above were wrong before the ink dried — in a paragraph belonging to a sweep *about* claims that go stale unread:

  - **The count was wrong.** "47 PRs" counted the meta repo's PRs, not the product repos' — the repos the sentence is about. Verified figures: **51 PRs across the eight product repos, 47 in the meta repo, 98 in the workspace, and all 98 merged** — zero open, zero closed-unmerged, workspace-wide.
  - **The scope was wrong.** The sweep audited the eight *sibling* repos and silently skipped the meta repo it was written in, which held **8 stale local branches of its own**. Total local: **33, not 25.**
  - **The `origin` claim expired.** The push was authorized explicitly and the branches are gone: **31 remote branches deleted** (2 meta + 29 product), verified against `GET /repos/:owner/:repo/branches` rather than local tracking refs, which lie after a delete elsewhere. **All nine repos now hold `master` and nothing else**, local and remote.

  Every deletion remains recoverable — each branch had a merged PR, and GitHub keeps a *Restore branch* button on it.

**Left alone deliberately.** Every `done` task on this board has its acceptance checkboxes **unticked** — T-001, T-009, T-018, T-019, T-022, T-102, T-106, T-107, all of them. That is consistent board-wide, so it is convention rather than drift and this sweep did not "fix" it. It is worth naming once, because it is *why* item 3 could happen: with the boxes decorative, the fact that a criterion is met can only live in prose, and prose is what this board keeps failing to propagate. Making them load-bearing would be a protocol change ([README.md](README.md)), not a board edit.

**The pattern, once more, now with a shorter fuse.** The previous sweep found facts that went stale over *days*. Items 1, 3 and 6 here went stale in **hours** — T-104's contradiction was authored the same day as the section that contradicts it. Velocity is what changed, not the failure mode: the board is now moving fast enough that a task file can be internally inconsistent before anyone reads it twice.

## T-103 merged — M2 is three of eleven, and the review found the acceptance criterion wrong (2026-08-21)

Picked up **at implementation** per its `reset_note`, as T-102 was — the H1 checkpoint from 2026-08-04 was real and was used as written. Merged as `2e54394` ([cv-domain-service#7](https://github.com/erfeamor/cv-domain-service/pull/7)). The catalog/assignment split, the composite key, the upsert and the 409 all landed as specified.

**Three premises had moved since that H1 and were recorded in the checkpoint before a line was written** — T-024 turned DoR rulings 1/2/5/6 into contract text, T-107 added the guard, T-006 added ordering. A 16-day-old DoR is not uniformly current, and saying which parts aged is cheaper than letting the implementer infer it.

**The most valuable output of this task is not the resource. It is that T-103's own acceptance criterion was wrong**, and the implementation satisfied it *exactly* while carrying the defect the criterion existed to prevent:

> ~~The upsert read-then-write is inside a single `@Transactional` boundary.~~

A single transaction does **not** serialize insert-if-absent. Two concurrent PUTs on an unlinked pair both read empty, both insert, and because the id is pre-populated `save()` takes `merge()` — so the INSERT defers to commit **after the handler returns**, and the violation escapes as a **500** where the contract mandates 200. `/code-review` (high effort) found it by booting the full application context, which no test in that repo does, and by decompiling Hibernate 6.5.2 rather than arguing from plausibility. Struck and corrected on the task: *transaction present **and** the create branch recovers from a lost race*. **That test plan is the template T-104 inherits**, which is the whole reason this matters beyond one PR.

**The PO's prescribed fix was wrong and the developer said so with evidence.** "Catch around the save and re-read" cannot work: after a flush failure the session is unusable and the transaction is rollback-only, and with annotation-based `@Transactional` the exception is not catchable in the method at all. Proven with a throwaway probe, not asserted. The shipped fix runs each attempt through a `TransactionTemplate` and retries once in a fresh transaction. Recorded because the disagreement was resolved *before* H2 rather than discovered after it — which is what the gate is for.

**Proven under real concurrency, twice, independently.** Developer: 6 rounds × 10 parallel PUTs → 60/60 `200`, 54 recovered `Duplicate entry` violations, zero escapes. Stage-4 QA reproduced **exactly 54** rather than accepting the number, and stressed the catalog's concurrent POST to 8-way (the plan asked for 2) → one `201`, seven `409`s, no 500. ~90 requests, zero 500s anywhere.

**Two rulings ended up enforced structurally rather than by vigilance**, which is the durable form and worth copying: `SkillRepository` has **no `findByName` at all**, so a pre-check 409 would not compile; and `SkillControllerTest` declares **no `PersonRepository`**, so adding a person-check to the global catalog fails context startup (DoR 7).

**Filed from this run, not folded in:** [T-027](T-027-contract-ordering-note-sql-vs-jpql.md) (the contract's ordering note prescribes SQL for a JPQL context — **T-104 hits it next**) and [T-028](T-028-qa-env-generator-worktree-build-context.md) (below).

### The QA stack was building `master` — [T-028](T-028-qa-env-generator-worktree-build-context.md)

`docker-compose.dev.yml:50` builds from `./cv-domain-service`, the **main checkout**, while every dev-loop task runs on a **worktree**. The documented stage-4 bring-up therefore exercises code that does not contain the change. Worked around by hand for this run with a third compose file; filed because the workaround lives in a **gitignored** generated file that vanishes with the next cleanup.

T-103 was greenfield and got lucky: QA proved provenance by observing that `GET /api/v1/skills` answered at all, since that endpoint does not exist on `master`. **A modifying task has no such tell** — it would answer plausibly on every endpoint and QA would sign off on a binary without the change. [T-105](T-105-experience-ordering-retrofit.md) is exactly that shape. T-104, T-151 and T-105 are annotated in place.

### [T-026](T-026-first-build-after-cold-start-fails.md) reproduced a fourth time — and its own severity claim is now narrower

```
06:45:54  error    PR-7/1/   "This commit cannot be built"
06:47:42  success  PR-7/2/   "This commit looks good"
```

**Nobody retriggered it.** Pushing the branch and opening the PR fire two separate webhook deliveries, so build #2 ran on the warm box unattended. GitHub's status API keeps only the latest state per context, so **the PR renders green and the failure is invisible** unless someone reads the full status history. T-026's *"every developer's first push after an idle period gets a red X"* is therefore too strong for the normal push-then-PR workflow — and unchanged for a push to an existing branch, where the red stands and gets blamed on the code. Corrected in the task; the diagnostic signature is untouched.

A caution now written into T-026: **`gh pr checks` will report `pass` while a failed build sits in the history**, so anyone verifying the eventual fix through it will "confirm" a fix that never ran.

## T-028 merged — the QA stack now builds and mounts the tree under test (2026-08-21)

Merged as `74be2c8` ([#49](https://github.com/erfeamor/curriculum/pull/49)), five commits, `scripts/` only, **33 tests wired into `scripts/test-all.sh`**.

**The defect it closes, restated because the fix is easy to under-read:** `docker-compose.dev.yml` wires every repo from the **main checkout**, which sits on `master`, while every dev-loop task runs on a **worktree**. Stage-4 QA was therefore capable of exercising code that did not contain the change under test — and it **fails toward a false pass**: an additive task 404s loudly, but a *modifying* task answers plausibly on every endpoint while QA signs off on a binary without the change.

### The most important thing this task learned is that its own model was wrong

The first implementation handled `build:` contexts, which is what [T-028's DoR ruling 3](T-028-qa-env-generator-worktree-build-context.md) told it to handle. `/code-review` found that ruling **incomplete on a repo this task explicitly cross-links**: `flyway` bind-mounts `./cv-database/sql` and `grafana` bind-mounts `./cv-observability/grafana/provisioning`, neither is a build context, and neither was ever visible to the matcher.

So [T-151](T-151-dev-seeds-cv-sections.md) would have seeded from **master's SQL**, its non-idempotent seeds would have duplicated exactly as before, and the generator would have printed *"no service repointed: task repo 'cv-database' is not built by docker-compose.dev.yml"* — **which reads as "nothing to do here".** The identical silent false pass, surviving the fix, wearing reassuring output. Now proven closed end to end, with the mount source inspected live **and** the seeded row read back (`T-028-BIND-PROBE` vs master's `Terraform`).

### Three corrections that outlive the code

1. **This task's AC1 was wrong** — *"a bring-up whose service reports code only present on the branch"* encodes the **additive** tell that T-103 passed by luck, and contradicted the modifying-task criterion directly below it. Struck. **That is the third acceptance criterion in two days found wrong by the person implementing against it**, after T-103's `@Transactional` boundary and T-104's inherited *"flag, don't block"*. The specifications, not the implementations, are this board's weak link — and all three were caught only because the implementer was told the spec was open to challenge.
2. **A guard was believed to cover a case it did not.** `/code-review` offered `git rev-parse --show-toplevel` as closing `--worktree ~/work/curriculum/cv-domain-service`. It does not: the main product checkout **is** a valid work-tree root. Only the branch check catches it. Corrected in the record because an inherited belief that a guard covers a case it doesn't is exactly how T-107's cross-person write survived three weeks behind a green test.
3. **A stale handler, not a wrong one.** The `try/except` was correct when written and went stale when the function beside it grew a new failure mode — so a `WorktreeError` escaped as a raw traceback. Fixed by *widening* the block rather than adding a second handler, so a future raiser is covered by construction. QA found it at stage 4; none of the 32 tests reached that path.

### Two consequences the board now owns

**[Board hygiene is load-bearing.](T-103-skills-catalog-and-assignments.md)** `checkpoint.worktree` now makes a repoint **mandatory** — a closed task still declaring a path makes every later bring-up for it exit 1. That is deliberate (loud, overridable with `--no-worktree-check`), but **"clear `checkpoint.worktree` at close-out" is now a convention with a tool depending on it.** T-103's entry is cleared accordingly; do the same at every close-out.

**Mount provenance is permanently weaker than build-label provenance.** Build labels are an image property and survive teardown; a bind mount leaves no trace beyond `docker inspect .Mounts`, which exists **only while the stack is up** and cannot be reconstructed. QA's adopted rule: for any bind-mount-only task (`cv-database`, `cv-observability`), sign-off requires **both** the `.Mounts` capture **and** an independent behavioural check. The pairing is the proof. **[T-151](T-151-dev-seeds-cv-sections.md) is the first task this binds.**

### The check that proved the check

T-103 began exiting 0 where it had exited 1, immediately after the driver cleared its `checkpoint.worktree` — indistinguishable from the guard having silently broken. QA ran the identical invocation against a scratch copy of the **old** board file: exit 1, same message. Same code, same task, same missing worktree; only the board content differed. **The check works; the board changed.** Recorded because "the signal agrees with itself" is this task's whole subject, and the driver's own edit was the likeliest place for it to recur.
## T-152 and T-016 merged — the workspace is on MySQL 8.4, and an H1 ruling was voided by evidence (2026-08-22)

**Written 2026-08-22, after the fact.** Both tasks merged earlier today and neither got a close-out section — the board sync for each ([#51](https://github.com/erfeamor/curriculum/pull/51), [#53](https://github.com/erfeamor/curriculum/pull/53)) changed table rows only, so everything below lived exclusively in commit messages. Every other merged task on this board has a section; these two did not, which is the same propagation failure the sweeps keep finding, arriving this time as an *absence* rather than a contradiction.

T-152 merged as `5942881` ([cv-database#3](https://github.com/erfeamor/cv-database/pull/3)); T-016 as `ebb6649` ([#52](https://github.com/erfeamor/curriculum/pull/52)). Together they retire the last three `mysql:8.0` pins in the workspace — `grep -rn "mysql:8.0"` across all nine repos now returns nothing.

**The migration gate was the half that mattered.** `cv-database/Jenkinsfile:18` stood up a throwaway **8.0** to answer *"will these migrations apply?"* while production applied them on **8.4**. A green CI therefore said nothing about the engine actually receiving the DDL. T-152 was filed separately from T-016 rather than widening it, because a `Jenkinsfile` diff forces `security_review: true` under adapter §5 and a local compose bump does not.

**The bump is proven, not observed.** The data-layer review diffed the full `information_schema` across real 8.0.46 and 8.4.11 — columns, charsets, collations, every index including `person_skill`'s composite PK, `sql_mode`, seed counts — and got byte-identical output except `SELECT VERSION()`. `ddl-auto: validate` therefore cannot behave differently across the two.

**What this retroactively costs the board:** four stage-4 checkpoints claim QA against *"live MySQL 8.4"* ([T-102](T-102-education-resource.md), [T-103](T-103-skills-catalog-and-assignments.md)). `scripts/qa-env-override.py` takes `docker-compose.dev.yml` as its base and has no image handling, so those stacks were almost certainly **8.0 wearing an 8.4 label**. They are torn down and not reconstructible. Nothing is being re-litigated — the point of the pair of tasks is that every such claim from today forward is true by construction.

### An H1 ruling was voided by evidence — the entry worth reading

H1 ratified *"wipe (`down -v`) is the supported route; seeds regenerate via the Flyway callback, so it costs nothing."* Both halves were false, and the reasoning is the artefact:

- The ruling rested on QA's stage-0 advice, given while everyone still believed 8.4 would **refuse** an 8.0 datadir. **The asymmetry proved inverted hours later** — 8.0→8.4 upgrades in place and *preserves* the datadir; 8.4→8.0 aborts with `MY-014061` and is unrecoverable in place. Nobody re-derived the ruling when its premise died.
- *"It costs nothing"* was false independently: `cv-admin-react` writes real rows to that same database, and `down -v` also drops `cv-dev-grafana-data`, where UI-built dashboards live with no JSON in the repo.

Both reviewers found it independently. The docs now say **forward wipe is optional, backward required**. Raised at H2 and the correction confirmed by the human — voided by evidence, not overridden silently. Not a stale number and not a stale status this time: **a ratified decision whose premise died the same day it was ratified.**

### QA's dirty-volume check ran against real data for the first time

The only genuine 8.0-era volume on this machine is developer data untouched since 2026-07-19, and the first plain `up` would have consumed it irreversibly — so the driver revised the check to **clone** it rather than test on it. The pre-existing person row survived the in-place upgrade byte-identical, `created_at=2026-07-11 15:10:00` included. The original was left untouched.

### Two task specs falsified by reviewers forbidden from fixing them — board rule 3 working as designed

- **[T-023](T-023-meta-docs-stale-bff-smoke-path.md) could not satisfy its own DoD.** It makes a clean `grep -rn "3000/api/v1"` the definition of done and listed **three** files. There are **four**: `docker-compose.dev.yml:7` is a compose comment header, not prose. Note the shape — T-023 was *created* by a drift sweep, its count was *corrected* by a second sweep (two → three, *"the hedge is now a fact"*), and it was **still wrong**. A sweep that greps only `*.md` keeps re-confirming its own blind spot. Scope widened on the task; the board line now says four.
- **[T-029](T-029-code-review-cannot-see-worktrees.md)'s premise was disproved hours after filing.** Filed as *"`/code-review` returns nothing on a worktree"*. T-016 runs in the **meta repo on a branch, with no worktree at all**, and bare `/code-review` returned the same empty result there; `/code-review 52` then ran a full review (21 tool calls, four findings). The real behaviour: with no explicit target it reviews the **uncommitted working-tree diff**, which in every failing invocation was board markdown. *"No findings"* was correct — it answered a question nobody asked. Retitled; the surviving defect is that an empty result is indistinguishable from a clean one.

### Five tasks filed from this run, none of them previously introduced here

| ID | What it is | Why it is not folded into another task |
|---|---|---|
| [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md) | `cv-database`'s `Deploy` stage is gated on `main`, a branch that does not exist here, and its placeholder still targets RDS | A pipeline file with a live-if-inert logic error, not prose — so not [T-017](T-017-docs-drift-rds-to-selfhosted.md)'s. `depends_on: [T-152]` is **file-level**: both edit `Jenkinsfile`, adjacent lines |
| [T-154](T-154-jenkins-pipeline-timeout.md) | No `timeout {}` on the pipeline | Latent, not live — but a hung build defeats [T-019](T-019-ci-host-on-demand.md)'s reaper and holds the **only** CI host up at ~$17.24/month. A cost argument, not a correctness one |
| [T-155](T-155-flyway-version-supports-mysql-84.md) | Flyway 10 does not claim MySQL 8.4 support and **already runs against 8.4 in production** | T-152 made it *visible*; it did not cause it. `cv-infra/templates/domain-service-user-data.sh:181` has run `flyway/flyway:10` against `mysql:8.4` on every instance replacement since MySQL left RDS. Cross-repo (four pins, three repos) — decompose at stage 0 |
| [T-029](T-029-code-review-cannot-see-worktrees.md) | `/code-review` silently reviews the wrong thing without an explicit target | See above — filed this morning, premise corrected the same afternoon |
| [T-030](T-030-pr3-build1-success-then-error.md) | A build posted `success` and then `error` **one second later** | **Attribution to [T-026](T-026-first-build-after-cold-start-fails.md) was withdrawn within the hour** after stage-4 QA challenged it. T-026's signature (`No build record …` plus an empty stage) was never obtained here, and all four confirmed T-026 occurrences *fail outright* rather than succeed and self-invalidate. Padding T-026's occurrence count would corrode the evidence base for *"reproducible on demand"* |

### T-152 merged with one acceptance criterion explicitly unverified

The CI-console version proof — Flyway's connection banner from the Jenkins PR-3 build — **was never obtained**: the console is authenticated and the credential path was declined by this machine's policy. Named in the PR at the human's H2 ruling rather than ticked, and carried in the task's `outstanding:` field. The same fetch also settles [T-030](T-030-pr3-build1-success-then-error.md), so one Jenkins login closes both.

That makes **three `done` tasks holding an unmet acceptance criterion** — T-019 (billing-week rate check), T-022 (admin UI loading with a real Cognito JWT), T-152 (the console banner). All three are honestly recorded in their files and **none is visible from the board table**, because this board's acceptance checkboxes are decorative by convention. That is the mechanism, named once more: with the boxes unticked board-wide, "met" and "unmet" can only live in prose, and prose is what keeps failing to propagate.

### The meta repo has no CI

No `.github/workflows` at all, so the engine's stage-3 *"authoritative gate"* **does not exist** for T-016 or for any other meta-repo task — [T-003](T-003-ci-docs-reflect-jenkins.md), [T-012](T-012-aws-endgame-decision.md), [T-015](T-015-docs-reflect-deployed-bff.md), [T-017](T-017-docs-drift-rds-to-selfhosted.md), [T-023](T-023-meta-docs-stale-bff-smoke-path.md), [T-027](T-027-contract-ordering-note-sql-vs-jpql.md), [T-029](T-029-code-review-cannot-see-worktrees.md). A1 and QA carry the entire weight there. Left unfiled per the human's H2 choice; recorded so the next meta-repo task knows what it is not getting.

## Board consistency sweep — 2026-08-22

A fourth sweep, run against all 52 task files, the frontmatter, `README.md`, and the live filesystem. **No status changed, no scope changed, no product code was touched.**

**Structural state is clean and was verified first:** 52 task files ↔ 52 board rows, no orphans in either direction, every file's `status:` matches its board line, no `todo` holds an owner, and no `depends_on` names a task that does not exist.

**What was wrong:**

1. **The wave-1 note still sent readers at [T-103](T-103-skills-catalog-and-assignments.md)**, which merged 2026-08-21 (`2e54394`) — in the note whose entire job is telling people what to claim, and in the sweep item directly above that corrected the *same sentence* one day earlier. Wave 1 is **T-104 and T-151**. Corrected in both places.
2. **T-152 and T-016 had no close-out section** — see above. Written.
3. **[README.md](README.md) said infra runs `T-001…T-028`.** It runs to T-030, and T-152–T-155 are boarded in that table too. **Third recurrence**: the 2026-08-20 sweep fixed this identical line from `T-001…T-024`. A hand-maintained range in prose is a fact with an expiry date; it now says "T-001 upward" and names no ceiling.
4. **[README.md](README.md) pointed at "the sweep note at its foot".** The foot of this file is a task close-out; the sweeps are mid-file and there are now four of them. Re-pointed at the section list rather than at a position.
5. **[T-101](T-101-experience-resource.md) and [T-102](T-102-education-resource.md) never had `checkpoint.worktree` cleared.** [T-028](T-028-qa-env-generator-worktree-build-context.md) made that convention load-bearing on 2026-08-21 and it was applied to T-103 and T-152 — but not retroactively. `cvdl-worktrees/` is empty, so `scripts/qa-env-override.py` refuses on both: *"Refusing: this stack would exercise the MAIN CHECKOUT (master)"*. Verified by running it, then cleared. This is exactly the case T-028 wrote down (*"a closed task still declaring a path makes every later bring-up for it exit 1"*) and it was sitting on two closed tasks the same day the tool shipped.
6. **[T-017](T-017-docs-drift-rds-to-selfhosted.md)'s title asserted work its own body says is largely done.** *"The repo still says RDS in five places"* — its 2026-08-22 re-scope check found all five surviving mentions are contrastive or historical and **explicitly permitted by its own AC1**, and `diagrams/architecture.mmd:15` reads `MySQL` and never said RDS. Retitled to what is actually left.

7. **Duplicate frontmatter keys were silently shadowing the values next to them — including one clearing that had already been done.** Found by *verifying* item 5 rather than by reading: `scripts/qa-env-override.py` still refused on [T-152](T-152-mysql-84-parity-cv-database.md), whose close-out had explicitly cleared `checkpoint.worktree` that morning. It carried **three** `worktree:` keys in one mapping (cleared · the stage-1 path · `pending` from stage 0) and a **second, empty `pr:`**. YAML takes the **last** duplicate, so the clearing was inert, the merged PR URL was shadowed by a blank, and the file read as correct to anyone looking at the line the close-out edited. Duplicates demoted to non-key names, originals kept. A sweep of all 52 files for the same shape found one more: [T-202](T-202-bff-public-routing-and-auth.md) had a second `security_review:` holding `done` — **a third vocabulary** for the key the 2026-08-17 sweep normalized from `required`/`true` down to one, and last, so it won. Renamed. (T-002 and T-103's apparent duplicates are sequence items in different rounds — checked, not touched.)

**The generator is now the check for item 5, and it passes.** `python3 scripts/qa-env-override.py --task <id>` exits 0 on every closed task that previously refused — T-101, T-102, T-103, T-152, T-016. This is the first sweep item on this board that has an executable test instead of a re-read, which is the direction the *"decorative checkboxes"* problem needs to move in.

**Left alone deliberately.** [T-104](T-104-project-resource.md) declares a `checkpoint.worktree` path that does not exist on disk, but it is **unclaimed** — the dev-loop recreates the worktree at stage 1, so the declaration is a pre-claim convention, not close-out drift. Item 5's rule applies at close-out, not before it.
## T-104 merged — M2's domain model is complete, and the sixth spec falsified in five days (2026-08-22)

Merged as `7677fee` ([cv-domain-service#8](https://github.com/erfeamor/cv-domain-service/pull/8)). Picked up **at implementation** per its `reset_note`, as T-102 and T-103 were — the H1 checkpoint from 2026-08-04 was real and was used as written.

**All four API resources are now done.** [T-201](T-201-bff-cv-aggregate.md) and [T-301](T-301-admin-cv-sections-crud.md) are unblocked; wave 2 is open. Wave 1 is [T-151](T-151-dev-seeds-cv-sections.md) alone. **M2 is four of eleven.**

**Three premises had moved since that H1 and were recorded before a line was written**, exactly as T-103 did — T-027 (below), T-028 landing (so the "hand-build a compose override" note was superseded), and MySQL 8.4 becoming real. A 18-day-old DoR is not uniformly current, and saying which parts aged is cheaper than letting the implementer infer it. This is now three tasks in a row where that step paid.

### [T-027](T-027-contract-ordering-note-sql-vs-jpql.md) hit exactly where this board said it would

The board has said since 2026-08-21 that *"T-104 hits it next"*. It did. `docs/api-contract.md:41` mandates an `@Query` for this collection while :39 prescribes `ORDER BY start_date IS NULL, start_date DESC, id ASC` — SQL, which does not parse in the JPQL context the same document requires. Shipped with the portable spelling T-103 proved:

```
ORDER BY CASE WHEN p.startDate IS NULL THEN 1 ELSE 0 END, p.startDate DESC, p.id ASC
```

No `nativeQuery` — staying in JPQL means a column rename still fails at **startup** rather than at runtime. **T-027 remains open and is now owed by two resources rather than one**; it is docs-only and trivial.

**The ordering was proven against real MySQL 8.4, not H2**, and that distinction is the point of stage 4: the unit tests only ever see H2, and the two engines can disagree on NULL sort order. QA inserted rows in an order deliberately mismatching the expected output — `2024-01-01`(id6), undated(id7), `2025-06-01`(id8), `2025-06-01`(id9), `2026-01-01`(id10) — and `GET` returned **[10, 8, 9, 6, 7]**: `startDate` DESC, undated **last**, `id` ASC on the shared-date tiebreak.

### The sixth acceptance criterion falsified by the person implementing against it

`/code-review` (high effort) and the developer **independently** found that `repoUrl` carried no `@Size`. V1 declares `repo_url VARCHAR(255)`; unbounded, a 260-character value passes bean validation, reaches MySQL strict mode as error **1406**, and surfaces as a **500 where contract design rule 4 requires a 400**.

T-104's AC says *"no validation annotation on any other field"*. **PO ruling: apply it anyway, because the AC's wording is over-broad and not the ratified part.** DoR ruling 5 is the ratified text and its reasoning is about **format** validation (`@URL`/`@Pattern`) silently narrowing the contract — which a length bound mirroring the column does not do. Two supports, both verified rather than asserted: `docs/api-contract.md:10` design rule 4, and the sibling convention, where `Education.fieldOfStudy` and `Skill.category` are **both optional and both carry `@Size`**. Leaving `repoUrl` bare made Project the odd one out. **C15 is untouched — `repoUrl: "not-a-url"` still returns 201**, so DoR 5's actual rule is preserved.

**That is six in five days** — after T-103's `@Transactional` boundary, T-104's own inherited *"flag, don't block"*, T-028's AC1, T-152's `docker exec` on a `--rm` container, and T-023's file count. The board has already named specifications as its weak link. The pattern in all six is identical: **each was caught only because the implementer was told the spec was open to challenge.** The developer here flagged the consequence and complied literally rather than quietly deviating, which is what made the ruling possible at all.

### The T-107 guard, closed by construction this time

Confirmed **red before** the guard went in (`Status expected:<400> but was:<201>`), then — going further than asked — the assertion was flipped to `isCreated()` + `$.id == 999` and **passed**, demonstrating that the unguarded POST really does return 201 carrying the victim's id. The `save()` stub echoes its argument back the way a real repository would, *deliberately*, so the assertion cannot be satisfied by the mock the way T-101's `clientSuppliedIdInThePostBodyIsIgnored` was for three weeks.

Stage-4 QA then proved the live half by exploit, not by argument: `POST /people/2/projects {"id":5,...}` where row 5 belongs to person 3 → **400**, row 5 read back **from MySQL** unchanged, `GET /people/3/projects` still returning it, no stray row under person 2.

### Filed, not folded in: [T-108](T-108-untransacted-update-read-modify-write.md)

`/code-review`'s second finding: `update()` is an untransacted read-modify-write. With `open-in-view: false` and no `@Transactional`, a concurrently deleted row makes the trailing `merge()` fall through to `persist` and **re-INSERT it under a new id** — the client gets a 200 whose `id` is not the one it PUT, and a deleted row reappears. No `@Version`, so two concurrent PUTs also lose an update silently.

**PO ruling: file, do not fix here.** `EducationController.update` and `ExperienceController.update` carry the shape **verbatim** and are already on `master` — verified directly. Fixing only Project would leave three sibling resources with two concurrency behaviours, which is the same argument [T-107](T-107-post-id-cross-person-write.md) used to decline the structurally better `@JsonProperty(access = READ_ONLY)`.

**The contrast with T-107 is written into T-108 deliberately, because the two rulings look inconsistent and are not.** T-107's defect was fixed *inside* T-102 rather than deferred, because shipping new code carrying a live cross-person write would have been following process off a cliff. This one is neither an authorization hole nor new — it ships identically on `master` today, so deferring changes nothing about the exposure, where deferring T-107 would have added a fourth instance of a live one.

### First "verified against MySQL 8.4" that is true by construction

`SELECT VERSION()` → **8.4.11**, read off the running container rather than the compose tag. [T-152](T-152-mysql-84-parity-cv-database.md) and [T-016](T-016-dev-prod-mysql-parity.md) landed that parity hours earlier, so this is the first stage-4 run on this board whose engine claim rests on something other than assumption — the four earlier claims (T-102, T-103) were most likely 8.0 wearing an 8.4 label.

**And [T-028](T-028-qa-env-generator-worktree-build-context.md) did its job on its first real outing.** The generator resolved the worktree and repointed the `domain-service` build context itself; QA confirmed provenance off the **image labels** (`com.cvproject.dev-loop.commit=81f4bef`, `dirty=false`) rather than inferring it, corroborated by the additive tell (`GET /people/1/projects` → `200 []` where master 404s). T-103 got that provenance by luck and a hand-built third compose file; this task got it from tooling.

### [T-026](T-026-first-build-after-cold-start-fails.md) reproduced a fifth time — and this one counts

`PR-8/1` failed **42 seconds after the doorbell started the box** (`pending → error`, no intervening success), and `PR-8/2` went green unattended on the warm box at 15:36:40Z. It matches on both axes that separate this task from [T-030](T-030-pr3-build1-success-then-error.md): it fails *outright* rather than succeeding and self-invalidating, and it fires on a cold start.

**The console signature is still unobtained** and is not being claimed — Jenkins needs credentials this machine's policy declines. Recorded as *"matches the cold-start-fails / warm-succeeds pattern, console signature unobtained"*, because stating it the strong way is precisely the error T-030 exists to correct, and repeating it one day later would be worse than the original.

**One Jenkins login now closes three open items**: this occurrence, [T-030](T-030-pr3-build1-success-then-error.md)'s anomaly, and [T-152](T-152-mysql-84-parity-cv-database.md)'s outstanding CI-console criterion.

**The `gh pr checks` caution, demonstrated live.** PR-8 renders green and `gh pr checks 8` reports a pass while the `error` sits in the history behind it — GitHub keeps only the latest state per context. Anyone verifying the eventual T-026 fix that way will confirm a fix that never ran.
## T-151 merged — wave 1 is complete, and T-028's rule got its first real test (2026-08-22)

Merged as `865784f` ([cv-database#4](https://github.com/erfeamor/cv-database/pull/4)). One file, append-only, +183 lines: `sql/dev-seeds/afterMigrate__seed_dev.sql`. No versioned migration, no edit to `V1__init_schema.sql`.

**Wave 1 is now complete** — T-101, T-102, T-103, T-104 and T-151 are all `done`. The local stack finally renders a *complete* demo CV; until today the section endpoints and both public front ends came up empty.

### The task's own guard was broken, and it was caught at H1 rather than in production

T-151 correctly diagnosed that `INSERT IGNORE` cannot dedupe `experience`, `education` or `project` (verified: each has **only** an autoincrement PK and an FK — no unique constraint), and correctly prescribed `INSERT … SELECT … WHERE NOT EXISTS`. Then it specified `name + start_date` as the natural key for `project` — and **`project.start_date` is nullable**, the only nullable date of the three tables. In MySQL `pr.start_date = '…'` is never true against a stored NULL, so for an undated project the guard passes and **the row is re-inserted on every migrate**: exactly the duplicate-row bug the task exists to prevent, reproduced by the fix it prescribed.

**Being right about the mechanism is not the same as being right about the instance.** That is the seventh specification defect this board has found in five days, and the first caught at H1 — before implementation rather than during it.

Fixed with the null-safe operator `<=>` on the three project guards; `experience.start_date` and `education.start_date` are `NOT NULL` and keep plain `=`, since null-safe handling there would be dead code implying a nullability the schema does not have.

**Confirmed red first**, and the isolation is what makes it evidence rather than assertion — with `<=>` swapped back to `=` on a fresh volume, the project count went 3 → 4 → 5 across three migrates while **only the undated row duplicated**; the two dated projects and both `NOT NULL` tables held. That pins the cause to the NULL comparison rather than to the guard's shape.

### Both sharp edges of the ordering contract are now exercised locally

H1 ratified seeding **one undated project** deliberately, to exercise the *"undated last"* rule [T-104](T-104-project-resource.md) had shipped hours earlier. `/code-review` then found the matching hole: every seeded row had a **distinct `start_date`**, so the contract's `id ASC` tiebreaker — *"mandatory, not decorative"* per § Ordering — was never exercised, and a regression dropping it would still render a correct-looking CV locally. A fourth project now shares a date:

```
id 1  Curriculum Interactivo  2024-02-05
id 2  Ledger CLI              2021-11-08   <-- tie
id 3  Schema Diff Reporter    2021-11-08   <-- tie
id 4  Dotfiles                NULL         <-- undated, last
```

QA verified the order **through the domain API**, not by re-running the `ORDER BY` in SQL: `GET /api/v1/people/1/projects` returned `1 → 2 → 3 → 4`. The tied pair resolving id 2 before id 3 is what distinguishes a real `id ASC` tiebreak from insertion order that happens to look right.

### [T-028](T-028-qa-env-generator-worktree-build-context.md)'s bind-mount rule, first real outing

T-028 named this task as the first its mount-provenance rule binds, and **both halves were obtained**:

- **`.Mounts` captured while the stack was up** — `cvdl_t-151-flyway-1` bound `…/cvdl-worktrees/T-151/sql` → `/flyway/sql`: the worktree, not the main checkout.
- **Paired behavioural check** — `experience=3, education=2, project=4` on the meta stack, counts that are *impossible* unless the worktree's SQL executed, since master's seed file has no rows in those tables at all.

The pairing is the sign-off because **a bind mount leaves no trace after teardown**, unlike a build label. Before T-028 landed, this exact task would have seeded from **master's SQL** while the generator printed *"no service repointed: task repo 'cv-database' is not built by docker-compose.dev.yml"* — output that reads as *nothing to do here*. The rule was written for this shape and it caught it.

### Documented, not fixed — and the documentation was verified

`/code-review` reproduced a silent break of this task's own invariant: rename a seeded row's **key** column through `cv-admin-react` and re-migrate, and the guard misses, the row is resurrected, and there are **two rows with `end_date NULL`** — two "current jobs" on the public CV, while migrate exits 0. The converse also holds: editing a **non-key** field *in the seed file* applies on a fresh volume and silently no-ops on every existing one.

Neither is fixable without a unique constraint, which is a schema change and explicitly out of this task's scope. Both are documented in the header block with `reset.sh` named as the remedy — and **QA reproduced both and confirmed the remedy**, so the comments describe observed behaviour rather than predicted behaviour. A comment that is subtly wrong is worse than none, in a file whose entire theme is that the absence of an error is not evidence of success.

### The gate that does not exist, stated once more

`Jenkinsfile:25` pins `FLYWAY_LOCATIONS=filesystem:/flyway/sql/migrations` and `dev-seeds` is **not** on that path — verified, not assumed. A syntax error, an FK violation, or the duplicate bug above would all pass CI green with no output. **Green CI is required by the DoD and proves nothing about this file.** The triple-migrate verification is the only check that will ever catch a seed regression, here or on any future edit — which is why it was run three times independently: by the developer, by the driver, and by `/code-review` in its own container.

**A record correction:** the *"two pre-existing 1062 warnings"* figure carried in this task's brief and in both agent reports is wrong — on MySQL 8.4 it is **eleven** (1 `person` + 5 `skill` + 5 `person_skill`). Same expected `INSERT IGNORE` noise, no defect, and the figure never reached the committed file. Kept because *"what does clean noise look like"* is precisely the judgement this file's silent-failure mode depends on, and a wrong baseline for it is how a real error gets skimmed past.
