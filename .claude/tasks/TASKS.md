# Board

Protocol: [README.md](README.md) · Contract: [docs/api-contract.md](../../docs/api-contract.md) · History: [HISTORY.md](HISTORY.md)

One line per task; the task file holds the detail. Merge narratives and superseded reasoning live in HISTORY.md — when a note below stops being current, move it there rather than striking it in place. Done rows are folded under each table.

## Now / Next / Later — refreshed 2026-10-01 (T-014 merged: the BFF is live; its public routes wait on T-043)

The order to claim in. It is **advice, refreshed at every board-sync**. `depends_on` is authoritative wherever the two disagree, and a lane entry that has gone stale is a board-sync finding, not a rule.

**Sizing:** plan by **plan windows and the human's `/usage` figure**, not by the budget probe — it doesn't count subagent spend, which dominates infra work (sessions 1–5, 2026-09-28 → 10-01, measured it; close-outs in [HISTORY.md](HISTORY.md)). High-risk infra has run about 2× its estimates. Host-up work follows `cv-infra/docs/runbooks/` (`drone.md`, `ci-host-replace.md`); pause the reaper with the **`CIKeepAlive` tag**, never by disabling the rule.

**Now**
- **[T-211](T-211-bff-service-token-provider.md) → [T-043](T-043-bff-service-token-to-domain.md)** (~1–2 windows; H1 decided 2026-10-01: 24 h token, ~$0.07/month): the BFF gets a Cognito service token so its public routes stop answering 401/502. **[T-014](T-014-deploy-bff-to-aws.md) is done** (cv-infra#32, 2026-10-01): the BFF is live behind `/bff/*`, Flyway is 13.7.0 in production, the domain service runs current master, and the admin's section editing works again. **The migration freeze is lifted.**
- **[T-113](T-113-optimistic-locking-lost-update.md)** in parallel with T-043 (cv-domain-service; it needed only T-014, which lifted the migration freeze): `@Version`/409, contract PR first.
- **[T-040](T-040-jenkins-github-pat-expiry.md)** as soon as the human has the token (**due 2026-10-30**; a fraction of a window). Independent.

**Next — after T-043** (~1–2 windows)
- In parallel, two repos: [T-403](T-403-public-vanilla-deploy.md) (vanilla deploy), [T-404](T-404-public-react-point-at-deployed-bff.md) (Vercel `BFF_URL`).
- [T-035](T-035-app-host-to-graviton.md) as its own apply: app host to Graviton, **plus the app host's IMDSv2/hop-limit hardening moved from T-005** (it replaces the host and re-verifies every container anyway). Its target size follows T-014's memory numbers.

**Then** (~1–2 windows)
- [T-112](T-112-domain-service-ci-ecr-deploy.md) + [T-203](T-203-bff-ci-deploy-stage.md) + [T-005](T-005-ci-secret-blast-radius.md)'s remainder: **one H1** for the credential model, with T-005 as its input. Multi-arch images are decided at their H1 (T-014 declined them for its one-off builds; T-035 does the arm64 rebuild).
- → **[T-501](T-501-e2e-cv-milestone.md)** (~1 window), which **absorbed [T-015](T-015-docs-reflect-deployed-bff.md)** on 2026-10-01: milestone M2 done.

**Anytime**
- [T-038](T-038-board-check-link-check-live-use-re-review.md) (check 8's live-use re-review), from **2026-10-12**. Small; slot it into any window.

**Human**
- **By 2026-10-30:** create a replacement CI GitHub token for Jenkins ([T-040](T-040-jenkins-github-pat-expiry.md)). The current one expires **2026-11-06**.
- Paid plan since 2026-09-29; all five credit activities done (grant $200). **$120.75** left on 2026-10-01, ~mid-March 2027 at the measured rate (credits expire 2027-07-12). Charges past them bill the card; the budget alarms are the guard.

~~**Standing invariant:** no new migration in cv-database until T-014 moves production to Flyway 13.7.0.~~ **Lifted 2026-10-01:** production runs Flyway 13.7.0 (T-014).

**Later / conditional**
- [T-021](T-021-mysql-password-rotation-persistent-datadir.md): T-004 decided **not** to rotate `db_password`, so this has no trigger today. Claim it **before** anyone changes `db_password` for any reason.

## M2 — Complete the domain model end-to-end

Tasks in [T-501](T-501-e2e-cv-milestone.md)'s transitive `depends_on` — **computed from the frontmatter on 2026-09-24**, not grouped by hand; the deployment chain has its own table below. Everything else in the product repos is in *Defects, hygiene & hardening*.

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-501](T-501-e2e-cv-milestone.md) | End-to-end verification + roadmap close-out | cv-project | todo | | T-101…T-105, T-151, T-201, T-301, T-401, T-402, T-014, T-403, T-404 (T-408, T-409 via T-401, T-402) | |

<details>
<summary>M2 — 15 done</summary>

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-101](T-101-experience-resource.md) | Experience resource in the domain API | cv-domain-service | done | backend-developer | — | [#3](https://github.com/erfeamor/cv-domain-service/pull/3) |
| [T-102](T-102-education-resource.md) | Education resource in the domain API | cv-domain-service | done | backend-developer | — | [#5](https://github.com/erfeamor/cv-domain-service/pull/5) |
| [T-103](T-103-skills-catalog-and-assignments.md) | Skill catalog + person-skill assignments | cv-domain-service | done | backend-developer | — | [#7](https://github.com/erfeamor/cv-domain-service/pull/7) |
| [T-104](T-104-project-resource.md) | Project resource in the domain API | cv-domain-service | done | backend-developer | — | [#8](https://github.com/erfeamor/cv-domain-service/pull/8) |
| [T-105](T-105-experience-ordering-retrofit.md) | Retrofit contract ordering onto the merged Experience resource | cv-domain-service | done | backend-developer | T-006 ✔ | [#9](https://github.com/erfeamor/cv-domain-service/pull/9) |
| [T-151](T-151-dev-seeds-cv-sections.md) | Dev seed data for CV sections | cv-database | done | backend-developer | — | [#4](https://github.com/erfeamor/cv-database/pull/4) |
| [T-201](T-201-bff-cv-aggregate.md) | BFF: aggregated public CV endpoint | cv-bff-node | done | fullstack-developer | T-101…T-104, T-006 | [#5](https://github.com/erfeamor/cv-bff-node/pull/5) |
| [T-209](T-209-contract-optional-field-null-semantics.md) | Contract: an optional field is a present key whose empty value is `null` (design rule 7) | cv-project (meta) | done | tech-product-owner | — | [#83](https://github.com/erfeamor/curriculum/pull/83) |
| [T-405](T-405-public-react-null-optionals.md) | Public site (React): optionals typed `null`, not absent or required | cv-public-react | done | fullstack-developer | T-209 ✔ | [#4](https://github.com/erfeamor/cv-public-react/pull/4) |
| [T-407](T-407-public-react-tocv-null-invariant.md) | Public site (React): `toCv` establishes the null-not-absent invariant its types assert | cv-public-react | done | fullstack-developer | T-405 ✔ | [#6](https://github.com/erfeamor/cv-public-react/pull/6) |
| [T-408](T-408-public-vanilla-bff-path-missing-prefix.md) | **Public site (vanilla): calls the BFF at `/api/v1`** — the landing page renders its error state today, and `main.js` has no test | cv-public-vanilla | done | fullstack-developer | — | [#3](https://github.com/erfeamor/cv-public-vanilla/pull/3) |
| [T-401](T-401-public-cv-sections.md) | Public site: render full CV | cv-public-vanilla | done | tech-product-owner | T-201 ✔, **T-408** | [#4](https://github.com/erfeamor/cv-public-vanilla/pull/4) |
| [T-409](T-409-public-react-adapter-validates-required-and-enum.md) | Public site (React): the adapter validates required fields, the `proficiency` enum, and absent-vs-null `endDate` | cv-public-react | done | tech-product-owner | T-407 | [#7](https://github.com/erfeamor/cv-public-react/pull/7) |
| [T-402](T-402-public-react-cv-sections.md) | Public site (React): render full CV sections | cv-public-react | done | tech-product-owner | T-201 ✔, T-405 ✔, T-409 ✔ | [#8](https://github.com/erfeamor/cv-public-react/pull/8) |
| [T-301](T-301-admin-cv-sections-crud.md) | Admin UI: CRUD for the four sections | cv-admin-react | done | tech-product-owner | T-101…T-104 | [#13](https://github.com/erfeamor/cv-admin-react/pull/13) |

</details>

### Before claiming

- **The domain waves are complete** — T-101…T-105 and T-151 merged; all four section collections are contract-compliant on ordering. The rendering tasks (T-301, T-401, T-402) are done too; **only the deployment chain below (T-014 → T-403/T-404) still gates [T-501](T-501-e2e-cv-milestone.md)**.
- **Read contract design rule 7's carve-outs before writing a consumer.** Requests are the opposite (`PUT` replaces, so an omitted optional in a *request* body IS the empty case), and `endDate` is not governed by rule 7 at all — always emitted, its `null` means "current" under rule 3.
- **Probe a guard, don't read it.** The T-205 → T-210 lineage caught several type-level guards passing for the wrong reason, each found only by making the defect and watching the check stay green. Narratives in HISTORY.md.
- **Concurrency lesson from T-103:** highest-risk tasks (composite key, upsert, 409) should start first so review convergence failures surface earliest.

### Repo context

- **cv-bff-node is now TypeScript** (strict, ts-jest/tsc). T-201's route and tests are `.ts`, type the aggregate payload, and `npm run typecheck` is a gate.
- **cv-admin-react is hexagonal TypeScript** (domain ← application ← composition → infrastructure). T-301 follows the repo CLAUDE.md's "adding a section resource" recipe.
- **cv-public-react** exists as a second public site (Next.js/ISR from the BFF). It renders all four CV sections (T-402, done); pointing it at the deployed BFF is T-404.
- **The database is self-hosted MySQL 8.4**, not RDS. Migrations verified compatible; production applies migrations only — dev-seeds stay dev-only. Backups (T-001) and dev/prod version parity (T-016, T-152) are done.

## Defects, hygiene & hardening — product repos (not on T-501's path)

Real defects, security fixes and CI debt in the product repos that **T-501 does not wait on** (no path to them through its `depends_on`). Until 2026-09-24 they sat in the M2 table, which made the milestone look larger than it is.

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-113](T-113-optimistic-locking-lost-update.md) | Two concurrent PUTs silently lose one write — no `@Version`, no 409 (T-108's declined half) | cv-domain-service | todo | | T-108, T-014 | |
| [T-112](T-112-domain-service-ci-ecr-deploy.md) | CI: push the image to ECR and roll the container on `master` (deploy is manual today). Needs a cv-infra apply: after T-014, one credential decision with T-203 | cv-domain-service | todo | | T-111 ✔ | |
| [T-116](T-116-domain-service-scope-enforcement.md) | The domain service accepts any pool token for any method — make the BFF's read-only service token GET-only (T-043 follow-up) | cv-domain-service | todo | | T-043 | |

<details>
<summary>Defects, hygiene & hardening — 15 done</summary>

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-111](T-111-domain-service-jenkins-pipeline-timeout.md) | Jenkinsfile hygiene: no `timeout {}` on the single shared executor; dead `main` Deploy gate + stale placeholder (**absorbs T-110**) | cv-domain-service | done | tech-product-owner | — | [#10](https://github.com/erfeamor/cv-domain-service/pull/10) |
| [T-106](T-106-restrict-openapi-and-actuator-exposure.md) | Stop serving the OpenAPI spec and Prometheus metrics anonymously | cv-domain-service | done | backend-developer | — | [#4](https://github.com/erfeamor/cv-domain-service/pull/4) |
| [T-107](T-107-post-id-cross-person-write.md) | **POST with a client-supplied id overwrites another person's row** (person, experience) | cv-domain-service | done | backend-developer | — | [#6](https://github.com/erfeamor/cv-domain-service/pull/6) |
| [T-110](T-110-domain-service-jenkins-deploy-dead-gate.md) | Jenkins `Deploy` stage gated on `main`; stale placeholder — **absorbed into T-111** | cv-domain-service | done | tech-product-owner | — | none |
| [T-205](T-205-bff-allowlist-section-normalizers.md) | BFF: the aggregate's section normalizers were denylists — now allowlists | cv-bff-node | done | fullstack-developer | T-201 ✔ | [#6](https://github.com/erfeamor/cv-bff-node/pull/6) |
| [T-206](T-206-person-id-guard-numeric-overflow.md) | The shared person-id guard accepted digit runs that overflow Java `Long` (502 where a 400 belongs) | cv-bff-node | done | fullstack-developer | T-201 ✔ | [#7](https://github.com/erfeamor/cv-bff-node/pull/7) |
| [T-207](T-207-public-types-derived-from-domain-interfaces.md) | BFF: `Public*` types transcribed from the contract, not `Omit<Domain*, …>` | cv-bff-node | done | fullstack-developer | T-205 ✔ | [#9](https://github.com/erfeamor/cv-bff-node/pull/9) |
| [T-208](T-208-error-handler-status-and-metrics-cardinality.md) | Error handler flattens **every** non-auth error to 500; unmatched paths mint **attacker-driven** Prometheus labels | cv-bff-node | done | fullstack-developer | — | [#11](https://github.com/erfeamor/cv-bff-node/pull/11) |
| [T-210](T-210-bff-domain-types-null-not-absent.md) | BFF: `Domain*` interfaces say `null`, not absent | cv-bff-node | done | fullstack-developer | T-209 ✔ | [#10](https://github.com/erfeamor/cv-bff-node/pull/10) |
| [T-406](T-406-public-react-bff-path-missing-prefix.md) | Public site (React): call the BFF at `/bff/api/v1`, not `/api/v1` | cv-public-react | done | fullstack-developer | — | [#5](https://github.com/erfeamor/cv-public-react/pull/5) |
| [T-108](T-108-untransacted-update-read-modify-write.md) | **PUT is an untransacted read-modify-write** — a concurrent DELETE re-INSERTs the row under a new id | cv-domain-service | done | tech-product-owner | — | [#11](https://github.com/erfeamor/cv-domain-service/pull/11) |
| [T-114](T-114-test-profile-open-in-view.md) | The test profile runs **open-in-view ON**, production OFF — it hid T-108's real failure mode once | cv-domain-service | done | tech-product-owner | — | [#12](https://github.com/erfeamor/cv-domain-service/pull/12) |
| [T-115](T-115-section-period-cross-field-validation.md) | The domain service accepts `endDate` earlier than `startDate` on a section | cv-domain-service | done | tech-product-owner | T-027 | [cv-domain-service#13](https://github.com/erfeamor/cv-domain-service/pull/13) |
| [T-302](T-302-admin-store-read-races.md) | Admin section/skills stores: rare load-vs-write interleavings show a wrong list, notice or error until reload | cv-admin-react | done | tech-product-owner | T-301 | [cv-admin-react#14](https://github.com/erfeamor/cv-admin-react/pull/14) |
| [T-109](T-109-ordering-tiebreak-unevidenced-siblings.md) | The `id ASC` tiebreaker is asserted by tests that **cannot go red** (every ordered collection but experience) | cv-domain-service | done | tech-product-owner | T-105 | |

</details>

## Infra & ops (outside M2)

[T-012](T-012-aws-endgame-decision.md) decided **A (go Paid, trimmed)** on 2026-09-24 and closed 2026-10-01 (Paid since 09-29, all credit activities done, $120.75 left), so the hardening and cost trims below are all worth doing. **cv-infra applies are strictly serial** — one root module, one state (in S3 with a DynamoDB lock since T-004, so a concurrent apply blocks rather than corrupts).

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-005](T-005-ci-secret-blast-radius.md) | CI secret blast radius — the remainder: the docker.sock/host-network IMDS gap, split parameter paths, narrow the app-host SSM read (CI-host IMDSv2 done in T-007; app host's moved to T-035) | cv-infra | todo | | T-002, T-007 | |
| [T-021](T-021-mysql-password-rotation-persistent-datadir.md) | Rotating `db_password` breaks silently now the datadir persists | cv-infra | todo | | T-018 | |
| [T-025](T-025-verify-requests-come-from-our-cloudfront.md) | The edge is not an authenticator: prove requests come from OUR distribution (cross-repo: split at stage 0 if implemented) | cv-infra + cv-domain-service | todo | | T-022, T-043 | |
| [T-035](T-035-app-host-to-graviton.md) | App host to Graviton (arm64 images first) **+ its IMDSv2 hardening (from T-005)** — −$1.75/mo, **after** T-014; size follows T-014's memory numbers | cv-infra | todo | | T-014 | |
| [T-038](T-038-board-check-link-check-live-use-re-review.md) | Re-review board-check's check 8 (link integrity) after two weeks of real edits — not before 2026-10-12 | cv-project (meta) | todo | | T-032 | |
| [T-040](T-040-jenkins-github-pat-expiry.md) | The CI GitHub token Jenkins uses expires 2026-11-06 — rotate it (**due 2026-10-30**) | cv-infra | todo | | — | |

<details>
<summary>Infra & ops — 37 done</summary>

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-001](T-001-selfhost-mysql-followups.md) | Backup: replace the managed backups lost when MySQL left RDS | cv-infra | done | infrastructure-engineer | — | [#15](https://github.com/erfeamor/cv-infra/pull/15) |
| [T-002](T-002-jenkins-on-drone-host.md) | Host Jenkins on the existing Drone CI instance | cv-infra | done | infrastructure-engineer | — | [#11](https://github.com/erfeamor/cv-infra/pull/11) |
| [T-003](T-003-ci-docs-reflect-jenkins.md) | Correct the CI documentation to match reality — **absorbed into T-023** | cv-project (meta) | done | tech-product-owner | T-002 | none |
| [T-006](T-006-contract-section-ordering.md) | Contract: define ordering for the CV section collections | cv-project (meta) | done | tech-product-owner | — | [#23](https://github.com/erfeamor/curriculum/pull/23) |
| [T-009](T-009-user-data-size-ceiling.md) | Get the provisioning script out of user_data before it hits the 16 KB wall | cv-infra | done | infrastructure-engineer | T-002 | [#18](https://github.com/erfeamor/cv-infra/pull/18) |
| [T-010](T-010-aws-credit-runway.md) | Track the AWS credit runway and free-plan cliff before it stops the demo | cv-project (meta) | done | tech-product-owner | — | none |
| [T-011](T-011-budget-credit-alarm.md) | Budget alarm that fires on credit burn, not on the invoice | cv-infra | done | infrastructure-engineer | — | [#13](https://github.com/erfeamor/cv-infra/pull/13) |
| [T-016](T-016-dev-prod-mysql-parity.md) | Dev/prod parity: bump the local MySQL to 8.4 | cv-project (meta) | done | infrastructure-engineer | T-152 ✔ | [#52](https://github.com/erfeamor/curriculum/pull/52) |
| [T-017](T-017-docs-drift-rds-to-selfhosted.md) | Docs drift: name MySQL 8.4 as the target engine in cv-database's docs — **absorbed into T-153** | cv-project (meta) + cv-database | done | tech-product-owner | — | none |
| [T-018](T-018-mysql-on-dedicated-ebs-volume.md) | MySQL on a dedicated EBS volume, surviving instance replacement | cv-infra | done | infrastructure-engineer | — | [#16](https://github.com/erfeamor/cv-infra/pull/16) |
| [T-019](T-019-ci-host-on-demand.md) | Stop paying for an idle CI host: start on demand, stop when quiet | cv-infra | done | infrastructure-engineer | — | [#17](https://github.com/erfeamor/cv-infra/pull/17) |
| [T-020](T-020-cost-model-correction.md) | Correct the stale cost model; stop the budget alarm crying wolf | cv-project (meta) + cv-infra | done | tech-product-owner | — | [#36](https://github.com/erfeamor/curriculum/pull/36) + [cv-infra#19](https://github.com/erfeamor/cv-infra/pull/19) |
| [T-022](T-022-domain-service-origin-bypasses-cloudfront.md) | Domain service reachable on :8080 bypassing CloudFront; leaks OpenAPI spec | cv-infra | done | infrastructure-engineer | — | [#20](https://github.com/erfeamor/cv-infra/pull/20) |
| [T-023](T-023-meta-docs-stale-bff-smoke-path.md) | The documented E2E smoke command curls a path the BFF no longer serves; `architecture.md:39` legacy Free Tier (**absorbs T-003**) | cv-project (meta) | done | tech-product-owner | — | [#88](https://github.com/erfeamor/curriculum/pull/88) |
| [T-024](T-024-contract-skill-assignment-put-shape.md) | Contract: split the skill-assignment PUT's request body from its response | cv-project (meta) | done | tech-product-owner | — | [#41](https://github.com/erfeamor/curriculum/pull/41) |
| [T-026](T-026-first-build-after-cold-start-fails.md) | First build after a Jenkins restart fails — **FIXED** (JENKINS-23152 build-number collision), verified on the live host | cv-infra | done | infrastructure-engineer | T-019 | [#21](https://github.com/erfeamor/cv-infra/pull/21) |
| [T-028](T-028-qa-env-generator-worktree-build-context.md) | QA stack builds `master`, not the worktree under test (**silent false pass**) | cv-project (meta) | done | infrastructure-engineer | — | [#49](https://github.com/erfeamor/curriculum/pull/49) |
| [T-030](T-030-pr3-build1-success-then-error.md) | A Jenkins build posted `success` then `error` — **DIAGNOSED: a mid-build Jenkins restart, NOT T-026** | cv-infra | done | tech-product-owner | — | none |
| [T-031](T-031-board-frontmatter-validator.md) | **A validator for the task board** (`scripts/board-check.py`) | cv-project (meta) | done | infrastructure-engineer | — | [#59](https://github.com/erfeamor/curriculum/pull/59) |
| [T-152](T-152-mysql-84-parity-cv-database.md) | Dev/CI parity: bump cv-database's stack **and its migration gate** to MySQL 8.4 | cv-database | done | backend-developer | — | [#3](https://github.com/erfeamor/cv-database/pull/3) |
| [T-154](T-154-jenkins-pipeline-timeout.md) | No `timeout {}` on cv-database's pipeline — **absorbed into T-153** | cv-database | done | tech-product-owner | — | none |
| [T-153](T-153-jenkins-deploy-stage-dead-gate-and-rds.md) | cv-database Jenkinsfile hygiene: dead `main` Deploy gate + RDS comment, no timeout, no MySQL health wait, docs never name 8.4 (**absorbs T-154, T-017**) | cv-database | done | tech-product-owner | T-152 ✔ | [#5](https://github.com/erfeamor/cv-database/pull/5) |
| [T-155](T-155-flyway-version-supports-mysql-84.md) | Flyway 10 → 13.7.0 — **decided**; the dev-stack pin (`docker-compose.dev.yml`) moved, and QA covered a Flyway-10 volume and a fresh one | cv-project (meta) | done | tech-product-owner | — | [#91](https://github.com/erfeamor/curriculum/pull/91) |
| [T-156](T-156-flyway-13-cv-database-pins.md) | Flyway 10 → 13.7.0 in cv-database: the Jenkins gate and `migrate.sh` (split from T-155) | cv-database | done | tech-product-owner | T-155 ✔, T-153 ✔ | [#6](https://github.com/erfeamor/cv-database/pull/6) |
| [T-027](T-027-contract-ordering-note-sql-vs-jpql.md) | Contract: the ordering note prescribes SQL syntax for a JPQL context | cv-project (meta) | done | tech-product-owner | — | [curriculum#99](https://github.com/erfeamor/curriculum/pull/99) |
| [T-029](T-029-code-review-cannot-see-worktrees.md) | `/code-review` **silently reviews the wrong thing** without an explicit target | cv-project (meta) | done | tech-product-owner | — | local adapter edit (gitignored) |
| [T-032](T-032-board-check-re-review-after-live-use.md) | Re-review `board-check.py` after live use, plus two blind spots: **link integrity** and **status-gated `pr:`** | cv-project (meta) | done | tech-product-owner | T-031 ✔ | [#102](https://github.com/erfeamor/curriculum/pull/102) |
| [T-036](T-036-qa-env-cors-port-shift.md) | `qa-env-override.py` shifts the BFF port but not its CORS allowlist — a port-shifted frontend preview is CORS-blocked | cv-project (meta) | done | tech-product-owner | — | [#101](https://github.com/erfeamor/curriculum/pull/101) |
| [T-004](T-004-terraform-state-hardening.md) | Harden Terraform state — **part 1 (0600) done; start at part 2**, the remote backend | cv-infra | done | tech-product-owner | — | [cv-infra#22](https://github.com/erfeamor/cv-infra/pull/22) |
| [T-008](T-008-drone-host-backup-and-snapshot.md) | Drone state to SSM + a real CI-host backup, then retire the T-002 snapshot — **trim step 1** (−$0.69/mo) | cv-infra | done | tech-product-owner | T-002 | [cv-infra#23](https://github.com/erfeamor/cv-infra/pull/23) |
| [T-007](T-007-ecs-agent-cleanup.md) | CI host: plain AL2023 AMI, **measured** root — drops the ecs-agent (**widened 2026-09-24; premise corrected 2026-09-25**: needs `-replace` and an explicit root size) | cv-infra | done | tech-product-owner | T-002, **T-008** | [cv-infra#24](https://github.com/erfeamor/cv-infra/pull/24) |
| [T-039](T-039-cv-infra-durable-runbooks-and-checks.md) | cv-infra: task-named T-007/T-008 runbooks and checks → durable, task-neutral ones | cv-infra | done | tech-product-owner | T-007, T-008 | [cv-infra#25](https://github.com/erfeamor/cv-infra/pull/25) |
| [T-033](T-033-ci-host-tls.md) | CI host TLS — **decided (b): Let's Encrypt via Caddy on `ci.erfeamor.com`**, shipped in T-034 phase 2 | cv-infra | done | tech-product-owner | — | [cv-infra#28](https://github.com/erfeamor/cv-infra/pull/28) |
| [T-034](T-034-release-ci-host-idle-eip.md) | Release the CI host's idle EIP — **done**: `ci.erfeamor.com` + DNS on boot, EIP released, Drone wired to the doorbell | cv-infra | done | tech-product-owner | T-007 | [cv-infra#27](https://github.com/erfeamor/cv-infra/pull/27) + [#28](https://github.com/erfeamor/cv-infra/pull/28) |
| [T-041](T-041-ci-dns-sentinel-shutdown-ordering.md) | The shutdown DNS sentinel raced network teardown — **fixed**: the unit orders after `network-online.target`; 6/6 stops proven | cv-infra | done | tech-product-owner | T-034 ✔ | [cv-infra#29](https://github.com/erfeamor/cv-infra/pull/29) |
| [T-042](T-042-doorbell-wakes-on-branch-deletion.md) | The doorbell woke the CI host for events with nothing to build — **fixed**: deleted refs and non-build PR actions are ignored | cv-infra | done | tech-product-owner | T-034 ✔ | [cv-infra#30](https://github.com/erfeamor/cv-infra/pull/30) |
| [T-012](T-012-aws-endgame-decision.md) | **Paid-vs-teardown — DECIDED 2026-09-24: A, go Paid with the stack trimmed**; upgrade by 2026-12-15 | cv-project (meta) | done | tech-product-owner | — | |

</details>

The cost model's 2026-09-23 reading (the T-020 table) moved to [HISTORY.md](HISTORY.md) on 2026-10-01; current figures are in [T-012](T-012-aws-endgame-decision.md)'s closing note and `cv-infra/CLAUDE.md`.

## Public-path deployment gap (cross-repo — blocks T-501)

**`cv-bff-node` has never been deployed to AWS, and neither has `cv-public-vanilla`.** Verified against the live account 2026-08-11/12: no BFF ECR repo, no BFF container in `user_data`, CloudFront `/api/*` goes straight to Java on :8080, and `s3://cv-project-frontend-dev/` holds only `admin/`. The only BFF-named object in the account is an empty log group. The whole **public** path is absent; the admin is live and unaffected because it bypasses the BFF by design (`docs/architecture.md:28`) — which is exactly why the gap stayed invisible.

One task per repo. The **numbered** rows are strictly sequential and their `depends_on` enforces the order; the unnumbered rows hang off the chain and are claimable once their own dependency is met. **This is the board line for all eight; claim here.**

| # | ID | Title | Repo | Status | Owner | Depends on | PR |
|---|----|-------|------|--------|-------|------------|----|
| 1 | [T-013](T-013-contract-bff-public-routing.md) | Contract: BFF public edge path + anonymous reads | cv-project (meta) | done | tech-product-owner | — | [#22](https://github.com/erfeamor/curriculum/pull/22) |
| 2 | [T-202](T-202-bff-public-routing-and-auth.md) | BFF: public edge path + anonymous read routes | cv-bff-node | done | fullstack-developer | T-013 | [#4](https://github.com/erfeamor/cv-bff-node/pull/4) |
| 3 | [T-014](T-014-deploy-bff-to-aws.md) | **Deploy cv-bff-node to AWS — registry, container, edge route** — done; the public 200 moved to T-043 | cv-infra | done | tech-product-owner | T-013, T-202, **T-201**, **T-156** | [cv-infra#32](https://github.com/erfeamor/cv-infra/pull/32) |
| 3a | [T-211](T-211-bff-service-token-provider.md) | BFF: call the domain service with a Cognito service token (split from T-043) | cv-bff-node | in_progress | tech-product-owner | — | |
| 3b | [T-043](T-043-bff-service-token-to-domain.md) | **The BFF can't read the domain service — give it a Cognito service token** (public routes 401/502 live) | cv-infra | todo | | T-014 ✔, T-211 | |
| 4 | [T-403](T-403-public-vanilla-deploy.md) | Public site (vanilla): deploy + point at the deployed BFF | cv-public-vanilla | todo | | T-014 ✔, **T-408** ✔, **T-043** | |
| 5 | [T-015](T-015-docs-reflect-deployed-bff.md) | Correct the meta docs that claim the BFF is deployed — **absorbed into T-501** (2026-10-01) | cv-project (meta) | done | tech-product-owner | T-014, T-403, T-404 | none |
| — | [T-203](T-203-bff-ci-deploy-stage.md) | BFF CI: push to ECR and roll the container on master | cv-bff-node | todo | | T-014 | |
| — | [T-204](T-204-bff-validate-person-id-param.md) | BFF: validate the person id before the upstream call (adopts T-201's shared guard) | cv-bff-node | done | fullstack-developer | T-202 ✔, **T-201 ✔** | [#8](https://github.com/erfeamor/cv-bff-node/pull/8) |
| — | [T-404](T-404-public-react-point-at-deployed-bff.md) | Public site (React): point Vercel's `BFF_URL` at the deployed BFF | cv-public-react | todo | | T-014 ✔, **T-043** | |

**[T-014](T-014-deploy-bff-to-aws.md) is claimable and heads the chain** — its `depends_on` (T-013, T-202, T-201) is fully satisfied. T-201 is there as a *sequencing* decision: the first deployed image must already serve the aggregate. When a dependency changes, the task file and every prose reference to it move together — the paragraph this replaces went stale about T-201 four times (see HISTORY.md).

Two things T-014 inherited from this chain's reviews, both of which fail quietly:
- `spa_router` rewrites extensionless URIs to `/index.html`, so `/metrics` and `/health` answer **200 with the SPA shell**, not 404. T-014 carries an acceptance criterion to exclude them, and to verify by request rather than by reading the Terraform.
- The BFF now serves `/bff/api/v1`, so CloudFront must forward the prefix **unstripped**. A behavior that strips it produces a deploy that 404s with nothing obviously wrong in the config.

> **T-202 merged without stage-4 QA.** Its auth matrix is proven by unit tests against `createApp()`, not against a live stack — no request has traversed a real CloudFront → BFF → domain-service path. T-014's own stage-4 verification is the first time that happens, so treat its live checks as covering both tasks.

Personas and risk for the open rows (assigned per the adapter's capability→repo map; each task file carries the reviewer set and gate commands):

| ID | Developer | Risk | `security_review` |
|---|---|---|---|
| T-014 | infrastructure-engineer | **high** | **true** — SG ingress, published ports, CORS |
| T-403 | fullstack-developer | normal | **true** — `.github/workflows/**` + AWS deploy creds |
| T-203 | infrastructure-engineer | normal | **true** — CI config + AWS creds; read T-005 first |
| T-404 | fullstack-developer | normal | false — a base URL for a public anonymous read; no credentials |

- **T-014 is the expensive one** (adapter §7: real apply + stage-4 AWS verification = budget for the full ceiling, never run it in a wave). It replaces the instance via `user_data_replace_on_change`; since [T-018](T-018-mysql-on-dedicated-ebs-volume.md) the MySQL datadir survives on its own volume, so confirm `/var/lib/cv-mysql` is mounted from it (`findmnt`) before applying.
- **A trap arrived with T-018**, filed as **[T-021](T-021-mysql-password-rotation-persistent-datadir.md)**: because the datadir now survives, `mysql:8.4` skips initialization and keeps its original credentials, so rotating `var.db_password` makes Flyway fail auth, aborts the bootstrap under `set -e`, and leaves the box with **no domain-service container at all**. Anyone editing `db_password` before T-021 lands should expect that.
- **T-203 is off the critical path** — T-501 needs the BFF *deployed*, not *auto-deployed*, and T-201 in T-014's `depends_on` means the first manual deploy already serves the aggregate.
- **Deadline context (2026-10-01):** none binding. Paid plan, $120.75 of credits (~mid-March 2027 at the measured rate, expiring 2027-07-12); T-012 closed as A (keep the stack, no teardown), so nothing here has to race a rebuild.


---

For historical context and board consistency sweeps, see [HISTORY.md](HISTORY.md).
