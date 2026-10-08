# Board

Protocol: [README.md](README.md) · Contract: [docs/api-contract.md](../../docs/api-contract.md) · History: [HISTORY.md](HISTORY.md)

One line per task; the task file holds the detail. Merge narratives and superseded reasoning live in HISTORY.md — when a note below stops being current, move it there rather than striking it in place. Done rows are folded under each table.

## Now / Next / Later — refreshed 2026-10-08 (T-502 merged: the roadmap is complete; next T-504, the M2 tag)

The order to claim in. It is **advice, refreshed at every board-sync**. `depends_on` is authoritative wherever the two disagree, and a lane entry that has gone stale is a board-sync finding, not a rule.

**Sizing:** plan by **plan windows and the human's `/usage` figure**, not by the budget probe — it doesn't count subagent spend, which dominates infra work (sessions 1–5, 2026-09-28 → 10-01, measured it; close-outs in [HISTORY.md](HISTORY.md)). High-risk infra has run about 2× its estimates. Host-up work follows `cv-infra/docs/runbooks/` (`drone.md`, `ci-host-replace.md`); pause the reaper with the **`CIKeepAlive` tag**, never by disabling the rule.

**Now**
- **[T-040](T-040-jenkins-github-pat-expiry.md)** as soon as the human has the token (**due 2026-10-30**).

**Next**
- **[T-051](T-051-cost-remeasure-after-trims.md)** cost re-measure **done 2026-10-08** (~$0.51/day), with [T-053](T-053-cv-infra-cost-table-refresh.md) (cv-infra's table), then [T-053](T-053-cv-infra-cost-table-refresh.md) (cv-infra's table).

**Then**
- **[T-504](T-504-m2-release-tag-all-repos.md)**: tag `M2` in all 9 repos, pinned by a manifest, with immutable tags. **Claimable: T-502 is done.**

**Anytime**
- [T-056](T-056-cv-infra-readme-free-tier-drift.md) and [T-057](T-057-cv-observability-docs-reflect-decision.md): trivial README fixes from T-502's audit.
- [T-038](T-038-board-check-link-check-live-use-re-review.md) (check 8's live-use re-review), from **2026-10-12**. Small.

**Human**
- **By 2026-10-30:** create a replacement CI GitHub token for Jenkins ([T-040](T-040-jenkins-github-pat-expiry.md)). The current one expires **2026-11-06**.
- Paid plan since 2026-09-29; all five credit activities done (grant $200). **$116.15** left on 2026-10-08 at **~$0.51/day** (T-051), enough until about late May 2027, before the credits expire on 2027-07-12. Charges past them bill the card; the budget alarms are the guard.

Recent close-outs: 2026-10-08 **T-502** (final docs + Mermaid diagram; the roadmap is complete); 2026-10-08 **T-055** (`cv-redeploy` resolves every input before removing the running container; app host now `i-05c8e011117d30b34`); 2026-10-08 **T-054** (app logs in CloudWatch; app host now `i-0ec8607bffc070d6a`); 2026-10-07 T-052 (decided: app logs to CloudWatch via T-054, metrics local by design); T-050 (ECR keeps latest + 4 shas per repo); **T-501: milestone M2** (absorbs T-015); **T-049 + T-158** (production migrations run from cv-database's master after Jenkins is green; schema-first ordering rule in both repos); 2026-10-06 T-503 (the human's CV is live), T-005, T-048, T-047/T-112/T-203 (automated deploys); 2026-10-05 T-035, T-025, T-116, T-044, T-303. Narratives are in each task file and [HISTORY.md](HISTORY.md).

**Later / conditional**
- [T-021](T-021-mysql-password-rotation-persistent-datadir.md): T-004 decided **not** to rotate `db_password`, so this has no trigger today. Claim it **before** anyone changes `db_password` for any reason.

## M2 — Complete the domain model end-to-end


Tasks in [T-501](T-501-e2e-cv-milestone.md)'s transitive `depends_on` — **computed from the frontmatter** (2026-09-24, re-checked 2026-10-06) — plus [T-502](T-502-final-docs-architecture-diagram.md), the roadmap close-out that follows it. The deployment chain's rows are folded in its own section below. Everything else in the product repos is in *Defects, hygiene & hardening*.

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-504](T-504-m2-release-tag-all-repos.md) | Tag `M2` in all 9 repos, pinned by a meta-repo manifest, with checkout/verify scripts and immutable tags | cv-project (meta) + all repos | todo | | T-502 | |

