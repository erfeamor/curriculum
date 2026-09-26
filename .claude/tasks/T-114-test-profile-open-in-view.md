---
id: T-114
title: "The test profile runs with `open-in-view` ON while production runs it OFF, so every other test exercises a persistence mode production never uses"
repo: cv-domain-service
status: todo
owner:
branch: fix/test-profile-open-in-view
pr:
depends_on: []
risk: normal
security_review: false
---

## The gap

`src/main/resources/application.yml` sets `spring.jpa.open-in-view: false`. `src/test/resources/application.yml` **replaces** that file on the test classpath and does not set the property, so every test runs with Boot's default, `true` (Spring logs the open-in-view warning at startup).

**This already hid a real defect once.** In [T-108](T-108-untransacted-update-read-modify-write.md), the race test first ran under the test profile. There the old code answered `500` rather than re-inserting the deleted row under a new id. The developer concluded the spec's premise was wrong, and only `/code-review` (round 1) caught that the test was running in a mode production does not use. T-108 fixed it **locally**, by pinning `spring.jpa.open-in-view=false` in that one test's `@TestPropertySource`, and deliberately did not widen its PR.

Any other test that depends on lazy loading or on entity-manager scope can be passing only because open-in-view keeps one `EntityManager` per request.

## Scope

- Set `spring.jpa.open-in-view: false` in the test `application.yml`, matching production.
- Run the full suite and fix or explain every test that changes behaviour. Each such change is a finding: production behaves the way the test now does.
- Remove the now-redundant pin from `ConcurrentDeleteDuringUpdateTest`'s `@TestPropertySource`, or keep it with a comment saying it is belt and braces.

## Acceptance criteria

- [ ] The test profile runs with open-in-view off, and the startup warning is gone from test logs.
- [ ] Every test whose outcome changed is listed on this task, with a fix or a reason.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Provenance

Filed by the driver on 2026-09-26, from T-108's round-1 `/code-review` finding. The human approved filing it at T-108's H2.
