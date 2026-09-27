---
id: T-114
title: "The test profile runs with `open-in-view` ON while production runs it OFF, so every other test exercises a persistence mode production never uses"
repo: cv-domain-service
status: done
owner: tech-product-owner
branch: fix/test-profile-open-in-view
pr: https://github.com/erfeamor/cv-domain-service/pull/12
depends_on: []
risk: normal
security_review: false
checkpoint:
  stage: done   # merged cf508e4 (squash of cv-domain-service#12), 2026-09-27 — H2 accepted by the human; Jenkins PR-12 build 1 green on cf733dd (2026-09-27). Stage 4: no live-stack surface (test config only); QA re-ran the full suite independently (148/148, 0 open-in-view warnings) and confirmed the single @SpringBootTest — recorded as the QA pass
  repo: cv-domain-service
  branch: fix/test-profile-open-in-view
  worktree: none   # removed after merge
  commit: cf508e4   # squash merge on master (branch head was cf733dd)
  pr: https://github.com/erfeamor/cv-domain-service/pull/12
  developer: backend-developer
  reviewers: [code-review, quality-assurance]
  risk: normal
  security_review: false
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: none   # test-config change; no live stack
  updated: 2026-09-27T10:00:00+02:00
  budget:
    turns: 319   # --since 2026-09-25T12:49:25.700Z
    total_tokens: 58797319
    subagent_tokens: 0
    spawns: 1   # quality-assurance (shared); backend-developer is T-108's instance, reused
    status: ok
    checked: 2026-09-27T10:00:00+02:00
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

- [x] The test profile runs with open-in-view off, and the startup warning is gone from test logs.
- [x] Every test whose outcome changed is listed on this task, with a fix or a reason.
- [x] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Provenance

Filed by the driver on 2026-09-26, from T-108's round-1 `/code-review` finding. The human approved filing it at T-108's H2.

## Test plan — quality-assurance, 2026-09-27 (stage 0)

- [x] **Baseline:** `mvn -B test` on master; record the per-test results and confirm the open-in-view warning appears in the startup log.
- [x] Set `spring.jpa.open-in-view: false` in `src/test/resources/application.yml` and re-run. Diff the results by test name: any flip, or any changed status code or assertion, is a finding.
- [x] For each flipped test, classify it and investigate it rather than silence it:
  - lazy associations serialized outside a session in `@WebMvcTest`/`@SpringBootTest`
  - tests relying on one `EntityManager` per request
- [x] The warning is gone after the change.
- [x] `ConcurrentDeleteDuringUpdateTest`'s pin is either removed or kept with a "belt and braces" comment. The PR contains one of the two.
- [x] Every changed test is listed on this task with a fix or a reason.
- [x] `src/main/resources/application.yml` is untouched.
- **Gates:** `mvn -B test`, `mvn -B checkstyle:check`.

## H1 decisions — human, 2026-09-27

Approved as written. Developer: `backend-developer`, **T-108's instance, reused**: it wrote the pin this task generalizes. Reviewers: `/code-review` + QA coverage.

## Outcome — 2026-09-27

**No test changed outcome**: all 148 passed before and after, and the per-test diff is empty. The reason is that `ConcurrentDeleteDuringUpdateTest` is the only `@SpringBootTest` and already pinned the setting. Every other test is a `@WebMvcTest` (mocked repositories) or a `@DataJpaTest` (no web layer), so open-in-view cannot affect it. The change protects every **future** full-context test. The pin is kept, commented as belt and braces.
