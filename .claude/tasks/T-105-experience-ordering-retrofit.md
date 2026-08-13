---
id: T-105
title: Retrofit contract ordering onto the merged Experience resource
repo: cv-domain-service
status: todo
owner:
branch: fix/experience-ordering
pr:
depends_on: [T-006]
risk: normal
security_review: false
---

## Why this exists

T-006 added § Ordering to `docs/api-contract.md`. T-102, T-103 and T-104 absorb it into their acceptance criteria before they are implemented. **T-101 cannot** — it merged as [cv-domain-service#3](https://github.com/erfeamor/cv-domain-service/pull/3) on 2026-08-09, so Experience is the one section resource already in `master` without an ordering guarantee.

`ExperienceRepository.findByPersonId` is a derived Spring Data query with no `ORDER BY`:

```java
List<Experience> findByPersonId(Long personId);
```

It returns rows in whatever order MySQL produces. That is exactly the defect T-006 exists to prevent, and it is live on `master` today.

**This task is the recorded answer to T-006's acceptance criterion "a decision on how T-101 picks it up."** T-006's own rollout section offered two options — amend T-101's PR, or file a follow-up. The amend option was written while T-101 was still `in_review` and **died when it merged**; a merged PR cannot absorb the change. Ratified at T-006's H1 on 2026-08-13: follow-up task, this one.

## Scope

`cv-domain-service` only. One repository method, plus the tests that prove it.

- Order `findByPersonId` by `startDate` **DESC**, tiebroken by `id` **ASC**, per the contract's § Ordering table.
- Prefer the derived-query form (`findByPersonIdOrderByStartDateDescIdAsc`) over an `@Query`; it is the idiom already used in this package and it cannot drift from the entity's column mapping.
- `startDate` is `NOT NULL` on `experience` (unlike `project.start_date`), so **the NULL-placement rule does not apply here.** Do not add `IS NULL` handling — it would be dead code that implies a nullability the schema does not have.

## Acceptance criteria

- [ ] `GET /api/v1/people/{personId}/experiences` returns `startDate` DESC, then `id` ASC.
- [ ] A `@DataJpaTest` seeds rows **inserted in a deliberately wrong order** and asserts the returned sequence. Inserting in the expected order would pass against an unordered query and prove nothing.
- [ ] A separate assertion covers the tiebreaker: two rows sharing a `startDate`, asserted to come back in `id` ASC order.
- [ ] No change to the controller, service, payload shape, or any other endpoint — the response body is byte-identical apart from element order.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Definition of done

PR open against `master` from `fix/experience-ordering`, Jenkins green, merged, task set `done`.

## dev-loop notes

- **Developer:** `backend-developer` (adapter §2 — `cv-domain-service`). **Reviewers:** `/code-review` + `backend-developer` specialist lens. `risk: normal`; small diff, but it changes the observable behavior of an endpoint already consumed.
- `security_review: false` — no auth, secrets, IAM, or CI surface.
- **Sequencing:** independent of T-102/T-103/T-104 (disjoint packages), so it can run in the same wave. It does **not** block T-201 — but leaving it undone means the aggregate serves one unordered section out of four, which T-501 would find at the worst possible moment.
