---
id: T-115
title: "The domain service accepts a section whose `endDate` is earlier than its `startDate`"
repo: cv-domain-service
status: todo
owner:
branch: fix/section-period-validation
pr:
depends_on: []
risk: normal
security_review: false
---

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