<details>
<summary>M2 — 18 done</summary>

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-502](T-502-final-docs-architecture-diagram.md) | Final documentation and architecture diagram (the roadmap's last item) | cv-project (meta) | done | tech-product-owner | T-501 ✔, T-052 ✔, T-054 ✔ | [#122](https://github.com/erfeamor/curriculum/pull/122) |
| [T-501](T-501-e2e-cv-milestone.md) | End-to-end verification + roadmap close-out | cv-project | done | tech-product-owner | T-101…T-105, T-151, T-201, T-301, T-401, T-402, T-014, T-043, T-403, T-404, T-503 (T-408, T-409 via T-401, T-402) | [#116](https://github.com/erfeamor/curriculum/pull/116) |
| [T-503](T-503-production-cv-content.md) | Production CV content: replace T-018's probe rows with a real CV (human, via `/admin/`) | cv-project (meta) | done | tech-product-owner | — | none |
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

- **The domain waves, the rendering tasks and the deployment chain are all done.** [T-503](T-503-production-cv-content.md) (real production content) is done too, so **[T-501](T-501-e2e-cv-milestone.md) is claimable**.
- **Read contract design rule 7's carve-outs before writing a consumer.** Requests are the opposite (`PUT` replaces, so an omitted optional in a *request* body IS the empty case), and `endDate` is not governed by rule 7 at all — always emitted, its `null` means "current" under rule 3.
- **Probe a guard, don't read it.** The T-205 → T-210 lineage caught several type-level guards passing for the wrong reason, each found only by making the defect and watching the check stay green. Narratives in HISTORY.md.
- **Concurrency lesson from T-103:** highest-risk tasks (composite key, upsert, 409) should start first so review convergence failures surface earliest.

### Repo context

- **cv-bff-node is now TypeScript** (strict, ts-jest/tsc). T-201's route and tests are `.ts`, type the aggregate payload, and `npm run typecheck` is a gate.
- **cv-admin-react is hexagonal TypeScript** (domain ← application ← composition → infrastructure). T-301 follows the repo CLAUDE.md's "adding a section resource" recipe.
- **cv-public-react** exists as a second public site (Next.js/ISR from the BFF). It renders all four CV sections (T-402) and points at the deployed BFF (T-404); both are done.
- **The database is self-hosted MySQL 8.4**, not RDS. Migrations verified compatible; production applies migrations only — dev-seeds stay dev-only. Backups (T-001) and dev/prod version parity (T-016, T-152) are done.

## Defects, hygiene & hardening — product repos (not on T-501's path)

Real defects, security fixes and CI debt in the product repos that **T-501 does not wait on** (no path to them through its `depends_on`). Until 2026-09-24 they sat in the M2 table, which made the milestone look larger than it is.

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|

<details>
<summary>Defects, hygiene & hardening — 20 done</summary>

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-158](T-158-cv-database-ci-migrate-on-master.md) | CI: apply new migrations to production on `master` (GitHub Actions after Jenkins is green → SSM `cv-redeploy-migrate`) | cv-database | done | tech-product-owner | T-049 | [cv-database#8](https://github.com/erfeamor/cv-database/pull/8) |
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
| [T-113](T-113-optimistic-locking-lost-update.md) | Lost updates on concurrent PUTs — **fixed (`@Version`, 409); deployed 2026-10-05** via T-044's `cv-redeploy` | cv-domain-service | done | tech-product-owner | T-108 ✔, T-014 ✔, T-046, T-157 | [cv-domain-service#15](https://github.com/erfeamor/cv-domain-service/pull/15) |
| [T-303](T-303-admin-send-version-handle-409.md) | Admin: keep each row's `version`, send it on PUT, handle a 409 (split from T-113) | cv-admin-react | done | tech-product-owner | T-046 ✔ (T-113 ✔) | [cv-admin-react#17](https://github.com/erfeamor/cv-admin-react/pull/17) |
| [T-116](T-116-domain-service-scope-enforcement.md) | The domain service accepts any pool token for any method — make the BFF's read-only service token GET-only (T-043 follow-up) | cv-domain-service | done | tech-product-owner | T-043 ✔ | [cv-domain-service#16](https://github.com/erfeamor/cv-domain-service/pull/16) |
| [T-112](T-112-domain-service-ci-ecr-deploy.md) | CI: push the image to ECR and roll the container on `master` (deploy is manual today). Needs a cv-infra apply: after T-014, one credential decision with T-203 | cv-domain-service | done | tech-product-owner | T-111 ✔, T-044 ✔, T-047 | [cv-domain-service#17](https://github.com/erfeamor/cv-domain-service/pull/17) |

</details>

## Infra & ops (outside M2)

[T-012](T-012-aws-endgame-decision.md) decided **A (go Paid, trimmed)** on 2026-09-24 and closed 2026-10-01 (Paid since 09-29, all credit activities done, $120.75 left), so the hardening and cost trims below are all worth doing. **cv-infra applies are strictly serial** — one root module, one state (in S3 with a DynamoDB lock since T-004, so a concurrent apply blocks rather than corrupts).

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-021](T-021-mysql-password-rotation-persistent-datadir.md) | Rotating `db_password` breaks silently now the datadir persists | cv-infra | todo | | T-018 | |
| [T-038](T-038-board-check-link-check-live-use-re-review.md) | Re-review board-check's check 8 (link integrity) after two weeks of real edits — not before 2026-10-12 | cv-project (meta) | todo | | T-032 | |
| [T-040](T-040-jenkins-github-pat-expiry.md) | The CI GitHub token Jenkins uses expires 2026-11-06 — rotate it (**due 2026-10-30**) | cv-infra | todo | | — | |
| [T-056](T-056-cv-infra-readme-free-tier-drift.md) | cv-infra README still says 'kept within the AWS Free Tier' (from T-502's audit) | cv-infra | todo | | — | |
| [T-057](T-057-cv-observability-docs-reflect-decision.md) | cv-observability docs predate T-052/T-054 (logging 'not wired up yet'; pipeline) (from T-502's audit) | cv-observability | todo | | — | |

<details>
<summary>Infra & ops — 53 done</summary>

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-053](T-053-cv-infra-cost-table-refresh.md) | cv-infra CLAUDE.md cost table from T-051's measurement | cv-infra | done | tech-product-owner | T-051 | [cv-infra#44](https://github.com/erfeamor/cv-infra/pull/44) |
| [T-051](T-051-cost-remeasure-after-trims.md) | Re-measure the run rate after the EIP release + Graviton — started early (H1 2026-10-08) | cv-project (meta) | done | tech-product-owner | — | [#120](https://github.com/erfeamor/curriculum/pull/120) |
| [T-055](T-055-cv-redeploy-resolve-inputs-before-rm.md) | `cv-redeploy` removes the running container before reading its SSM parameters; a failed read leaves the service down (from T-054's review) | cv-infra | done | tech-product-owner | T-054 ✔ | [cv-infra#43](https://github.com/erfeamor/cv-infra/pull/43) |
| [T-054](T-054-app-container-logs-to-cloudwatch.md) | Ship the app containers' logs to the existing CloudWatch groups (awslogs driver); decided at T-052 | cv-infra | done | tech-product-owner | T-052 ✔ | [cv-infra#42](https://github.com/erfeamor/cv-infra/pull/42) |
| [T-052](T-052-observability-scope-decision.md) | Decide the observability scope (metrics are local-only; the logs pipeline is still "pending") | cv-project (meta) | done | tech-product-owner | — | none |
| [T-050](T-050-ecr-sha-tag-retention.md) | ECR keeps every `:<sha>` deploy image forever — add a retention rule | cv-infra | done | tech-product-owner | T-112 ✔, T-203 ✔ | [cv-infra#41](https://github.com/erfeamor/cv-infra/pull/41) |
| [T-049](T-049-ci-migrate-role-and-ssm-document.md) | SSM document `cv-redeploy-migrate` + a master-only OIDC role for cv-database (for T-158) | cv-infra | done | tech-product-owner | T-047 ✔ | [cv-infra#40](https://github.com/erfeamor/cv-infra/pull/40) |
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
| [T-044](T-044-app-host-bootstrap-s3-and-redeploy.md) | App host: bootstrap to S3 (user_data ~14.6/15.5 KB) + a `cv-redeploy <service>` command and a deploy runbook — today a new image only lands by replacing the host | cv-infra | done | tech-product-owner | T-043 ✔ | [cv-infra#35](https://github.com/erfeamor/cv-infra/pull/35) |
| [T-045](T-045-github-oidc-deploy-role-public-vanilla.md) | GitHub Actions OIDC provider + a deploy role for cv-public-vanilla (bucket root, explicit deny on `admin/*`); split from T-403 | cv-infra | done | tech-product-owner | — | [cv-infra#34](https://github.com/erfeamor/cv-infra/pull/34) |
| [T-025](T-025-verify-requests-come-from-our-cloudfront.md) | The edge is not an authenticator — **closed 2026-10-05 as documented accepted risk** (only the BFF's `/metrics` counters are exposed; re-open triggers on the task) | cv-infra + cv-domain-service | done | tech-product-owner | T-022, T-043 ✔ | none |
| [T-035](T-035-app-host-to-graviton.md) | App host to Graviton (arm64 images first) **+ its IMDSv2 hardening (from T-005)** — −$1.75/mo, **after** T-014; size follows T-014's memory numbers | cv-infra | done | tech-product-owner | T-014 | [cv-infra#36](https://github.com/erfeamor/cv-infra/pull/36) |
| [T-005](T-005-ci-secret-blast-radius.md) | CI secret blast radius — the remainder: the docker.sock/host-network IMDS gap, split parameter paths, narrow the app-host SSM read (CI-host IMDSv2 done in T-007; app host's moved to T-035) | cv-infra | done | tech-product-owner | T-002, T-007 | [cv-infra#39](https://github.com/erfeamor/cv-infra/pull/39) |
| [T-046](T-046-contract-section-version-409.md) | Contract: optional `version` on person + sections, 409 on a stale PUT (split from T-113) | cv-project (meta) | done | tech-product-owner | — | [#107](https://github.com/erfeamor/curriculum/pull/107) |
| [T-157](T-157-migration-version-columns.md) | cv-database V2: additive `version` columns on person + sections (split from T-113); reaches production via T-044's `cv-redeploy migrate` | cv-database | done | tech-product-owner | T-046 ✔ | [cv-database#7](https://github.com/erfeamor/cv-database/pull/7) |
| [T-047](T-047-ci-deploy-roles-and-ssm-documents.md) | GitHub OIDC deploy roles for the domain service and BFF + one SSM document per service (`cv-redeploy <svc>` only); for T-112/T-203 | cv-infra | done | tech-product-owner | T-044 ✔, T-045 ✔ | [cv-infra#37](https://github.com/erfeamor/cv-infra/pull/37) |
| [T-048](T-048-jenkins-misses-push-when-ci-host-up.md) | **A push to a Jenkins repo while the CI host is up never reaches Jenkins** (the doorbell no-ops; Jenkins only scans on boot); found live at T-112's merge | cv-infra | done | tech-product-owner | — | [cv-infra#38](https://github.com/erfeamor/cv-infra/pull/38) |

</details>

The cost model's 2026-09-23 reading (the T-020 table) moved to [HISTORY.md](HISTORY.md) on 2026-10-01; current figures are in [T-012](T-012-aws-endgame-decision.md)'s closing note and `cv-infra/CLAUDE.md`.

## Public-path deployment chain (cross-repo) — done 2026-10-06

The public path is live: CloudFront `/bff/*` → BFF → domain service → MySQL, the vanilla site at the distribution root, cv-public-react on Vercel, and both services deploy themselves on a master push. The section's prose, its personas table and its sequencing notes are in [HISTORY.md](HISTORY.md) (2026-10-06).

<details>
<summary>Public-path deployment chain — 10 done</summary>

| # | ID | Title | Repo | Status | Owner | Depends on | PR |
|---|----|-------|------|--------|-------|------------|----|
| 1 | [T-013](T-013-contract-bff-public-routing.md) | Contract: BFF public edge path + anonymous reads | cv-project (meta) | done | tech-product-owner | — | [#22](https://github.com/erfeamor/curriculum/pull/22) |
| 2 | [T-202](T-202-bff-public-routing-and-auth.md) | BFF: public edge path + anonymous read routes | cv-bff-node | done | fullstack-developer | T-013 | [#4](https://github.com/erfeamor/cv-bff-node/pull/4) |
| 3 | [T-014](T-014-deploy-bff-to-aws.md) | **Deploy cv-bff-node to AWS — registry, container, edge route** — done; the public 200 moved to T-043 | cv-infra | done | tech-product-owner | T-013, T-202, **T-201**, **T-156** | [cv-infra#32](https://github.com/erfeamor/cv-infra/pull/32) |
| 3a | [T-211](T-211-bff-service-token-provider.md) | BFF: call the domain service with a Cognito service token (split from T-043) | cv-bff-node | done | tech-product-owner | — | [cv-bff-node#12](https://github.com/erfeamor/cv-bff-node/pull/12) |
| 3b | [T-043](T-043-bff-service-token-to-domain.md) | **The BFF reads the domain service with a Cognito service token** — the public CV is 200 live | cv-infra | done | tech-product-owner | T-014 ✔, T-211 ✔ | [cv-infra#33](https://github.com/erfeamor/cv-infra/pull/33) |
| 4 | [T-403](T-403-public-vanilla-deploy.md) | Public site (vanilla): deploy + point at the deployed BFF — H1 2026-10-04: OIDC (T-045 first), same-origin calls, root deploy excluding `admin/*` | cv-public-vanilla | done | tech-product-owner | T-014 ✔, **T-408** ✔, **T-043** ✔, **T-045** ✔ | [cv-public-vanilla#5](https://github.com/erfeamor/cv-public-vanilla/pull/5) |
| 5 | [T-015](T-015-docs-reflect-deployed-bff.md) | Correct the meta docs that claim the BFF is deployed — **absorbed into T-501** (2026-10-01) | cv-project (meta) | done | tech-product-owner | T-014, T-403, T-404 | none |
| — | [T-203](T-203-bff-ci-deploy-stage.md) | BFF CI: push to ECR and roll the container on master | cv-bff-node | done | tech-product-owner | T-014 ✔, T-044 ✔, T-047 | [cv-bff-node#13](https://github.com/erfeamor/cv-bff-node/pull/13) |
| — | [T-204](T-204-bff-validate-person-id-param.md) | BFF: validate the person id before the upstream call (adopts T-201's shared guard) | cv-bff-node | done | fullstack-developer | T-202 ✔, **T-201 ✔** | [#8](https://github.com/erfeamor/cv-bff-node/pull/8) |
| — | [T-404](T-404-public-react-point-at-deployed-bff.md) | Public site (React): point Vercel's `BFF_URL` at the deployed BFF — **done 2026-10-04**: live, and a production build fails without it | cv-public-react | done | tech-product-owner | T-014 ✔, **T-043** ✔ | [cv-public-react#9](https://github.com/erfeamor/cv-public-react/pull/9) |

</details>

---

For historical context and board consistency sweeps, see [HISTORY.md](HISTORY.md).