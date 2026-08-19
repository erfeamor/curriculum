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
| [T-501](T-501-e2e-cv-milestone.md) | End-to-end verification + roadmap close-out | cv-project | todo | | all above **+ T-105, T-014, T-403, T-404** | |

### Parallelization notes (read before claiming)

- **Wave 1 (5 agents in parallel):** T-101, T-102, T-103, T-104, T-151 — fully independent; the four API tasks touch disjoint packages, so PRs won't conflict except trivially.
  - **Status as of 2026-08-09:** T-101 is **merged** (PR #3, `09282ed` — CI green, stage-4 QA passed). T-102/T-103/T-104 reached **H1 and stopped** — refinement and their DoR/test plans are complete and ratified, but no code was written; their claims were reset from a stale `in_progress` so they can be picked up. **Start them at implementation, not refinement.** T-151 never started.
- **Wave 2:** T-201 and T-301 — both may *start* against the contract (mocked upstreams) during wave 1; their final verification needs wave 1 merged.
- **Wave 3:** T-401 and T-402 after T-201 (different repos — run them in parallel); T-501 strictly last.
- T-103 is the highest-risk API task (composite key, upsert, 409) — assign it to the strongest agent or start it first.
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
| [T-016](T-016-dev-prod-mysql-parity.md) | Dev/prod parity: bump the local MySQL to 8.4 | cv-project (meta) | todo | | — | |
| [T-017](T-017-docs-drift-rds-to-selfhosted.md) | Docs drift: the repo still says RDS in five places | cv-project (meta) + cv-database | todo | | — | |
| [T-018](T-018-mysql-on-dedicated-ebs-volume.md) | MySQL on a dedicated EBS volume, surviving instance replacement | cv-infra | done (applied + survival proven) | infrastructure-engineer | — | [#16](https://github.com/erfeamor/cv-infra/pull/16) |
| [T-021](T-021-mysql-password-rotation-persistent-datadir.md) | Rotating `db_password` breaks silently now the datadir persists | cv-infra | todo | | T-018 | |
| [T-022](T-022-domain-service-origin-bypasses-cloudfront.md) | Domain service reachable on :8080 bypassing CloudFront; leaks OpenAPI spec | cv-infra | todo | | — | |
| [T-019](T-019-ci-host-on-demand.md) | Stop paying for an idle CI host: start on demand, stop when quiet | cv-infra | in_review (**applied + stage-4 verified**; one manual step left — re-point the GitHub webhooks) | infrastructure-engineer | — | [#17](https://github.com/erfeamor/cv-infra/pull/17) |
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
| [T-023](T-023-meta-docs-stale-bff-smoke-path.md) | The documented E2E smoke command curls a path the BFF no longer serves | cv-project (meta) | todo | | — | |
| [T-024](T-024-contract-skill-assignment-put-shape.md) | Contract: split the skill-assignment PUT's request body from its response | cv-project (meta) | todo | | — | |

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

**[T-022](T-022-domain-service-origin-bypasses-cloudfront.md) should be done before T-014, and that was invisible on this board until 2026-08-17.** Both tasks argue it — T-014's ruling 1 and T-022's dev-loop notes — but neither the chain table nor its prose mentioned T-022, and T-014 is the task everyone is told to claim next. It is **not** a `depends_on` edge in either direction (deliberately: neither blocks the other). The argument is that T-022 applies the *same* managed-prefix-list fix to port 8080 that T-014's ruling 1 mandates for port 3000, so doing it first means T-014 follows an established pattern instead of inventing one, and the reviewer sees one consistent approach across both ports. T-022 is also cheap (in-place SG change, `risk: normal`, easily reverted) and closes a live unauthenticated `/v3/api-docs` disclosure that grows automatically with every M2 resource that lands.

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
