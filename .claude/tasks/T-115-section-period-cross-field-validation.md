---
id: T-115
title: "The domain service accepts a section whose `endDate` is earlier than its `startDate`"
repo: cv-domain-service
status: done
owner: tech-product-owner
branch: fix/section-period-validation
pr: https://github.com/erfeamor/cv-domain-service/pull/13
depends_on: [T-027]   # contract line lands in T-027's PR (board rule 4)
risk: normal
security_review: false
checkpoint:
  stage: done   # merged c1213e8 (squash of cv-domain-service#13), 2026-09-27 — H2 accepted by the human after #99; branch already on master cf508e4, Jenkins PR-13 #1 green
  repo: cv-domain-service
  branch: fix/section-period-validation
  worktree: none   # removed after merge
  commit: c1213e8
  pr: https://github.com/erfeamor/cv-domain-service/pull/13
  developer: backend-developer
  reviewers: [code-review, quality-assurance]
  risk: normal
  security_review: false
  review_round: 1   # /code-review: 1 finding (vacuous body test) fixed in dbd0e06; QA coverage: no blocking gaps
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 0
  updated: 2026-09-27T11:40:00+02:00
  budget:
    turns: 55   # budget baseline reset by the human: --since 2026-09-27T09:19:56.000Z
    total_tokens: 6385214
    subagent_tokens: 0
    spawns: 2   # quality-assurance (shared plan) + developer
    status: ok
    checked: 2026-09-27T11:40:00+02:00
---

## H1 — accepted by the human, 2026-09-27

- **Contract first:** rule 4 in `docs/api-contract.md` gains the cross-field line, in the same meta PR as [T-027](T-027-contract-ordering-note-sql-vs-jpql.md). T-115 may implement in parallel but **merges only after that PR**.
- **Rule:** checked **only when both dates are non-null** (`endDate ≥ startDate`, equal allowed). One-sided project dates keep today's behavior.
- **Shape:** no class-level constraint exists in the repo yet; one reusable constraint over the three entities is preferred to three ad hoc checks.
- **Test plan:** QA's 10 cases (POST+PUT inverted → 400 for all three, fail-first; equal, null `endDate`, no-date project accepted; validator unit test; malformed date unaffected).

## The gap

`Experience`, `Education` and `Project` bind `startDate`/`endDate` as `LocalDate` with no cross-field check. A POST or PUT with `startDate: 2023-05-01, endDate: 2021-01-01` returns 201/200, and both public sites then render an inverted period.

[T-301](T-301-admin-cv-sections-crud.md) adds a **client-side** check in cv-admin-react (round 1, 2026-09-27). But the domain service is the source of truth, and any other client (curl, a future importer) bypasses the UI.

## Scope

- A class-level Bean Validation constraint (or equivalent) on the three entities: `endDate`, when non-null, must be ≥ `startDate`, when non-null. `null` `endDate` means "current" (rule 3). A project may have neither date.
- A 400 in the contract's existing validation-error shape. **Check `docs/api-contract.md` first**: if the cross-field rule is not stated there, it needs a contract line, and board rule 4 puts that change in a contract PR first.

## Acceptance criteria

- [ ] An inverted period gets a 400 on POST and PUT for all three sections, and the tests fail on master first.
- [ ] Equal dates, a null `endDate`, and a project with no dates are all still accepted.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Provenance

Filed by the driver, 2026-09-27, from T-301's round-1 `/code-review` finding, where it was accepted client-side only.
